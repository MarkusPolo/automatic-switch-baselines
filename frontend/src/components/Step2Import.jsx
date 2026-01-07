import { useState } from 'react'
import { api } from '../api'

function Step2Import({ jobId, onNext, onPrev }) {
    const [file, setFile] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError('');
        setImportResult(null);
        try {
            const result = await api.importCSV(jobId, file);
            setImportResult(result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const hasErrors = importResult?.errors && importResult.errors.length > 0;
    const successCount = importResult?.success_count || 0;

    return (
        <div className="card">
            <h2>Step 2: Import Device CSV</h2>
            <p style={{ color: 'var(--text-muted)' }}>
                Upload a CSV file containing your device configurations (hostname, mgmt_ip, etc.).
            </p>

            <div className="form-group mt-4">
                <label>Select CSV File</label>
                <div className="flex gap-2">
                    <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setFile(e.target.files[0])}
                        style={{ flex: 1 }}
                    />
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={!file || loading}
                    >
                        {loading ? 'Importing...' : 'Upload & Validate'}
                    </button>
                </div>
            </div>

            {error && <div className="card mt-4" style={{ borderColor: 'var(--error-color)', padding: '1rem' }}>
                <p style={{ color: 'var(--error-color)', margin: 0 }}>{error}</p>
            </div>}

            {importResult && (
                <div className="mt-4">
                    <div className="flex justify-between items-center">
                        <h3>Import Result</h3>
                        <span className="badge badge-verified">{successCount} Loaded</span>
                    </div>

                    {hasErrors && (
                        <div className="mt-2 card" style={{ borderColor: 'var(--error-color)', background: 'rgba(239, 68, 68, 0.05)' }}>
                            <p style={{ color: 'var(--error-color)', fontWeight: 600 }}>Validation Errors found:</p>
                            <ul style={{ fontSize: '0.875rem', paddingLeft: '1.25rem' }}>
                                {importResult.errors.map((err, i) => (
                                    <li key={i} style={{ marginBottom: '0.5rem' }}>
                                        <strong>Row {err.row || '?'}:</strong> {err.message}
                                        {err.suggestion && <em style={{ color: 'var(--text-muted)' }}> — Suggestion: {err.suggestion}</em>}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {!hasErrors && successCount > 0 && (
                        <div className="card mt-2" style={{ borderColor: 'var(--success-color)', background: 'rgba(34, 197, 94, 0.05)' }}>
                            <p style={{ color: 'var(--success-color)', margin: 0 }}>
                                All devices imported successfully without validation errors!
                            </p>
                        </div>
                    )}
                </div>
            )}

            <div className="flex justify-between mt-8">
                <button className="btn btn-secondary" onClick={onPrev}>Back</button>
                <button
                    className="btn btn-primary"
                    disabled={!importResult || successCount === 0}
                    onClick={onNext}
                >
                    Continue to Port Mapping
                </button>
            </div>
        </div>
    )
}

export default Step2Import
