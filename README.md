# Hox Bio MCP Server

**V1: Discover → Curate → Approve → Load**

MCP server for ML bio researchers to find public sequencing data and load it into Hox.

## Tools (7 total)

| Tool | Purpose |
|------|---------|
| `get_study_info` | Get metadata for a GEO/SRA study |
| `list_runs` | List all runs in a study |
| `create_manifest` | Bundle accessions for approval |
| `list_manifests` | View pending/approved manifests |
| `approve_manifest` | Mark manifest ready for import |
| `import_to_hox` | Load approved data into warehouse |
| `get_import_status` | Check import job progress |

## Workflow

```
1. DISCOVER
   get_study_info("GSE123456")     # Found accession in paper/GEO
   list_runs("GSE123456")          # See all samples

2. CURATE
   create_manifest(
     name="mdd_rnaseq",
     description="DLPFC RNA-seq from MDD patients",
     accessions="SRR123,SRR124,SRR125",
     tags="disease=MDD,tissue=DLPFC"
   )

3. APPROVE
   list_manifests("mdd_rnaseq")    # Review details
   approve_manifest("mdd_rnaseq")  # Mark approved

4. LOAD
   import_to_hox("mdd_rnaseq")     # Import to warehouse
   get_import_status()             # Monitor progress
```

## Quick Start

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
./start.sh
```

## Supported Accessions

- **GEO:** GSE (series), GSM (samples)
- **SRA:** SRP (projects), SRR/ERR/DRR (runs)
- **BioProject:** PRJNA

## Requirements

- Python 3.10+
- `hox` CLI (for import features)
- Network access to NCBI/ENA APIs
