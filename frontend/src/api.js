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
    throw new Error(error.detail || response.statusText);
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
};
