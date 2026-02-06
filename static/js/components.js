/**
 * DOM rendering functions — pure HTML builders.
 */
const Components = {

  /** Render console panel lines */
  renderConsole(history) {
    return history.map(entry => {
      const cls = entry.type ? `console-line ${entry.type}` : 'console-line';
      const prompt = entry.type === '' ? '<span class="prompt">&gt;</span>' : '';
      return `<div class="${cls}">${prompt}${escapeHtml(entry.text)}</div>`;
    }).join('');
  },

  /** Render a single study card */
  renderStudyCard(study, isExpanded, runs, selectedRuns) {
    const acc = study.accession || study.experiment || '—';
    const title = study.title || '—';
    const summary = study.summary || '';
    const organism = study.organism || '';
    const platform = study.platform || study.strategy || '';
    const date = study.date || '';
    const runCount = study.runs || study.samples || '';

    let metaParts = [];
    if (organism) metaParts.push(organism);
    if (platform) metaParts.push(platform);
    if (date) metaParts.push(date);
    if (runCount) metaParts.push(`${runCount} runs`);

    let runsHtml = '';
    if (isExpanded && runs) {
      runsHtml = this.renderRunsSection(acc, runs, selectedRuns);
    } else if (isExpanded) {
      runsHtml = `<div class="runs-section"><div class="loading-msg"><span class="spinner"></span> Loading runs...</div></div>`;
    }

    return `
      <div class="study-card" data-accession="${escapeAttr(acc)}">
        <div class="study-card-header">
          <span class="study-accession">${escapeHtml(acc)}</span>
          <div class="study-meta">${metaParts.map(p => `<span>${escapeHtml(String(p))}</span>`).join('<span class="run-detail-sep">|</span>')}</div>
        </div>
        <div class="study-title">${escapeHtml(title)}</div>
        ${summary ? `<div class="study-summary">${escapeHtml(summary)}</div>` : ''}
        <div class="study-actions">
          <button class="btn btn-sm btn-outline btn-expand" data-accession="${escapeAttr(acc)}">${isExpanded ? 'Collapse' : 'Expand Runs'}</button>
          ${isExpanded && runs && runs.length > 0 ? `<button class="btn btn-sm btn-primary btn-add-selected" data-accession="${escapeAttr(acc)}" data-title="${escapeAttr(title)}">+ Add Selected</button>` : ''}
        </div>
        ${runsHtml}
      </div>`;
  },

  /** Render runs section within a study card */
  renderRunsSection(studyAcc, runs, selectedRuns) {
    if (!runs || runs.length === 0) {
      return `<div class="runs-section"><span class="text-muted" style="font-size:12px">No runs found</span></div>`;
    }

    const selected = selectedRuns || new Set();
    const allSelected = runs.every(r => selected.has(r.accession));

    const header = `
      <div class="runs-header">
        <span>${runs.length} run${runs.length > 1 ? 's' : ''}</span>
        <label style="font-size:12px;cursor:pointer;color:var(--text-muted)">
          <input type="checkbox" class="toggle-all-runs" data-study="${escapeAttr(studyAcc)}" ${allSelected ? 'checked' : ''}> Select All
        </label>
      </div>`;

    const rows = runs.map(run => {
      const checked = selected.has(run.accession) ? 'checked' : '';
      const details = [run.strategy, run.source, run.platform].filter(Boolean).join(' / ');
      const sample = run.sample || '';
      return `
        <div class="run-row">
          <input type="checkbox" class="run-checkbox" data-study="${escapeAttr(studyAcc)}" data-run="${escapeAttr(run.accession)}" ${checked}>
          <span class="run-acc">${escapeHtml(run.accession)}</span>
          <span class="run-detail">${escapeHtml(details || '—')}</span>
          ${sample ? `<span class="run-detail-sep">|</span><span class="run-detail">${escapeHtml(sample)}</span>` : ''}
        </div>`;
    }).join('');

    return `<div class="runs-section">${header}${rows}</div>`;
  },

  /** Render all study cards */
  renderResults(studies, expandedStudy, studyRuns, selectedRuns) {
    if (!studies || studies.length === 0) return '';
    return studies.map(study => {
      const acc = study.accession || study.experiment || '';
      const isExpanded = expandedStudy === acc;
      const runs = studyRuns[acc] || null;
      const selected = selectedRuns[acc] || new Set();
      return this.renderStudyCard(study, isExpanded, runs, selected);
    }).join('');
  },

  /** Render staged studies inside the manifest modal */
  renderStagedStudies(staged) {
    if (staged.length === 0) {
      return `<div class="text-muted" style="padding:16px 0;text-align:center;font-size:13px">No studies staged yet. Search and add runs first.</div>`;
    }
    return staged.map((s, i) => {
      // Compute study-level totals
      const totalSpots = s.runs.reduce((sum, r) => sum + (parseInt(r.spots) || 0), 0);
      const totalBases = s.runs.reduce((sum, r) => sum + (parseInt(r.bases) || 0), 0);
      const strategy = s.runs.find(r => r.strategy)?.strategy || '';
      const platform = s.runs.find(r => r.platform)?.platform || '';
      const studyMeta = [
        strategy,
        platform,
        `${s.runs.length} runs`,
        totalSpots ? `${formatNumber(totalSpots)} spots` : '',
        totalBases ? formatSize(totalBases) : '',
      ].filter(Boolean).join(' · ');

      return `
      <div class="staged-study-group" data-accession="${escapeAttr(s.accession)}">
        <div class="staged-study-header">
          <div>
            <span class="staged-study-num">#${i + 1}</span>
            <span class="staged-study-acc">${escapeHtml(s.accession)}</span>
          </div>
          <button class="staged-study-remove" data-accession="${escapeAttr(s.accession)}" title="Remove study">&#128465;</button>
        </div>
        <div class="staged-study-meta">${escapeHtml(studyMeta)}</div>
        <div class="staged-run-list">
          ${s.runs.map(r => {
            const acc = typeof r === 'string' ? r : r.accession;
            const spots = r.spots ? formatNumber(parseInt(r.spots)) + ' spots' : '';
            const bases = r.bases ? formatSize(parseInt(r.bases)) : '';
            const meta = [r.strategy || '', spots, bases].filter(Boolean).join(' · ');
            return `<div class="staged-run"><label><input type="checkbox" class="staged-run-checkbox" data-accession="${escapeAttr(s.accession)}" data-run="${escapeAttr(acc)}" checked> <span class="run-acc">${escapeHtml(acc)}</span>${meta ? `<span class="run-detail">${escapeHtml(meta)}</span>` : ''}</label></div>`;
          }).join('')}
        </div>
      </div>`;
    }).join('');
  },

  /** Render manifests list */
  renderManifestsList(manifests) {
    if (!manifests || manifests.length === 0) {
      return `<div class="text-muted" style="padding:24px;text-align:center;font-size:13px">No manifests yet. Create one by staging runs and approving.</div>`;
    }

    return manifests.map(m => {
      const statusClass = m.status === 'approved' ? 'manifest-status-approved' :
                          m.status === 'importing' ? 'manifest-status-importing' :
                          m.status === 'pending' ? 'manifest-status-pending' : '';
      const tags = m.tags ? Object.entries(m.tags).map(([k, v]) => `${k}=${v}`).join(', ') : '';

      let actions = '';
      if (m.status === 'pending') {
        actions = `<button class="btn btn-sm btn-success manifest-action-approve" data-name="${escapeAttr(m.name)}">Approve</button>`;
      } else if (m.status === 'approved') {
        actions = `<button class="btn btn-sm btn-primary manifest-action-load" data-name="${escapeAttr(m.name)}">Load to HOX</button>`;
      } else if (m.status === 'importing') {
        actions = `<span class="text-muted" style="font-size:12px"><span class="spinner"></span> Importing...</span>`;
      }

      return `
      <div class="manifest-card">
        <div class="manifest-card-header">
          <div class="manifest-card-name">${escapeHtml(m.name)}</div>
          <span class="manifest-status ${statusClass}">${escapeHtml(m.status)}</span>
        </div>
        <div class="manifest-card-desc">${escapeHtml(m.description || '')}</div>
        <div class="manifest-card-meta">
          <span>${m.runs || 0} runs</span>
          <span>${escapeHtml(m.created || '')}</span>
          ${tags ? `<span>${escapeHtml(tags)}</span>` : ''}
        </div>
        <div class="manifest-card-actions">${actions}</div>
      </div>`;
    }).join('');
  },
};

/* Utility: escape HTML */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/** Format large numbers: 1234567 -> "1.23M" */
function formatNumber(n) {
  if (!n || isNaN(n)) return '—';
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return String(n);
}

/** Format bases to human-readable size: 5000000000 -> "4.7 Gb" */
function formatSize(bases) {
  if (!bases || isNaN(bases)) return '';
  if (bases >= 1e12) return (bases / 1e12).toFixed(1) + ' Tb';
  if (bases >= 1e9) return (bases / 1e9).toFixed(1) + ' Gb';
  if (bases >= 1e6) return (bases / 1e6).toFixed(1) + ' Mb';
  if (bases >= 1e3) return (bases / 1e3).toFixed(1) + ' Kb';
  return bases + ' bp';
}

function escapeAttr(str) {
  return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
