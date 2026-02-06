/**
 * Client-side state for the Manifest Curator.
 */
const State = {
  // Current database selection
  database: 'sra',

  // Search results from last query
  searchResults: [],

  // Map of study accession -> runs array (loaded on expand)
  studyRuns: {},

  // Map of study accession -> Set of selected run accessions
  selectedRuns: {},

  // Staged studies for manifest: [{ accession, title, runs: [{ accession, spots, bases, strategy, platform, sample }...] }]
  staged: [],

  // Console log history
  consoleHistory: [],

  // Last approved manifest name
  approvedManifest: null,

  // UI flags
  loading: false,
  expandedStudy: null,

  /** Stage selected runs for a study */
  stageStudy(accession, title, runs) {
    // Remove if already staged (replace)
    this.staged = this.staged.filter(s => s.accession !== accession);
    if (runs.length > 0) {
      this.staged.push({ accession, title, runs: [...runs] });
    }
  },

  /** Remove a staged study */
  unstageStudy(accession) {
    this.staged = this.staged.filter(s => s.accession !== accession);
  },

  /** Get total staged run count */
  get stagedRunCount() {
    return this.staged.reduce((sum, s) => sum + s.runs.length, 0);
  },

  /** Get all staged run accessions as CSV */
  get stagedAccessionsCsv() {
    return this.staged.flatMap(s => s.runs.map(r => typeof r === 'string' ? r : r.accession)).join(',');
  },

  /** Clear all staged */
  clearStaged() {
    this.staged = [];
    this.selectedRuns = {};
  },

  /** Add a console line */
  log(text, type = '') {
    this.consoleHistory.push({ text, type, time: new Date() });
    // Keep max 100 lines
    if (this.consoleHistory.length > 100) {
      this.consoleHistory.shift();
    }
  },
};
