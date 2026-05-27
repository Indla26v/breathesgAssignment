from django.db import models
from apps.normalization.models import NormalizedRecord
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ApprovalEvent(models.Model):
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    FLAGGED = 'FLAGGED'
    EDITED = 'EDITED'
    COMMENT = 'COMMENT'

    ACTION_CHOICES = [
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (FLAGGED, 'Flagged'),
        (EDITED, 'Edited'),
        (COMMENT, 'Comment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(NormalizedRecord, on_delete=models.CASCADE, related_name='approval_events')
    analyst = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_events')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    previous_value = models.JSONField(null=True, blank=True)  # Populated on EDITED action
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.analyst.email} on record {self.record.id}"
