const API_URL = 'http://localhost:8000';

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
    return fetch(`${API_URL}/jobs/${jobId}/import`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  },

  // Devices
  getDevices: (jobId) => request(`/jobs/${jobId}/devices`),
  updateDevice: (deviceId, data) => request(`/devices/${deviceId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),

  // Dry-run / Preview
  getPreview: (jobId) => request(`/jobs/${jobId}/preview`, { method: 'POST' }),
  runDryRun: (jobId) => request(`/jobs/${jobId}/dry-run`, { method: 'POST' }),

  // Runs
  getRuns: (jobId) => request(`/runs?job_id=${jobId}`),
  createRun: (jobId, parallelism = 4) => request('/runs', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId, parallelism }),
  }),
  getRun: (id) => request(`/runs/${id}`),
  getRunDevices: (id) => request(`/runs/${id}/devices`),
  getRunEvents: (id) => request(`/runs/${id}/events`),

  // Reports
  getReportJson: (id) => `${API_URL}/runs/${id}/report.json`,
  getReportCsv: (id) => `${API_URL}/runs/${id}/report.csv`,
};
