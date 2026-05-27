import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.tenants.models import Tenant, FacilityMapping
from apps.users.models import User
from apps.ingestion.models import Batch
from apps.ingestion.tasks import ingest_and_normalize
from django.conf import settings

class Command(BaseCommand):
    help = 'Seeds the database with a tenant, users, facility mappings, and runs ingestion pipelines on sample files'

    def add_arguments(self, parser):
        parser.add_argument('--tenant-slug', type=str, default='demo', help='Slug of the tenant to create/use')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']
        
        self.stdout.write(self.style.NOTICE(f"Seeding tenant '{tenant_slug}'..."))

        # 1. Create Tenant
        tenant, tenant_created = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={'name': 'Demo Corp'}
        )
        if tenant_created:
            self.stdout.write(self.style.SUCCESS(f"Tenant '{tenant.name}' created."))
        else:
            self.stdout.write(self.style.WARNING(f"Tenant '{tenant.name}' already exists."))

        # 2. Create Analyst User
        analyst_email = 'analyst@demo.com'
        analyst, created = User.objects.get_or_create(
            email=analyst_email,
            defaults={
                'tenant': tenant,
                'full_name': 'Jane Analyst',
                'role': User.ANALYST,
                'is_staff': False
            }
        )
        if created:
            analyst.set_password('demo1234')
            analyst.save()
            self.stdout.write(self.style.SUCCESS(f"Analyst user '{analyst_email}' created."))
        else:
            self.stdout.write(self.style.WARNING(f"Analyst user '{analyst_email}' already exists."))

        # 3. Create Tenant Admin User
        admin_email = 'admin@demo.com'
        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'tenant': tenant,
                'full_name': 'Bob Admin',
                'role': User.TENANT_ADMIN,
                'is_staff': True
            }
        )
        if created:
            admin.set_password('demo1234')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Tenant Admin user '{admin_email}' created."))
        else:
            self.stdout.write(self.style.WARNING(f"Tenant Admin user '{admin_email}' already exists."))

        # 4. Create Facility Mappings
        self.stdout.write(self.style.NOTICE("Creating facility mappings..."))
        mappings = [
            ('PLANT_001', 'FAC-001', 'Houston Assembly Plant', 'US'),
            ('PLANT_002', 'FAC-002', 'Chicago Warehouse', 'US'),
            ('PLANT_003', 'FAC-003', 'Berlin Logistics Hub', 'DE'),
        ]
        for plant_code, fac_id, name, country in mappings:
            mapping, created = FacilityMapping.objects.get_or_create(
                tenant=tenant,
                plant_code=plant_code,
                defaults={
                    'facility_id': fac_id,
                    'facility_name': name,
                    'country_code': country
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Mapped {plant_code} to {name}."))

        # 5. Ingest Sample Fixture Files
        # We find files in the project root's backend/fixtures folder
        fixtures_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'fixtures'))
        samples = [
            ('sample_sap_export.txt', Batch.SAP, {
                "material_map": {
                    "50045": {"fuel_type": "diesel", "canonical_unit": "L"},
                    "50046": {"fuel_type": "natural_gas_kg", "canonical_unit": "KG"},
                    "GAS-":  {"fuel_type": "natural_gas_m3", "canonical_unit": "M3"}
                }
            }),
            ('sample_utility.csv', Batch.UTILITY, {
                "meter_unit_map": {
                    "MTR-1043": "MWh",
                    "MTR-2045": "MWh"
                }
            }),
            ('sample_travel_concur.csv', Batch.TRAVEL, {
                "default_currency": "USD"
            }),
        ]

        for filename, source_type, metadata in samples:
            src_path = os.path.join(fixtures_dir, filename)
            if not os.path.exists(src_path):
                self.stdout.write(self.style.ERROR(f"Fixture file not found: {src_path}"))
                continue

            # Simulate file upload by saving to default_storage
            dest_dir = f"batches/{tenant.id}"
            dest_name = f"{dest_dir}/{filename}"
            
            # Make sure target directory exists
            if not default_storage.exists(dest_name):
                with open(src_path, 'rb') as f:
                    default_storage.save(dest_name, f)
                self.stdout.write(self.style.SUCCESS(f"Copied {filename} to storage: {dest_name}"))

            # Create Batch record
            batch = Batch.objects.create(
                tenant=tenant,
                source_type=source_type,
                status=Batch.QUEUED,
                original_filename=filename,
                file_ref=dest_name,
                uploaded_by=analyst,
                metadata=metadata,
                parser_version='1.0.0'
            )

            self.stdout.write(self.style.NOTICE(f"Enqueuing pipeline for {filename}..."))
            
            # Run the ingestion synchronously to populate DB immediately for demo
            try:
                ingest_and_normalize(str(batch.id))
                # Refresh from DB
                batch.refresh_from_db()
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully processed {filename}: "
                    f"{batch.record_count} records normalized ({batch.flagged_count} flagged) - Status: {batch.status}"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process {filename}: {str(e)}"))

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("DEMO SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Login URL: http://localhost:5173/login")
        self.stdout.write(f"Tenant Slug: {tenant_slug}")
        self.stdout.write(f"Analyst User: {analyst_email} / demo1234")
        self.stdout.write(f"Admin User:   {admin_email} / demo1234")
        self.stdout.write("=" * 50 + "\n")
