/**
 * App controller — event binding and flow orchestration.
 */
(function () {
  // DOM refs
  const $console = document.getElementById('console-lines');
  const $searchInput = document.getElementById('search-input');
  const $btnSearch = document.getElementById('btn-search');
  const $dbChips = document.getElementById('db-chips');
  const $results = document.getElementById('results');
  const $yearFilter = document.getElementById('year-filter');
  const $hasReadsFilter = document.getElementById('has-reads-filter');
  const $stagedBanner = document.getElementById('staged-banner');
  const $stagedCount = document.getElementById('staged-count');
  const $btnOpenManifest = document.getElementById('btn-open-manifest');
  const $modalOverlay = document.getElementById('modal-overlay');
  const $modalClose = document.getElementById('modal-close');
  const $stagedStudies = document.getElementById('staged-studies');
  const $btnApprove = document.getElementById('btn-approve');
  const $approvalBanner = document.getElementById('approval-banner');
  const $approvalText = document.getElementById('approval-text');
  const $btnLoadHox = document.getElementById('btn-load-hox');
  const $btnDismissApproval = document.getElementById('btn-dismiss-approval');
  const $btnManifests = document.getElementById('btn-manifests');

  // --- Init ---
  logInfo('NCBI SRA Manifest Curator ready.');
  logInfo('Select a database, enter a query, and press Search.');

  // --- Database chips ---
  $dbChips.addEventListener('click', (e) => {
    const chip = e.target.closest('.chip:not(.disabled)');
    if (!chip) return;
    $dbChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    State.database = chip.dataset.db;
    logCmd(`database = ${chip.textContent.trim()}`);
  });

  // --- Search ---
  $btnSearch.addEventListener('click', doSearch);
  $searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doSearch();
  });

  async function doSearch() {
    const query = $searchInput.value.trim();
    if (!query) return;

    const year = $yearFilter.value;
    const hasReadsOnly = $hasReadsFilter.checked;

    logCmd(`search "${query}" --db=${State.database}${year ? ' --year=' + year : ''}`);
    State.loading = true;
    State.expandedStudy = null;
    $results.innerHTML = `<div class="loading-msg"><span class="spinner"></span> Searching ${State.database.toUpperCase()}...</div>`;

    try {
      const data = await API.search(query, State.database, 'Homo sapiens', 20, year);
      let studies = data.studies || [];

      // Client-side filter for "has reads" (SRA dedup already done server-side)
      if (hasReadsOnly) {
        studies = studies.filter(s => (s.runs || 0) > 0);
      }

      State.searchResults = studies;
      if (data.resolved_query) {
        logInfo(`Query: ${data.resolved_query}`);
      }
      logInfo(`Found ${data.total_found || 0} results, showing ${State.searchResults.length}${hasReadsOnly ? ' (with reads)' : ''}`);

      if (State.searchResults.length === 0) {
        $results.innerHTML = `<div class="text-muted" style="padding:24px;text-align:center">No studies found. Try different search terms${hasReadsOnly ? ' or uncheck "Has reads only"' : ''}.</div>`;
      } else {
        renderResults();
      }
    } catch (err) {
      logError(`Search failed: ${err.message}`);
      $results.innerHTML = '';
    } finally {
      State.loading = false;
    }
  }

  // --- Results event delegation ---
  $results.addEventListener('click', (e) => {
    // Expand / Collapse
    const btnExpand = e.target.closest('.btn-expand');
    if (btnExpand) {
      const acc = btnExpand.dataset.accession;
      if (State.expandedStudy === acc) {
        State.expandedStudy = null;
        renderResults();
      } else {
        expandStudy(acc);
      }
      return;
    }

    // Add Selected
    const btnAdd = e.target.closest('.btn-add-selected');
    if (btnAdd) {
      const acc = btnAdd.dataset.accession;
      const title = btnAdd.dataset.title;
      const selected = State.selectedRuns[acc];
      const allRuns = State.studyRuns[acc] || [];
      if (selected && selected.size > 0) {
        // Pass full run objects (with spots/bases/strategy metadata)
        const selectedRuns = allRuns.filter(r => selected.has(r.accession));
        State.stageStudy(acc, title, selectedRuns);
        logInfo(`Staged ${selected.size} runs from ${acc}`);
        updateStagedBanner();
      }
      return;
    }
  });

  // Checkbox changes (delegation)
  $results.addEventListener('change', (e) => {
    // Individual run checkbox
    if (e.target.classList.contains('run-checkbox')) {
      const study = e.target.dataset.study;
      const run = e.target.dataset.run;
      if (!State.selectedRuns[study]) State.selectedRuns[study] = new Set();
      if (e.target.checked) {
        State.selectedRuns[study].add(run);
      } else {
        State.selectedRuns[study].delete(run);
      }
      // Update select-all checkbox state
      updateSelectAll(study);
      return;
    }

    // Toggle all
    if (e.target.classList.contains('toggle-all-runs')) {
      const study = e.target.dataset.study;
      const runs = State.studyRuns[study] || [];
      if (!State.selectedRuns[study]) State.selectedRuns[study] = new Set();
      if (e.target.checked) {
        runs.forEach(r => State.selectedRuns[study].add(r.accession));
      } else {
        State.selectedRuns[study].clear();
      }
      renderResults();
      return;
    }
  });

  function updateSelectAll(study) {
    const runs = State.studyRuns[study] || [];
    const selected = State.selectedRuns[study] || new Set();
    const toggle = $results.querySelector(`.toggle-all-runs[data-study="${study}"]`);
    if (toggle) {
      toggle.checked = runs.length > 0 && runs.every(r => selected.has(r.accession));
    }
  }

  async function expandStudy(acc) {
    State.expandedStudy = acc;
    renderResults(); // shows spinner

    if (!State.studyRuns[acc]) {
      logCmd(`list_runs("${acc}")`);
      try {
        const data = await API.listRuns(acc);
        const runs = data.runs || [];
        if (runs.length > 0) {
          State.studyRuns[acc] = runs;
          State.selectedRuns[acc] = new Set(runs.map(r => r.accession));
          logInfo(`${runs.length} runs loaded for ${acc}`);
        } else {
          throw new Error('No runs from API');
        }
      } catch (err) {
        // Fallback: use experiment accessions from search results
        const exps = (State.searchExperiments || {})[acc] || [];
        if (exps.length > 0) {
          const runs = exps.map(e => ({ accession: e, sample: '', strategy: '', source: '', platform: '' }));
          State.studyRuns[acc] = runs;
          State.selectedRuns[acc] = new Set(exps);
          logInfo(`${exps.length} experiments loaded for ${acc} (from search cache)`);
        } else {
          logError(`Failed to load runs: ${err.message}`);
          State.studyRuns[acc] = [];
        }
      }
    }
    renderResults();
  }

  function renderResults() {
    $results.innerHTML = Components.renderResults(
      State.searchResults,
      State.expandedStudy,
      State.studyRuns,
      State.selectedRuns
    );
  }

  // --- Staged Banner ---
  function updateStagedBanner() {
    const count = State.stagedRunCount;
    if (count > 0) {
      $stagedCount.textContent = `${count} run${count > 1 ? 's' : ''} staged from ${State.staged.length} stud${State.staged.length > 1 ? 'ies' : 'y'}`;
      $stagedBanner.classList.remove('hidden');
    } else {
      $stagedBanner.classList.add('hidden');
    }
  }

  // --- Manifest Modal ---
  $btnOpenManifest.addEventListener('click', () => {
    $modalOverlay.classList.remove('hidden');
    renderStagedModal();
  });

  $modalClose.addEventListener('click', () => {
    $modalOverlay.classList.add('hidden');
  });

  $modalOverlay.addEventListener('click', (e) => {
    if (e.target === $modalOverlay) $modalOverlay.classList.add('hidden');
  });

  // Remove staged study from modal
  $stagedStudies.addEventListener('click', (e) => {
    const btn = e.target.closest('.staged-study-remove');
    if (btn) {
      State.unstageStudy(btn.dataset.accession);
      renderStagedModal();
      updateStagedBanner();
    }
  });

  // Toggle individual runs in manifest modal
  $stagedStudies.addEventListener('change', (e) => {
    if (e.target.classList.contains('staged-run-checkbox')) {
      const acc = e.target.dataset.accession;
      const run = e.target.dataset.run;
      const study = State.staged.find(s => s.accession === acc);
      if (!study) return;
      if (e.target.checked) {
        if (!study.runs.includes(run)) study.runs.push(run);
      } else {
        study.runs = study.runs.filter(r => (typeof r === 'string' ? r : r.accession) !== run);
        // Remove study entirely if no runs left
        if (study.runs.length === 0) {
          State.unstageStudy(acc);
          renderStagedModal();
        }
      }
      updateStagedBanner();
    }
  });

  function renderStagedModal() {
    $stagedStudies.innerHTML = Components.renderStagedStudies(State.staged);
  }

  // --- Approve ---
  function showModalError(msg) {
    let el = document.getElementById('modal-error');
    if (!el) {
      el = document.createElement('div');
      el.id = 'modal-error';
      el.style.cssText = 'padding:10px 14px;margin:10px 0;background:rgba(248,81,73,0.15);border:1px solid var(--red);border-radius:6px;color:var(--red);font-size:12px;';
      document.querySelector('.modal-body').prepend(el);
    }
    el.textContent = msg;
    el.classList.remove('hidden');
  }

  function clearModalError() {
    const el = document.getElementById('modal-error');
    if (el) el.classList.add('hidden');
  }

  $btnApprove.addEventListener('click', async () => {
    clearModalError();

    const name = document.getElementById('manifest-name').value.trim();
    const desc = document.getElementById('manifest-desc').value.trim();
    const tags = document.getElementById('manifest-tags').value.trim() || null;

    if (!name) { showModalError('Manifest name is required.'); return; }
    if (!desc) { showModalError('Description is required.'); return; }
    if (State.staged.length === 0) { showModalError('No runs staged. Search and add runs first.'); return; }

    $btnApprove.disabled = true;
    $btnApprove.textContent = 'Creating...';

    try {
      // Build studies payload with full run metadata
      const studies = State.staged.map(s => ({
        accession: s.accession,
        title: s.title,
        runs: s.runs.map(r => typeof r === 'string' ? { accession: r } : r),
      }));
      const totalRuns = studies.reduce((sum, s) => sum + s.runs.length, 0);
      logCmd(`create_manifest("${name}", ${studies.length} studies, ${totalRuns} runs)`);

      const createResult = await API.createManifest(name, desc, studies, tags);

      if (createResult.error || createResult.detail) {
        const err = createResult.error || JSON.stringify(createResult.detail);
        showModalError(`Create failed: ${err}`);
        logError(`Create failed: ${err}`);
        return;
      }
      logInfo(`Manifest "${name}" created with ${createResult.total_runs} runs`);

      // Approve
      $btnApprove.textContent = 'Approving...';
      logCmd(`approve_manifest("${name}")`);
      const approveResult = await API.approveManifest(name);

      if (approveResult.error) {
        showModalError(`Approval failed: ${approveResult.error}`);
        logError(`Approval failed: ${approveResult.error}`);
        return;
      }

      logInfo(`Manifest "${name}" approved — ${approveResult.runs_to_import} runs ready to import`);
      State.approvedManifest = name;
      State.approvedRunCount = approveResult.runs_to_import;

      // Close modal, show approval banner
      $modalOverlay.classList.add('hidden');
      $approvalText.textContent = `Manifest "${name}" approved (${approveResult.runs_to_import} runs)`;
      $approvalBanner.classList.remove('hidden');

      // Clear staged
      State.clearStaged();
      updateStagedBanner();

    } catch (err) {
      showModalError(`Error: ${err.message}`);
      logError(`Error: ${err.message}`);
    } finally {
      $btnApprove.disabled = false;
      $btnApprove.textContent = 'Approve Manifest';
    }
  });

  // --- Load to HOX ---
  $btnLoadHox.addEventListener('click', async () => {
    if (!State.approvedManifest) return;
    const name = State.approvedManifest;

    logCmd(`import_to_hox("${name}")`);
    $btnLoadHox.disabled = true;
    $btnLoadHox.textContent = 'Importing...';

    try {
      const result = await API.importToHox(name);
      if (result.error) {
        logError(`Import error: ${result.error}`);
      } else {
        logInfo(`Import started: ${result.started} runs queued, ${result.failed} failed`);
        // Poll status
        pollImportStatus();
      }
    } catch (err) {
      logError(`Import failed: ${err.message}`);
    } finally {
      $btnLoadHox.disabled = false;
      $btnLoadHox.textContent = 'Load to HOX';
    }
  });

  async function pollImportStatus() {
    logCmd('get_import_status()');
    try {
      const status = await API.getImportStatus();
      logInfo(`Import status: ${JSON.stringify(status).substring(0, 200)}`);
    } catch (err) {
      logError(`Status check failed: ${err.message}`);
    }
  }

  // --- Dismiss approval banner ---
  $btnDismissApproval.addEventListener('click', () => {
    $approvalBanner.classList.add('hidden');
  });

  // --- View Manifests ---
  const $manifestsOverlay = document.getElementById('manifests-overlay');
  const $manifestsList = document.getElementById('manifests-list');
  const $manifestsClose = document.getElementById('manifests-close');

  $btnManifests.addEventListener('click', loadManifestsList);

  $manifestsClose.addEventListener('click', () => {
    $manifestsOverlay.classList.add('hidden');
  });

  $manifestsOverlay.addEventListener('click', (e) => {
    if (e.target === $manifestsOverlay) $manifestsOverlay.classList.add('hidden');
  });

  async function loadManifestsList() {
    $manifestsOverlay.classList.remove('hidden');
    $manifestsList.innerHTML = `<div class="loading-msg"><span class="spinner"></span> Loading manifests...</div>`;

    try {
      const data = await API.listManifests();
      const manifests = data.manifests || [];
      $manifestsList.innerHTML = Components.renderManifestsList(manifests);
    } catch (err) {
      $manifestsList.innerHTML = `<div style="color:var(--red);padding:16px">Failed to load manifests: ${err.message}</div>`;
    }
  }

  // Manifest list actions (delegation)
  $manifestsList.addEventListener('click', async (e) => {
    // Approve from list
    const btnApproveList = e.target.closest('.manifest-action-approve');
    if (btnApproveList) {
      const name = btnApproveList.dataset.name;
      btnApproveList.disabled = true;
      btnApproveList.textContent = 'Approving...';
      try {
        const result = await API.approveManifest(name);
        if (result.error) {
          logError(`Approval failed: ${result.error}`);
        } else {
          logInfo(`Manifest "${name}" approved`);
        }
      } catch (err) {
        logError(`Error: ${err.message}`);
      }
      loadManifestsList(); // refresh
      return;
    }

    // Load to HOX from list
    const btnLoadList = e.target.closest('.manifest-action-load');
    if (btnLoadList) {
      const name = btnLoadList.dataset.name;
      btnLoadList.disabled = true;
      btnLoadList.textContent = 'Importing...';
      logCmd(`import_to_hox("${name}")`);
      try {
        const result = await API.importToHox(name);
        if (result.error) {
          logError(`Import error: ${result.error}`);
        } else {
          logInfo(`Import started: ${result.started} runs queued, ${result.failed} failed`);
        }
      } catch (err) {
        logError(`Import failed: ${err.message}`);
      }
      loadManifestsList(); // refresh
      return;
    }
  });

  // --- Console helpers ---
  function logCmd(text) {
    State.log(text, '');
    renderConsole();
  }

  function logInfo(text) {
    State.log(text, 'info');
    renderConsole();
  }

  function logError(text) {
    State.log(text, 'error');
    renderConsole();
  }

  function renderConsole() {
    $console.innerHTML = Components.renderConsole(State.consoleHistory);
    const consoleEl = document.getElementById('console');
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }
})();
