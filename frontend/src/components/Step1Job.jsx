import { useState } from 'react'
import { api } from '../api'

function Step1Job({ onNext }) {
    const [name, setName] = useState('');
    const [customer, setCustomer] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const job = await api.createJob({ name, customer });
            onNext(job);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card">
            <h2>Step 1: Create a Job</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                A job groups all switches that should be configured with the same baseline logic.
            </p>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="jobName">Job Name *</label>
                    <input
                        id="jobName"
                        type="text"
                        placeholder="e.g. Campus Core Refresh 2026"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="customer">Customer / Department (Optional)</label>
                    <input
                        id="customer"
                        type="text"
                        placeholder="e.g. Finance"
                        value={customer}
                        onChange={(e) => setCustomer(e.target.value)}
                    />
                </div>

                {error && <div style={{ color: 'var(--error-color)', marginBottom: '1rem' }}>{error}</div>}

                <div className="text-center mt-4">
                    <button type="submit" className="btn btn-primary" disabled={loading || !name}>
                        {loading ? 'Creating...' : 'Continue to CSV Import'}
                    </button>
                </div>
            </form>
        </div>
    )
}

export default Step1Job
