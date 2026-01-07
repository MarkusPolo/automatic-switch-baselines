import { useState, useEffect } from 'react'
import { api } from '../api'

function Step2Import({ jobId, onNext, onPrev }) {
    const [activeTab, setActiveTab] = useState('csv'); // 'csv' or 'manual'
    const [file, setFile] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [devices, setDevices] = useState([]);

    // Manual form state
    const [manualForm, setManualForm] = useState({
        hostname: '',
        mgmt_ip: '',
        mask: '',
        gateway: '',
        vendor: 'generic',
        mgmt_vlan: ''
    });

    useEffect(() => {
        loadDevices();
    }, [jobId]);

    const loadDevices = async () => {
        try {
            const data = await api.getDevices(jobId);
            setDevices(data);
        } catch (err) {
            console.error('Failed to load devices', err);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        setError('');
        setImportResult(null);
        try {
            const result = await api.importCSV(jobId, file);
            setImportResult(result);
            loadDevices();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleManualAdd = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const data = {
                ...manualForm,
                mgmt_vlan: manualForm.mgmt_vlan ? parseInt(manualForm.mgmt_vlan) : null
            };
            await api.createDevice(jobId, data);
            setManualForm({
                hostname: '',
                mgmt_ip: '',
                mask: '',
                gateway: '',
                vendor: 'generic',
                mgmt_vlan: ''
            });
            loadDevices();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (deviceId) => {
        try {
            await api.deleteDevice(deviceId);
            loadDevices();
        } catch (err) {
            setError(err.message);
        }
    };

    const hasErrors = importResult?.errors && importResult.errors.length > 0;

    return (
        <div className="card">
            <h2>Step 2: Device Configuration</h2>
            <p style={{ color: 'var(--text-muted)' }}>
                You can either upload a CSV file or add devices manually.
            </p>

            <div className="flex gap-4 mt-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
                <button
                    className={`pb-2 px-1 ${activeTab === 'csv' ? 'border-b-2' : ''}`}
                    style={{ borderColor: activeTab === 'csv' ? 'var(--primary-color)' : 'transparent', color: activeTab === 'csv' ? 'var(--primary-color)' : 'inherit' }}
                    onClick={() => setActiveTab('csv')}
                >
                    CSV Import
                </button>
                <button
                    className={`pb-2 px-1 ${activeTab === 'manual' ? 'border-b-2' : ''}`}
                    style={{ borderColor: activeTab === 'manual' ? 'var(--primary-color)' : 'transparent', color: activeTab === 'manual' ? 'var(--primary-color)' : 'inherit' }}
                    onClick={() => setActiveTab('manual')}
                >
                    Manual Entry
                </button>
            </div>

            {activeTab === 'csv' && (
                <div className="mt-4">
                    <div className="form-group">
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

                    {importResult && hasErrors && (
                        <div className="mt-4 card" style={{ borderColor: 'var(--error-color)', background: 'rgba(239, 68, 68, 0.05)' }}>
                            <p style={{ color: 'var(--error-color)', fontWeight: 600 }}>Validation Errors found in CSV:</p>
                            <ul style={{ fontSize: '0.875rem', paddingLeft: '1.25rem' }}>
                                {importResult.errors.map((err, i) => (
                                    <li key={i} style={{ marginBottom: '0.5rem' }}>
                                        <strong>Row {err.row || '?'}:</strong> {err.message}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'manual' && (
                <form onSubmit={handleManualAdd} className="mt-4">
                    <div className="flex flex-wrap gap-4">
                        <div className="form-group" style={{ flex: '1 1 200px' }}>
                            <label>Hostname *</label>
                            <input
                                type="text"
                                required
                                value={manualForm.hostname}
                                onChange={e => setManualForm({ ...manualForm, hostname: e.target.value })}
                                placeholder="sw-leaf-01"
                            />
                        </div>
                        <div className="form-group" style={{ flex: '1 1 200px' }}>
                            <label>MGMT IP *</label>
                            <input
                                type="text"
                                required
                                value={manualForm.mgmt_ip}
                                onChange={e => setManualForm({ ...manualForm, mgmt_ip: e.target.value })}
                                placeholder="10.0.0.1"
                            />
                        </div>
                        <div className="form-group" style={{ flex: '1 1 100px' }}>
                            <label>Mask *</label>
                            <input
                                type="text"
                                required
                                value={manualForm.mask}
                                onChange={e => setManualForm({ ...manualForm, mask: e.target.value })}
                                placeholder="255.255.255.0"
                            />
                        </div>
                        <div className="form-group" style={{ flex: '1 1 200px' }}>
                            <label>Gateway *</label>
                            <input
                                type="text"
                                required
                                value={manualForm.gateway}
                                onChange={e => setManualForm({ ...manualForm, gateway: e.target.value })}
                                placeholder="10.0.0.254"
                            />
                        </div>
                        <div className="form-group" style={{ flex: '1 1 150px' }}>
                            <label>Vendor</label>
                            <select
                                value={manualForm.vendor}
                                onChange={e => setManualForm({ ...manualForm, vendor: e.target.value })}
                            >
                                <option value="generic">Generic</option>
                                <option value="cisco">Cisco</option>
                            </select>
                        </div>
                        <div className="form-group" style={{ flex: '1 1 100px' }}>
                            <label>VLAN</label>
                            <input
                                type="number"
                                value={manualForm.mgmt_vlan}
                                onChange={e => setManualForm({ ...manualForm, mgmt_vlan: e.target.value })}
                                placeholder="10"
                            />
                        </div>
                    </div>
                    <button type="submit" className="btn btn-primary mt-4" disabled={loading}>
                        {loading ? 'Adding...' : 'Add Device'}
                    </button>
                </form>
            )}

            {error && <div className="card mt-4" style={{ borderColor: 'var(--error-color)', padding: '1rem' }}>
                <p style={{ color: 'var(--error-color)', margin: 0 }}>{error}</p>
            </div>}

            {devices.length > 0 && (
                <div className="mt-8">
                    <div className="flex justify-between items-center mb-2">
                        <h3>Configured Devices ({devices.length})</h3>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Hostname</th>
                                <th>IP Address</th>
                                <th>Vendor</th>
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
                                        <button
                                            className="btn"
                                            style={{ color: 'var(--error-color)', padding: '0.25rem 0.5rem' }}
                                            onClick={() => handleDelete(dev.id)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="flex justify-between mt-8">
                <button className="btn btn-secondary" onClick={onPrev}>Back</button>
                <button
                    className="btn btn-primary"
                    disabled={devices.length === 0}
                    onClick={onNext}
                >
                    Continue to Port Mapping
                </button>
            </div>
        </div>
    )
}

export default Step2Import
