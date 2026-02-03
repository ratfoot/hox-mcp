# Hox Bio MCP Server - Backlog

## Target User Profile: Computational Psychiatry Lab (e.g., Grosenick Lab)

**Context:** ML researchers working on psychiatric disorders who need to:
- Find public datasets (fMRI, RNA-seq, scRNA-seq) by disease/tissue
- Curate collections for model training
- Load approved data into Hox warehouse

---

## V2+ Feature Ideas

### Disease-Centric Search
```python
@mcp.tool()
def search_datasets_by_condition(
    condition: str,      # "major depressive disorder", "PTSD"
    tissue: str = None,  # "brain", "prefrontal cortex"
    assay: str = None,   # "RNA-seq", "scRNA-seq", "ATAC-seq"
    min_samples: int = 10
) -> str:
    """Search GEO/SRA for datasets matching disease criteria using MeSH terms"""
```

### GEO DataSets Integration
- Current gap: ffq focuses on raw reads, not processed expression matrices
- Need: Search GEO Series (GSE) with filters for study type, organism, platform
- Could use Entrez esearch/efetch APIs

### Tissue Ontology Filtering
- Integrate UBERON ontology for tissue terms
- Brain-specific: map common terms → ontology IDs
- Example: "prefrontal cortex" → UBERON:0000451

### Publication-to-Data Linking
```python
@mcp.tool()
def datasets_from_publication(doi: str) -> str:
    """Given a paper DOI, find all associated GEO/SRA accessions via ENA/GEO APIs"""
```

### Brain Atlas Integration
- Allen Brain Atlas API for regional expression
- BrainSpan for developmental data
- GTEx brain tissues

### Multi-Modal Manifest Support
- Link imaging ↔ omics ↔ clinical within same manifest
- Support for subject-level linking across modalities
- Batch effect documentation

### Advanced Metadata Search
- Clinical phenotype filtering (treatment response, severity scores)
- Demographic filters (age range, sex)
- Quality metrics (RIN scores, read depth)

### Meta-Analysis Support
```python
@mcp.tool()
def create_meta_analysis_manifest(
    studies: list[str],  # List of GSE/SRP accessions
    harmonization_notes: str = None
) -> str:
    """Bundle multiple studies for cross-study analysis"""
```

---

## Data Sources to Integrate

| Source | Type | API |
|--------|------|-----|
| GEO | Expression matrices | Entrez E-utilities |
| SRA | Raw sequences | ENA API (via ffq) |
| Allen Brain | Brain expression | brain-map.org API |
| GTEx | Tissue expression | GTEx Portal API |
| ENCODE | Epigenomics | ENCODE REST API |
| Single Cell Portal | scRNA-seq | Broad API |

---

## Workflow Improvements

### Current (V1)
```
search_genes → fetch_metadata → create_manifest → approve → import
```

### Future (V2+)
```
search_by_disease_question
  → filter_by_tissue_assay
  → preview_sample_metadata
  → create_curated_manifest (with QC notes)
  → collaborative_review
  → staged_import (test subset first)
  → harmonization_pipeline
```

---

## Technical Debt

- [ ] Add caching for API calls (gget/ffq can be slow)
- [ ] Async support for bulk metadata fetches
- [ ] Better error messages with suggested fixes
- [ ] Manifest versioning
- [ ] Export manifests to standard formats (ISA-Tab, MAGE-TAB)
