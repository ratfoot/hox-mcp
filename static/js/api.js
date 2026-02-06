/**
 * API client for the Manifest Curator backend.
 */
const API = {
  async search(query, database = 'sra', organism = 'Homo sapiens', limit = 20, year = '') {
    const params = new URLSearchParams({ query, database, organism, limit });
    if (year) params.append('year', year);
    const resp = await fetch(`/api/search?${params}`);
    return resp.json();
  },

  async getStudyInfo(accession) {
    const resp = await fetch(`/api/study/${encodeURIComponent(accession)}`);
    return resp.json();
  },

  async listRuns(studyAccession) {
    const resp = await fetch(`/api/runs/${encodeURIComponent(studyAccession)}`);
    return resp.json();
  },

  async getFileUrls(accession) {
    const resp = await fetch(`/api/files/${encodeURIComponent(accession)}`);
    return resp.json();
  },

  async createManifest(name, description, studies, tags = null) {
    const resp = await fetch('/api/manifests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, studies, tags }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      return { error: `Server error ${resp.status}: ${text.substring(0, 200)}` };
    }
    return resp.json();
  },

  async listManifests(name = null) {
    const params = name ? `?name=${encodeURIComponent(name)}` : '';
    const resp = await fetch(`/api/manifests${params}`);
    return resp.json();
  },

  async approveManifest(name) {
    const resp = await fetch(`/api/manifests/${encodeURIComponent(name)}/approve`, {
      method: 'POST',
    });
    return resp.json();
  },

  async importToHox(name, setName = null, profile = null) {
    const body = {};
    if (setName) body.set_name = setName;
    if (profile) body.profile = profile;
    const resp = await fetch(`/api/manifests/${encodeURIComponent(name)}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return resp.json();
  },

  async getImportStatus(profile = null) {
    const params = profile ? `?profile=${encodeURIComponent(profile)}` : '';
    const resp = await fetch(`/api/import-status${params}`);
    return resp.json();
  },
};
