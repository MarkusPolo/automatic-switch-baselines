import { useState, useEffect } from 'react'
import { api } from '../api'

function Step3Devices({ jobId, onNext, onPrev }) {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadDevices();
    }, [jobId]);

    const loadDevices = async () => {
        try {
            const data = await api.getDevices(jobId);
            setDevices(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handlePortChange = (deviceId, port) => {
        setDevices(prev => prev.map(d =>
            d.id === deviceId ? { ...d, port: port ? parseInt(port) : null } : d
        ));
    };

    const checkDuplicates = () => {
        const ports = devices.map(d => d.port).filter(p => p !== null);
        const uniquePorts = new Set(ports);
        return ports.length !== uniquePorts.size;
    };

    const handleSaveAndContinue = async () => {
        if (checkDuplicates()) {
            setError('Duplicate ports detected. Each device must have a unique port.');
            return;
        }

        setSaving(true);
        setError('');
        try {
            // Parallel update
            await Promise.all(devices.map(d =>
                api.updateDevice(d.id, { port: d.port })
            ));
            onNext();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="text-center">Loading devices...</div>;

    const duplicatesFound = checkDuplicates();

    return (
        <div className="card">
            <h2>Step 3: Port Mapping</h2>
            <p style={{ color: 'var(--text-muted)' }}>
                Assign each switch to a physical port (1-16) on your console server.
            </p>

            <div className="mt-4">
                {error && <div style={{ color: 'var(--error-color)', marginBottom: '1rem', fontWeight: 600 }}>{error}</div>}

                <table>
                    <thead>
                        <tr>
                            <th>Hostname</th>
                            <th>Management IP</th>
                            <th>Vendor</th>
                            <th>Console Port (1-16)</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {devices.map(dev => (
                            <tr key={dev.id}>
                                <td>{dev.hostname}</td>
                                <td>{dev.mgmt_ip}</td>
                                <td><span className="badge badge-secondary">{dev.vendor || 'generic'}</span></td>
                                <td>
                                    <select
                                        value={dev.port || ''}
                                        onChange={(e) => handlePortChange(dev.id, e.target.value)}
                                        style={{
                                            borderColor: duplicatesFound && devices.filter(d => d.port === dev.port && d.port !== null).length > 1
                                                ? 'var(--error-color)'
                                                : 'var(--border-color)'
                                        }}
                                    >
                                        <option value="">-- Unassigned --</option>
                                        {[...Array(16)].map((_, i) => (
                                            <option key={i + 1} value={i + 1}>Port {i + 1}</option>
                                        ))}
                                    </select>
                                </td>
                                <td>
                                    <button
                                        className="btn"
                                        style={{ color: 'var(--error-color)', padding: '0.25rem 0.5rem' }}
                                        onClick={async () => {
                                            if (window.confirm(`Delete ${dev.hostname}?`)) {
                                                try {
                                                    await api.deleteDevice(dev.id);
                                                    loadDevices();
                                                } catch (err) {
                                                    setError(err.message);
                                                }
                                            }
                                        }}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {devices.length === 0 && <p className="text-center mt-4">No devices found. Please go back to Step 2.</p>}
            </div>

            <div className="flex justify-between mt-8">
                <button className="btn btn-secondary" onClick={onPrev}>Back</button>
                <button
                    className="btn btn-primary"
                    disabled={saving || devices.length === 0 || devices.some(d => !d.port) || duplicatesFound}
                    onClick={handleSaveAndContinue}
                >
                    {saving ? 'Saving...' : 'Review Configurations'}
                </button>
            </div>
        </div>
    )
}

export default Step3Devices
