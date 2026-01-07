import { useState, useEffect, useRef } from 'react'
import { api } from '../api'

function Step5Run({ jobId, onReset }) {
    const [parallelism, setParallelism] = useState(4);
    const [activeRun, setActiveRun] = useState(null);
    const [runDevices, setRunDevices] = useState([]);
    const [selectedDeviceEvents, setSelectedDeviceEvents] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const pollTimer = useRef(null);

    useEffect(() => {
        // Check if there's an ongoing run for this job
        checkActiveRuns();
        return () => stopPolling();
    }, [jobId]);

    const checkActiveRuns = async () => {
        try {
            const runs = await api.getRuns(jobId);
            const ongoing = runs.find(r => r.status === 'running');
            if (ongoing) {
                setActiveRun(ongoing);
                startPolling(ongoing.id);
            } else if (runs.length > 0) {
                // Just show the latest completed run
                setActiveRun(runs[0]);
                loadRunData(runs[0].id);
            }
        } catch (err) {
            console.error("Failed to check runs", err);
        }
    };

    const startRun = async () => {
        setLoading(true);
        setError('');
        try {
            const run = await api.createRun(jobId, parallelism);
            setActiveRun(run);
            startPolling(run.id);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const startPolling = (runId) => {
        stopPolling();
        loadRunData(runId);
        pollTimer.current = setInterval(() => loadRunData(runId), 2000);
    };

    const stopPolling = () => {
        if (pollTimer.current) {
            clearInterval(pollTimer.current);
            pollTimer.current = null;
        }
    };

    const loadRunData = async (runId) => {
        try {
            const [runData, devicesData] = await Promise.all([
                api.getRun(runId),
                api.getRunDevices(runId)
            ]);

            setActiveRun(runData);
            setRunDevices(devicesData);

            if (runData.status !== 'running') {
                stopPolling();
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    };

    const viewEvents = async (deviceId) => {
        try {
            const events = await api.getRunEvents(activeRun.id);
            // Filter for specific device
            const deviceEvents = events.filter(e => e.device_id === deviceId);
            const devName = runDevices.find(rd => rd.device_id === deviceId)?.status || 'Device';
            setSelectedDeviceEvents({ deviceId, events: deviceEvents });
        } catch (err) {
            alert("Failed to load events: " + err.message);
        }
    };

    return (
        <div className="card">
            <div className="flex justify-between items-center">
                <h2>Step 5: Execution Dashboard</h2>
                {activeRun && (
                    <span className={`badge badge-${activeRun.status === 'running' ? 'running' : 'verified'}`}>
                        Run #{activeRun.id}: {activeRun.status}
                    </span>
                )}
            </div>

            {!activeRun && (
                <div className="text-center py-8">
                    <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                        Ready to deploy? Choose your parallelism and hit Start.
                    </p>
                    <div className="form-group" style={{ maxWidth: '200px', margin: '0 auto' }}>
                        <label>Max Parallel Devices</label>
                        <select value={parallelism} onChange={(e) => setParallelism(parseInt(e.target.value))}>
                            <option value="1">1 (Sequential)</option>
                            <option value="2">2</option>
                            <option value="4">4 (Recommended)</option>
                            <option value="8">8</option>
                        </select>
                    </div>
                    <button className="btn btn-primary mt-4" onClick={startRun} disabled={loading} style={{ width: '200px' }}>
                        {loading ? 'Starting...' : '🚀 Start Configuration'}
                    </button>
                </div>
            )}

            {activeRun && (
                <div className="mt-4">
                    <table>
                        <thead>
                            <tr>
                                <th>Port</th>
                                <th>Status</th>
                                <th>Error / Message</th>
                                <th>Hash</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {runDevices.map(rd => (
                                <tr key={rd.device_id}>
                                    <td>Port {rd.port || '?'}</td>
                                    <td>
                                        <span className={`badge badge-${rd.status.toLowerCase()}`}>
                                            {rd.status}
                                        </span>
                                    </td>
                                    <td style={{ fontSize: '0.8rem', color: rd.error_code ? 'var(--error-color)' : 'var(--text-muted)' }}>
                                        {rd.error_code ? `[${rd.error_code}] ${rd.error_message}` : 'Running...'}
                                    </td>
                                    <td style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{rd.template_hash || '-'}</td>
                                    <td>
                                        <button className="btn btn-ghost" style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }} onClick={() => viewEvents(rd.device_id)}>
                                            Logs
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {activeRun.status !== 'running' && (
                        <div className="mt-8 card" style={{ background: 'rgba(99, 102, 241, 0.1)', borderColor: 'var(--primary-color)' }}>
                            <h3>Run Completed</h3>
                            <p>Deployment finished. You can now download the audit reports.</p>
                            <div className="flex gap-2 mt-4">
                                <button className="btn btn-secondary" onClick={() => api.downloadReport(activeRun.id, 'csv')}>Download CSV Report</button>
                                <button className="btn btn-secondary" onClick={() => api.downloadReport(activeRun.id, 'json')}>Download JSON Report</button>
                                <button className="btn btn-primary" onClick={onReset}>Start New Job</button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {selectedDeviceEvents && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', zIndex: 100, display: 'flex',
                    alignItems: 'center', justifyContent: 'center', padding: '2rem'
                }}>
                    <div className="card" style={{ width: '100%', maxWidth: '800px', maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        <div className="flex justify-between items-center mb-4">
                            <h3>Device Event Log</h3>
                            <button className="btn btn-ghost" onClick={() => setSelectedDeviceEvents(null)}>✕ Close</button>
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', background: '#0a0f1d', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                            {selectedDeviceEvents.events.map((e, i) => (
                                <div key={i} style={{ marginBottom: '0.5rem', fontSize: '0.85rem', borderBottom: '1px solid #1e293b', paddingBottom: '0.25rem' }}>
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>[{new Date(e.ts).toLocaleTimeString()}]</span>{' '}
                                    <span style={{
                                        color: e.level === 'ERROR' ? 'var(--error-color)' : e.level === 'WARNING' ? 'var(--warning-color)' : 'var(--text-color)',
                                        fontWeight: e.level !== 'DEBUG' ? 600 : 400
                                    }}>
                                        {e.level}: {e.message}
                                    </span>
                                    {e.raw && <pre style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: '#6b7280', overflowX: 'auto' }}>{e.raw}</pre>}
                                </div>
                            ))}
                            {selectedDeviceEvents.events.length === 0 && <p className="text-center">No logs found for this device.</p>}
                        </div>
                    </div>
                </div>
            )}

            {error && <div className="card mt-4" style={{ borderColor: 'var(--error-color)' }}>
                <p style={{ color: 'var(--error-color)', margin: 0 }}>{error}</p>
            </div>}
        </div>
    )
}

export default Step5Run
