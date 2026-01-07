const API_URL = window.location.origin.includes('localhost:5173')
  ? 'http://localhost:8000'
  : '';

const request = async (path, options = {}) => {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    let message = error.detail || response.statusText;
    if (Array.isArray(message)) {
      message = message.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
    }
    throw new Error(message);
  }

  if (response.headers.get('Content-Type')?.includes('application/json')) {
    return response.json();
  }
  return response.text();
};

export const api = {
  // Jobs
  getJobs: () => request('/jobs'),
  createJob: (data) => request('/jobs', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getJob: (id) => request(`/jobs/${id}`),

  // CSV Import
  importCSV: (jobId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_URL}/jobs/${jobId}/devices/import-csv`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },

  // Devices
  getDevices: (jobId) => request(`/jobs/${jobId}/devices`),
  createDevice: (jobId, data) => request(`/jobs/${jobId}/devices`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  deleteDevice: (deviceId) => request(`/devices/${deviceId}`, {
    method: 'DELETE',
  }),
  updateDevice: (deviceId, data) => request(`/devices/${deviceId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),

  // Dry-run / Preview
  getPreview: (jobId) => request(`/jobs/${jobId}/preview`, { method: 'POST' }),
  runDryRun: (jobId) => request(`/jobs/${jobId}/dry-run`, { method: 'POST' }),

  // Runs
  getRunsByJob: (jobId) => request(`/jobs/${jobId}/runs`), // Not strictly needed for wizard but good to have
  createRun: (jobId, parallelism = 4) => request(`/jobs/${jobId}/runs`, {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId, parallelism }),
  }),
  getRun: (id) => request(`/runs/${id}`),
  getRunDevices: (jobId) => request(`/jobs/${jobId}/devices`),
  getRunLogs: (id) => request(`/runs/${id}/logs`),

  // Reports
  getReportJson: (id) => `${API_URL}/runs/${id}/report.json`,
  getReportCsv: (id) => `${API_URL}/runs/${id}/report.csv`,
  downloadReport: async (id, type = 'csv') => {
    const url = type === 'json' ? `/runs/${id}/report.json` : `/runs/${id}/report.csv`;
    const response = await fetch(`${API_URL}${url}`, {
      headers: {
        'X-Passcode': localStorage.getItem('api_passcode') || ''
      }
    });
    if (!response.ok) throw new Error('Failed to download report');
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = `report_${id}.${type}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);
  }
};
