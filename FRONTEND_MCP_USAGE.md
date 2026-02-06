# NCBI SRA Manifest Curator: Front-End → MCP Mapping

> Based on the Figma prototype at `city-user-56632970.figma.site`

## App Identity

- **Title:** NCBI SRA Manifest Curator
- **Subtitle:** "Query studies, select runs, and import datasets"
- **Core concept:** A terminal-inspired search UI connected to a manifest editor with an approval gate before loading to Hox.

---

## Screen 1: Interactive Query Console + Search Results

### Layout

The main screen has two sections stacked vertically:

**Top: Interactive Query Console** — a dark terminal-style panel showing command history. Commands appear as green `$` prompts (e.g., `$ search NCBI SRA: RNA-seq Cancer`) with `→ Searching...` feedback. This gives the feel of a CLI tool with a GUI wrapper.

**Below the console: Search Controls**
- **Database selector** — horizontal chip/pill group: `NCBI SRA` (active, blue fill), `NCBI GEO`, `ENA`, `DDBJ`. Only one selected at a time.
- **Search input** — text field with `$` prefix, placeholder shows the query (`RNA-seq human Cancer`).
- **Search button** — blue, right-aligned, with magnifying glass icon.
- **Tip text** below: "Use keywords, accession numbers, or concepts to query the database"

**Below controls: Search Results** — scrollable list of study cards.

### Study Result Cards

Each result is a bordered card containing:
- **Expand arrow** (chevron `>`) on the left — collapses/expands the run list
- **SRP accession** in blue (e.g., `SRP965629`) — acts as a link
- **Study title** in bold (e.g., "WGS analysis of Homo sapiens rna-seq human cancer - comprehensive study")
- **Summary text** truncated with ellipsis
- **Metadata row:** Organism (`Homo sapiens`), Platform (`Illumina HiSeq 2500`)
- **Stats row:** Date (`2022-06-18`), Runs count (`Runs: 6`), Total size (`Total: 5.64 GB`)
- **Selection badge** — green pill at bottom left showing `6 runs selected`
- **"+ Add Selected" button** — blue outline button at top right of the card. This is the action that stages selected runs into the manifest.

### MCP tool mapping

| UI Element | MCP Tool | Parameters |
|------------|----------|------------|
| Database chips + search input + Search button | `search_studies` | `query` = input text, `database` = selected chip (`sra`/`gds`), `organism` inferred |
| Study card metadata (title, abstract, organism, platform) | `get_study_info` | `accession` = SRP number from card |
| Expand arrow → run list | `list_runs` | `study_accession` = SRP number |
| Individual run metadata (size, spots, bases) | `get_file_urls` | `accession` = SRR number (for file size/URL data) |

---

## Screen 2: Run Selection (Expanded Study)

### Layout

When a study card is expanded, the runs appear as a scrollable list of selectable cards beneath it.

**Each run card contains:**
- **Checkbox** — blue filled square with checkmark when selected
- **SRR accession** in bold (e.g., `SRR15416245`)
- **Metadata row:** Size (`1.55 GB`), Spots (`51,047,087`), Bases (`5.16G`), Avg read length (`101bp`)

**Top right:** "Deselect All" link (partially visible)

### Interaction flow

1. User expands a study → `list_runs` is called → run cards render
2. Runs appear pre-selected (all checkboxes checked) or user toggles individually
3. "Deselect All" clears all checkboxes for that study
4. User clicks **"+ Add Selected"** on the parent study card → selected SRR accessions are staged for the manifest

### MCP tool mapping

| UI Action | MCP Tool | Notes |
|-----------|----------|-------|
| Expand study | `list_runs` | Returns run accessions + metadata |
| Run card data (size, spots, bases, avg bp) | `get_file_urls` or embedded in `list_runs` response | Per-run stats displayed inline |
| "+ Add Selected" button | Client-side staging | No MCP call yet — accumulates selections locally until manifest is created |

---

## Screen 3: Manifest Editor (Modal Panel)

### Layout

A modal/drawer panel titled **"Manifest Editor"** with subtitle "Review and finalize your dataset manifest." Has an `X` close button.

**Manifest Name** — editable text input, defaults to `untitled-manifest`.

**Summary stats bar:** `Studies: 2`, `Total Runs: 16`, `Total Size: ~15.75 GB` — all in blue text.

**Study list** — numbered cards (1, 2, ...) each containing:
- **Number badge** (circled, e.g., `1`) with expand/collapse chevron
- **SRP accession** in blue (e.g., `SRP938059`)
- **Study title** in bold
- **Metadata:** Organism, Platform, run selection count (e.g., `11 of 11 runs`)
- **Delete icon** (trash can) — top right, removes this study from the manifest
- **"Selected Runs (N)" sub-section** — expandable list of individual SRR cards with:
  - Checkbox (checked, blue)
  - SRR accession
  - Size, Spots, Bases

**Bottom action bar** (sticky):
- **"Approve Manifest"** — green button with checkmark icon, primary action
- **"Export Manifest"** — outline button with download icon
- **"Settings"** — outline button with gear icon

### Interaction flow

