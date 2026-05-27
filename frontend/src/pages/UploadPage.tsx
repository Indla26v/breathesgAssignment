import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadBatch } from '../hooks/useBatches';
import {
  Database, Lightbulb, Plane, Upload, ArrowLeft, ArrowRight,
  Settings, Loader2, CheckCircle, FileSpreadsheet
} from 'lucide-react';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [sourceType, setSourceType] = useState<'SAP' | 'UTILITY' | 'TRAVEL' | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [metadataText, setMetadataText] = useState('{}');
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const uploadMutation = useUploadBatch();

  const handleSourceSelect = (type: 'SAP' | 'UTILITY' | 'TRAVEL') => {
    setSourceType(type);
    if (type === 'SAP') {
      setMetadataText(JSON.stringify({
        material_map: {
          "50045": { fuel_type: "diesel", canonical_unit: "L" },
          "50046": { fuel_type: "natural_gas_kg", canonical_unit: "KG" },
          "GAS-":  { fuel_type: "natural_gas_m3", canonical_unit: "M3" }
        }
      }, null, 2));
    } else if (type === 'UTILITY') {
      setMetadataText(JSON.stringify({
        meter_unit_map: { "MTR-1043": "MWh", "MTR-2045": "MWh" }
      }, null, 2));
    } else {
      setMetadataText(JSON.stringify({ default_currency: "USD" }, null, 2));
    }
    setStep(2);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setStep(3);
    }
  };

  const handleUploadSubmit = async () => {
    if (!file || !sourceType) return;
    setUploading(true);
    setErrorMsg('');
    setStep(4);
    let parsedMetadata = {};
    try {
      parsedMetadata = JSON.parse(metadataText);
    } catch {
      setErrorMsg('Invalid metadata JSON structure.');
      setStep(3);
      setUploading(false);
      return;
    }
    try {
      const result = await uploadMutation.mutateAsync({ file, sourceType, metadata: parsedMetadata });
      setTimeout(() => navigate(`/batches/${result.id}`), 1500);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.errors?.[0]?.message || 'Ingestion request failed.');
      setStep(3);
      setUploading(false);
    }
  };

  const sourceDetails: Record<string, { title: string; desc: string; headers: string }> = {
    SAP: {
      title: 'SAP Material & Movements Export',
      desc: 'Tab-delimited flat files exported from SE16 or table exports (EKPO, MSEG).',
      headers: 'Werk | Buchungskreis | Material | Bewegungsart | Menge | Mengeneinheit | Buchungsdatum | Kostenstelle'
    },
    UTILITY: {
      title: 'Utility Portal CSV Export',
      desc: 'Standard meter bill exports containing billing ranges and quantities (kWh, MWh, Therms).',
      headers: 'Account Number | Meter ID | Service Address | Read Date From | Read Date To | Usage (kWh) | Demand (kW) | Charges ($)'
    },
    TRAVEL: {
      title: 'Concur Expense / Travel Report',
      desc: 'CSV spreadsheets containing employee travel details, nights, flight classes, and origins/destinations.',
      headers: 'Report Name | Report ID | Employee | Department | Expense Type | Travel Date | Vendor | Origin | Destination | Distance | Distance Unit | Nights | Ticket Class'
    },
  };

  const sourceIcons: Record<string, { icon: React.ReactNode; bg: string; color: string }> = {
    SAP: { icon: <Database size={20} />, bg: 'var(--source-sap-bg)', color: 'var(--source-sap)' },
    UTILITY: { icon: <Lightbulb size={20} />, bg: 'var(--source-utility-bg)', color: 'var(--source-utility)' },
    TRAVEL: { icon: <Plane size={20} />, bg: 'var(--source-travel-bg)', color: 'var(--source-travel)' },
  };

  return (
    <div className="upload-wizard">
      {/* Header */}
      <div className="upload-header">
        {step > 1 && step < 4 && (
          <button onClick={() => setStep(step - 1)} className="btn btn-secondary btn-icon">
            <ArrowLeft size={14} />
          </button>
        )}
        <div>
          <h2>Upload Emission Data</h2>
          <p>Step {step} of 4 — Ingestion Wizard</p>
        </div>
      </div>

      {errorMsg && <div className="error-alert" style={{ marginBottom: 16 }}>{errorMsg}</div>}

      {/* Step 1: Source Select */}
      {step === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <p>Select the enterprise system source format you wish to ingest:</p>
          <div className="source-cards">
            {(['SAP', 'UTILITY', 'TRAVEL'] as const).map((type) => {
              const si = sourceIcons[type];
              return (
                <div key={type} className="source-card" onClick={() => handleSourceSelect(type)}>
                  <div className="source-card-icon" style={{ background: si.bg, color: si.color }}>
                    {si.icon}
                  </div>
                  <h4>{type === 'SAP' ? 'SAP ERP' : type === 'UTILITY' ? 'Utility Bills' : 'Corporate Travel'}</h4>
                  <p>{sourceDetails[type].desc.substring(0, 100)}…</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 2: File Drop */}
      {step === 2 && sourceType && (
        <div className="card" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <label>Active Source</label>
            <h3 style={{ marginTop: 4 }}>{sourceDetails[sourceType].title}</h3>
            <p style={{ marginTop: 2 }}>{sourceDetails[sourceType].desc}</p>
          </div>

          <div className="file-dropzone">
            <input type="file" accept=".csv,.txt" onChange={handleFileChange} />
            <div className="file-dropzone-icon">
              <Upload size={18} />
            </div>
            <p style={{ fontWeight: 500, color: 'var(--text)', fontSize: '0.875rem', margin: 0 }}>Click to select file</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>Accepts UTF-8 flat files (.txt, .csv) up to 50k rows</p>
          </div>

          <div className="expected-headers">
            <div className="expected-headers-label">
              <FileSpreadsheet size={12} /> Expected Column Headers
            </div>
            <code>{sourceDetails[sourceType].headers}</code>
          </div>
        </div>
      )}

      {/* Step 3: Metadata */}
      {step === 3 && sourceType && file && (
        <div className="card" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <label>Selected File</label>
            <h3 style={{ marginTop: 4 }}>{file.name}</h3>
            <p style={{ marginTop: 2 }}>{(file.size / 1024).toFixed(1)} KB</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Settings size={12} /> Source Parsing Metadata Config (JSON)
            </label>
            <textarea
              rows={8}
              value={metadataText}
              onChange={(e) => setMetadataText(e.target.value)}
              className="font-mono"
              style={{ fontSize: '0.75rem', lineHeight: 1.6 }}
            />
            <p style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', margin: 0 }}>
              Add mapping configurations, unit overrides, or parser instructions specific to this batch.
            </p>
          </div>

          <button onClick={handleUploadSubmit} className="btn btn-primary" style={{ width: '100%', padding: '10px 16px' }}>
            Start Ingestion Pipeline
            <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* Step 4: Progress */}
      {step === 4 && (
        <div className="card upload-progress">
          {uploading ? (
            <>
              <Loader2 size={36} className="animate-spin" />
              <h3>Ingesting & Normalizing Data</h3>
              <p>Uploading files, mapping columns, checking physical dimensions, and screening anomaly rules.</p>
            </>
          ) : (
            <>
              <CheckCircle size={40} style={{ color: 'var(--primary)' }} />
              <h3>Pipeline Enqueued</h3>
              <p>Batch loaded successfully. Redirecting you to the workspace…</p>
            </>
          )}
        </div>
      )}
    </div>
  );
};
