import { useState, useEffect } from 'react'
import { api } from '../api'

function Step4Preview({ jobId, onNext, onPrev }) {
    const [previews, setPreviews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dryRunning, setDryRunning] = useState(false);
    const [error, setError] = useState('');
    const [dryRunResult, setDryRunResult] = useState(null);

    useEffect(() => {
        loadPreviews();
    }, [jobId]);

    const loadPreviews = async () => {
        try {
            setLoading(true);
            const data = await api.getPreview(jobId);
            setPreviews(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDryRun = async () => {
        setDryRunning(true);
        setError('');
        setDryRunResult(null);
        try {
            const result = await api.runDryRun(jobId);
            setDryRunResult(result);
        } catch (err) {
            if (err.message.includes('[')) { // It's probably a JSON list of validation errors
                try {
                    setDryRunResult({ success: false, errors: JSON.parse(err.message) });
                } catch {
                    setError(err.message);
                }
            } else {
                setError(err.message);
            }
        } finally {
            setDryRunning(false);
        }
    };

    if (loading) return <div className="text-center">Generating configuration previews...</div>;

    const validationErrors = dryRunResult?.errors || [];
    const dryRunSuccess = dryRunResult?.success || (dryRunResult && validationErrors.length === 0);

    return (
        <div className="card">
            <h2>Step 4: Configuration Preview</h2>
            <p style={{ color: 'var(--text-muted)' }}>
                Review the generated commands for each device and run a dry-run validation.
            </p>

            <div className="mt-4" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
                {previews.map(p => (
                    <div key={p.device_id} className="card" style={{ padding: '1rem', background: 'rgba(15, 23, 42, 0.4)' }}>
                        <div className="flex justify-between items-center mb-2">
                            <h3 style={{ margin: 0, fontSize: '1rem' }}>{p.hostname}</h3>
                            <span className="badge badge-secondary" style={{ fontSize: '0.6rem' }}>{p.vendor}</span>
                        </div>
                        <pre style={{
                            background: '#0a0f1d',
                            padding: '0.75rem',
                            borderRadius: '0.5rem',
                            fontSize: '0.75rem',
                            maxHeight: '200px',
                            overflowY: 'auto',
                            color: '#d1d5db',
                            border: '1px solid var(--border-color)'
                        }}>
                            {p.commands}
                        </pre>
                        <div className="mt-2 text-right">
                            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Hash: {p.hash}</span>
                        </div>
                    </div>
                ))}
            </div>

            {error && <div className="card mt-4" style={{ borderColor: 'var(--error-color)' }}>
                <p style={{ color: 'var(--error-color)', margin: 0 }}>{error}</p>
            </div>}

            {dryRunResult && (
                <div className="mt-4 card" style={{ borderColor: dryRunSuccess ? 'var(--success-color)' : 'var(--error-color)' }}>
                    <div className="flex justify-between items-center">
                        <h3>Dry-Run Results</h3>
                        <span className={`badge ${dryRunSuccess ? 'badge-verified' : 'badge-failed'}`}>
                            {dryRunSuccess ? 'Check Passed' : 'Policy Violations'}
                        </span>
                    </div>

                    {validationErrors.length > 0 && (
                        <ul className="mt-2" style={{ fontSize: '0.875rem' }}>
                            {validationErrors.map((err, i) => (
                                <li key={i} style={{ color: 'var(--error-color)', marginBottom: '0.4rem' }}>
                                    <strong>Device {err.device_id}:</strong> {err.message}
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}> (Field: {err.field})</span>
                                </li>
                            ))}
                        </ul>
                    )}

                    {dryRunSuccess && (
                        <p style={{ color: 'var(--success-color)', margin: '0.5rem 0 0' }}>
                            All configuration rules and vendor templates validated successfully!
                        </p>
                    )}
                </div>
            )}

            <div className="text-center mt-6">
                <button
                    className="btn btn-secondary"
                    onClick={handleDryRun}
                    disabled={dryRunning}
                    style={{ width: '200px' }}
                >
                    {dryRunning ? 'Validating...' : 'Run Dry-Run Check'}
                </button>
            </div>

            <div className="flex justify-between mt-8">
                <button className="btn btn-secondary" onClick={onPrev}>Back</button>
                <button
                    className="btn btn-primary"
                    disabled={dryRunning || (dryRunResult && !dryRunSuccess)}
                    onClick={onNext}
                >
                    {!dryRunResult ? 'Skip to Run (Not Recommended)' : 'Proceed to Deployment'}
                </button>
            </div>
        </div>
    )
}

export default Step4Preview