1. User reviews studies and runs in the manifest
2. Can **remove entire studies** via the trash icon
3. Can **deselect individual runs** via checkboxes within each study
4. Can **rename the manifest** via the name input
5. Clicks **"Approve Manifest"** → triggers the approval

### MCP tool mapping

| UI Action | MCP Tool | Parameters |
|-----------|----------|------------|
| Opening the Manifest Editor (initial render) | `create_manifest` | `name` = input value, `accessions` = all staged SRR accessions, `description` = (from a field not shown or auto-generated) |
| Viewing manifest contents | `list_manifests` | `name` = manifest name |
| Removing a study / deselecting runs | Client-side edit | Modifies local state before final creation, or calls `create_manifest` again |
| "Approve Manifest" button | `approve_manifest` | `name` = manifest name |
| "Export Manifest" button | `list_manifests` | Fetches full JSON for download/export |

### Key design observation

The Manifest Editor aggregates runs **by study** (numbered 1, 2, etc.) rather than as a flat list. This means the front-end groups SRR runs back under their parent SRP, which requires either:
- Tracking the study→run relationship client-side during search/select
- Or deriving it from the manifest JSON where accessions contain both the parent study and extracted runs

---

## Screen 4: Manifest Approved (Confirmation)

### Layout

A green-bordered success banner containing:
- **Green checkmark icon** (circle with check)
- **"Manifest Approved"** heading in bold
- **Summary text:** "Ready to load 16 runs from 2 studies (~17.29 GB total)."
- **"Load to HOX"** — blue primary button with upload icon
- **"Close"** — outline/secondary button

### Interaction flow

1. After approval, this confirmation appears immediately
2. User can **Load to HOX** right away or **Close** and come back later
3. "Load to HOX" triggers the import pipeline

### MCP tool mapping

| UI Action | MCP Tool | Parameters |
|-----------|----------|------------|
| "Load to HOX" button | `import_to_hox` | `manifest_name` = approved manifest name |
| Post-import monitoring | `get_import_status` | Polled for job progress |

---

## Complete User Flow → MCP Call Sequence

```
1. SEARCH
   User types "RNA-seq human Cancer", selects NCBI SRA, clicks Search
   → search_studies(query="RNA-seq human Cancer", database="sra")

2. EXPLORE
   Results render. User clicks expand on SRP965629
   → list_runs(study_accession="SRP965629")
   Run cards appear with checkboxes, sizes, spots, bases

3. SELECT
   User checks desired runs, clicks "+ Add Selected"
   → (client-side: staged accessions accumulate)
   User repeats for additional studies

4. CURATE
   User opens Manifest Editor, names it, reviews grouped studies/runs
   → create_manifest(name="my-manifest", accessions="SRR15416245,SRR11346220,...")

5. APPROVE
   User clicks "Approve Manifest"
   → approve_manifest(name="my-manifest")

6. LOAD
   Confirmation banner appears. User clicks "Load to HOX"
   → import_to_hox(manifest_name="my-manifest")
   → get_import_status() (polled)
```

---

## Front-End Design Patterns

### Terminal aesthetic
The query console uses a dark background with green monospace text and `$` prompts, giving researchers a familiar CLI feel while wrapping it in a GUI. Command history scrolls upward as new searches are issued.

### Progressive disclosure
- Studies start collapsed → expand to show runs
- Runs show summary stats → can drill into file URLs
- Manifest Editor is a modal that opens only after selections are made

### Inline selection with batch action
Runs are selected via checkboxes within expanded study cards. The **"+ Add Selected"** button on each study card batches the selected runs. The green `N runs selected` badge provides immediate feedback.

### Study-grouped manifest review
The Manifest Editor groups runs under their parent study with numbered cards, trash icons for removal, and nested checkbox lists. This is a curation UX — the researcher can trim at both the study level (delete entire study) and the run level (deselect individual runs).

### Two-step commit: Approve then Load
The green "Approve Manifest" button is the human-in-the-loop gate. Only after approval does the blue "Load to HOX" button appear in the confirmation banner. This prevents accidental imports of uncurated data.

---

## MCP Gaps / Front-End Needs Not Covered by Current MCP

| Front-End Feature | Current MCP Support | Gap |
|-------------------|--------------------|----|
| Database selector (NCBI SRA, GEO, ENA, DDBJ) | `search_studies` supports `gds` and `sra` | ENA and DDBJ not yet supported as database options |
| Avg read length per run | Not returned by `list_runs` or `get_file_urls` | Front-end shows `Avg: 101bp` — needs to be computed or added to API |
| Total size per study | Not aggregated by MCP | Front-end shows `Total: 5.64 GB` — must be summed client-side from run sizes |
| Export Manifest | `list_manifests(name)` returns JSON | Works, but no dedicated export format (ISA-Tab, CSV) |
| Settings button | No MCP equivalent | Likely client-side preferences (default organism, database, etc.) |
| Manifest description field | `create_manifest` accepts `description` | Not visible in the prototype UI — may be in Settings or a field not shown |
| Tags | `create_manifest` accepts `tags` | No tag editor visible in prototype — may be in Settings or a future addition |
