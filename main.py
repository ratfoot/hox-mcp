"""
Hox Bio MCP Server - V1

Focused workflow: Discover → Curate → Approve → Load

Tools:
1. search_studies     - Search NCBI GEO/SRA for studies by keyword
2. get_study_info     - Get metadata for a GEO/SRA study (uses gget)
3. list_runs          - List all sequencing runs in a study (uses gget)
4. get_file_urls      - Get download URLs for sequencing data (uses ffq)
5. create_manifest    - Bundle accessions for approval
6. list_manifests     - View pending/approved manifests
7. approve_manifest   - Mark manifest ready for import
8. import_to_hox      - Load approved manifest into warehouse
9. get_import_status  - Check import job progress

Uses:
- NCBI Entrez: For searching GEO/SRA databases
- gget: For metadata retrieval (stable API, rich annotations)
- ffq: For locating binary data files (FASTQ URLs, file sizes)
"""
import json
import subprocess
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP
import gget

# NCBI E-utilities base URL
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

mcp = FastMCP("hox-bio")

MANIFEST_DIR = Path.home() / ".hox" / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DISCOVERY - Search and get study/sample metadata
# ============================================================================

@mcp.tool()
def search_studies(
    query: str,
    database: str = "gds",
    organism: str = "Homo sapiens",
    limit: int = 20
) -> str:
    """
    Search NCBI GEO/SRA for studies matching keywords.

    Search for studies by tissue, disease, cell type, or any keyword.
    Returns study accessions that can be used with get_study_info() and list_runs().

    Args:
        query: Search terms (e.g., "brain tissue", "RNA-seq depression", "DLPFC schizophrenia")
        database: NCBI database - "gds" for GEO DataSets, "sra" for SRA (default: gds)
        organism: Filter by organism (default: "Homo sapiens", use "" for all)
        limit: Maximum results to return (default: 20, max: 100)

    Returns:
        JSON with matching studies including accessions, titles, and summaries

    Examples:
        search_studies("brain tissue RNA-seq")
        search_studies("prefrontal cortex depression", organism="Homo sapiens")
        search_studies("single cell brain", database="sra", limit=50)
    """
    try:
        # Build search query
        search_terms = [query]
        if organism:
            search_terms.append(f'"{organism}"[Organism]')

        full_query = " AND ".join(search_terms)

        # Search NCBI using E-utilities
        search_url = f"{NCBI_BASE}/esearch.fcgi"
        search_params = {
            "db": database,
            "term": full_query,
            "retmax": min(limit, 100),
            "retmode": "json",
            "usehistory": "y"
        }

        resp = requests.get(search_url, params=search_params, timeout=30)
        resp.raise_for_status()
        search_data = resp.json()

        result = search_data.get("esearchresult", {})
        id_list = result.get("idlist", [])
        total_count = int(result.get("count", 0))

        if not id_list:
            return json.dumps({
                "query": query,
                "database": database,
                "organism": organism,
                "total_found": 0,
                "studies": [],
                "message": "No studies found. Try broader search terms."
            }, indent=2)

        # Fetch summaries for the IDs
        summary_url = f"{NCBI_BASE}/esummary.fcgi"
        summary_params = {
            "db": database,
            "id": ",".join(id_list),
            "retmode": "json"
        }

        resp = requests.get(summary_url, params=summary_params, timeout=30)
        resp.raise_for_status()
        summary_data = resp.json()

        studies = []
        doc_sums = summary_data.get("result", {})

        for uid in id_list:
            if uid in doc_sums:
                study = _parse_entrez_summary(doc_sums[uid], database)
                if study:
                    studies.append(study)

        return json.dumps({
            "query": query,
            "database": database,
            "organism": organism,
            "total_found": total_count,
            "returned": len(studies),
            "studies": studies,
            "next_step": "Use get_study_info(accession) or list_runs(accession) for details"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "query": query,
            "hint": "Try simpler search terms or check NCBI connectivity"
        })


def _parse_entrez_summary(item: dict, database: str) -> dict:
    """Parse Entrez JSON summary into clean study record."""
    if database == "gds":
        # GEO DataSets format (JSON keys are lowercase)
        accession = item.get("accession", "")
        # Convert GDS to GSE if needed
        if accession.startswith("GDS"):
            gse = item.get("gse", "")
            if gse:
                accession = f"GSE{gse}"

        summary = item.get("summary", "")
        return {
            "accession": accession,
            "title": item.get("title", ""),
            "summary": (summary[:300] + "...") if len(summary) > 300 else summary,
            "organism": item.get("taxon", ""),
            "type": item.get("gdstype", ""),
            "platform": item.get("gpl", ""),
            "samples": item.get("n_samples", 0),
            "date": item.get("pdat", "")
        }
    elif database == "sra":
        # SRA format - extract from expxml if present
        exp_xml = item.get("expxml", "")
        runs_xml = item.get("runs", "")

        # Parse key fields from XML strings if presentg
        accession = _extract_xml_attr(exp_xml, "Experiment", "acc") or item.get("accession", "")
        study_acc = _extract_xml_attr(exp_xml, "Study", "acc") or ""
        title = _extract_xml_text(exp_xml, "Title") or item.get("exptitle", "")
        organism = _extract_xml_attr(exp_xml, "Organism", "ScientificName") or item.get("organism", "")
        platform = _extract_xml_attr(exp_xml, "Platform", "instrument_model") or ""
        strategy = _extract_xml_attr(exp_xml, "Library_descriptor", "LIBRARY_STRATEGY") or ""

        # Count runs
        run_count = runs_xml.count("<Run ") if runs_xml else 1

        return {
            "accession": study_acc or accession,
            "experiment": accession,
            "title": title,
            "organism": organism,
            "platform": platform,
            "strategy": strategy,
            "runs": run_count,
            "bases": item.get("total_bases", 0),
            "date": item.get("createdate", "")
        }
    return {}


def _extract_xml_attr(xml_str: str, tag: str, attr: str) -> str:
    """Extract attribute from XML string."""
    try:
        if not xml_str:
            return ""
        # Wrap in root for parsing
        root = ET.fromstring(f"<root>{xml_str}</root>")
        elem = root.find(f".//{tag}")
        if elem is not None:
            return elem.get(attr, "")
    except:
        pass
    return ""


def _extract_xml_text(xml_str: str, tag: str) -> str:
    """Extract text content from XML string."""
    try:
        if not xml_str:
            return ""
        root = ET.fromstring(f"<root>{xml_str}</root>")
        elem = root.find(f".//{tag}")
        if elem is not None and elem.text:
            return elem.text
    except:
        pass
    return ""


def _fetch_sra_metadata(accession: str) -> dict:
    """Fetch metadata for SRA/GEO accessions using ffq."""
    from ffq import ffq

    acc_upper = accession.upper()

    # Route to appropriate ffq function based on accession prefix
    if acc_upper.startswith(('SRR', 'ERR', 'DRR')):
        return ffq.ffq_run(accession)
    elif acc_upper.startswith('GSE'):
        return ffq.ffq_gse(accession)
    elif acc_upper.startswith('GSM'):
        return ffq.ffq_gsm(accession)
    elif acc_upper.startswith(('SRP', 'ERP', 'DRP')):
        return ffq.ffq_study(accession)
    elif acc_upper.startswith(('SRS', 'ERS', 'DRS')):
        return ffq.ffq_sample(accession)
    elif acc_upper.startswith(('SRX', 'ERX', 'DRX')):
        return ffq.ffq_experiment(accession)
    elif acc_upper.startswith(('PRJNA', 'PRJEB', 'PRJDB')):
        return ffq.ffq_bioproject(accession)
    else:
        raise ValueError(f"Unknown accession type: {accession}")


def _is_sra_accession(accession: str) -> bool:
    """Check if accession is an SRA/GEO type."""
    prefixes = ('SRR', 'SRP', 'SRS', 'SRX', 'ERR', 'ERP', 'ERS', 'ERX',
                'DRR', 'DRP', 'DRS', 'DRX', 'GSE', 'GSM', 'PRJNA', 'PRJEB', 'PRJDB')
    return accession.upper().startswith(prefixes)


def _extract_ffq_summary(accession: str, data) -> dict:
    """Extract clean summary from ffq response."""
    summary = {
        "accession": accession,
        "runs": [],
        "run_count": 0
    }

    def walk(obj, parent_acc=None):
        if isinstance(obj, dict):
            # Capture study-level info
            for key in ["title", "abstract", "organism", "description"]:
                if key in obj and obj[key] and key not in summary:
                    summary[key] = obj[key]

            # Capture run info
            acc = obj.get("accession", "")
            if acc.startswith(("SRR", "ERR", "DRR")):
                summary["runs"].append({
                    "accession": acc,
                    "experiment": obj.get("experiment", ""),
                    "sample_title": obj.get("sample_title", obj.get("title", "")),
                    "library_strategy": obj.get("library_strategy", ""),
                    "library_source": obj.get("library_source", ""),
                    "platform": obj.get("platform", ""),
                    "spots": obj.get("spots", ""),
                    "bases": obj.get("bases", "")
                })

            for v in obj.values():
                walk(v, acc or parent_acc)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, parent_acc)

    walk(data)
    summary["run_count"] = len(summary["runs"])

    # For single runs, simplify
    if accession.startswith(("SRR", "ERR", "DRR")) and summary["runs"]:
        summary["run_info"] = summary["runs"][0]
        del summary["runs"]
        del summary["run_count"]

    return summary


@mcp.tool()
def get_study_info(accession: str) -> str:
    """
    Get metadata for a study or sample from GEO/SRA/ENA.

    Args:
        accession: Study or sample accession (GSE, SRP, PRJNA, GSM, SRR, etc.)

    Returns:
        JSON with study title, abstract, organism, samples, and run counts

    Examples:
        get_study_info("GSE123456")  # GEO series
        get_study_info("SRP123456")  # SRA project
        get_study_info("SRR123456")  # Single run
    """
    try:
        if _is_sra_accession(accession):
            # Use ffq for SRA/GEO metadata
            data = _fetch_sra_metadata(accession)
        else:
            # Use gget.info() for Ensembl IDs
            df = gget.info(accession)
            if df is None or (hasattr(df, 'empty') and df.empty):
                return json.dumps({"error": "No data found", "accession": accession})
            if hasattr(df, 'to_dict'):
                data = df.to_dict(orient='records')
                if len(data) == 1:
                    data = data[0]
            else:
                data = df

        return json.dumps({"accession": accession, "metadata": data}, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "accession": accession})


def _extract_metadata_summary(accession: str, df) -> dict:
    """Extract clean summary from gget response."""
    summary = {
        "accession": accession,
        "runs": [],
        "run_count": 0
    }

    # Convert DataFrame to list of dicts
    if hasattr(df, 'to_dict'):
        records = df.to_dict(orient='records')
    elif isinstance(df, dict):
        records = [df]
    elif isinstance(df, list):
        records = df
    else:
        return summary

    for record in records:
        if not isinstance(record, dict):
            continue

        # Capture study-level info
        for key in ["title", "abstract", "organism", "description", "study_title"]:
            if key in record and record[key] and key not in summary:
                summary[key] = record[key]

        # Capture run info
        acc = record.get("accession", record.get("run_accession", ""))
        if acc.startswith(("SRR", "ERR", "DRR")):
            summary["runs"].append({
                "accession": acc,
                "experiment": record.get("experiment", record.get("experiment_accession", "")),
                "sample_title": record.get("sample_title", record.get("title", "")),
                "library_strategy": record.get("library_strategy", ""),
                "library_source": record.get("library_source", ""),
                "platform": record.get("platform", record.get("instrument_platform", "")),
                "spots": record.get("spots", record.get("total_spots", "")),
                "bases": record.get("bases", record.get("total_bases", ""))
            })

    summary["run_count"] = len(summary["runs"])

    # For single runs, simplify
    if accession.startswith(("SRR", "ERR", "DRR")) and summary["runs"]:
        summary["run_info"] = summary["runs"][0]
        del summary["runs"]
        del summary["run_count"]

    return summary


@mcp.tool()
def list_runs(study_accession: str) -> str:
    """
    List all sequencing runs in a study with key metadata.

    Args:
        study_accession: Study accession (GSE, SRP, PRJNA, ERP)

    Returns:
        JSON with run accessions and metadata (library type, platform, etc.)

    Example:
        list_runs("SRP123456")
    """
    try:
        if _is_sra_accession(study_accession):
            # Use ffq for SRA/GEO metadata
            data = _fetch_sra_metadata(study_accession)
            runs = []

            def extract_runs(obj):
                if isinstance(obj, dict):
                    acc = obj.get("accession", "")
                    if acc.startswith(("SRR", "ERR", "DRR")):
                        runs.append({
                            "accession": acc,
                            "sample": str(obj.get("sample_title", obj.get("title", "")))[:60],
                            "strategy": obj.get("library_strategy", ""),
                            "source": obj.get("library_source", ""),
                            "platform": obj.get("platform", ""),
                        })
                    for v in obj.values():
                        extract_runs(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_runs(item)

            extract_runs(data)
        else:
            df = gget.info(study_accession)
            if df is None or (hasattr(df, 'empty') and df.empty):
                return json.dumps({"error": "No data found", "study": study_accession})

            if hasattr(df, 'to_dict'):
                records = df.to_dict(orient='records')
            else:
                records = [df] if isinstance(df, dict) else df

            runs = []
            for record in records if isinstance(records, list) else [records]:
                if isinstance(record, dict):
                    acc = record.get('accession', record.get('run_accession', ''))
                    if acc.startswith(('SRR', 'ERR', 'DRR')):
                        runs.append({
                            "accession": acc,
                            "sample": str(record.get('sample_title', record.get('title', '')))[:60],
                            "strategy": record.get('library_strategy', ''),
                            "source": record.get('library_source', ''),
                            "platform": record.get('platform', record.get('instrument_platform', '')),
                        })

        return json.dumps({
            "study": study_accession,
            "total_runs": len(runs),
            "runs": runs
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "study": study_accession})


@mcp.tool()
def get_file_urls(accession: str) -> str:
    """
    Get download URLs for sequencing data files (FASTQ, BAM, etc.).

    Uses ffq to locate the actual binary files associated with an accession.
    Use this when you need to download or reference the raw data files.

    Args:
        accession: Run or sample accession (SRR, ERR, DRR, GSM, etc.)

    Returns:
        JSON with file URLs, sizes, and checksums

    Examples:
        get_file_urls("SRR9990627")  # Get FASTQ URLs for a run
        get_file_urls("GSM4037981")  # Get files for a GEO sample
    """
    from ffq.ffq import ffq_ids

    try:
        # ffq_ids returns a list of dicts with file info
        data = ffq_ids([accession])

        if not data:
            return json.dumps({"error": "No files found", "accession": accession})

        # Extract file URLs from the response
        files = []
        for item in data:
            if isinstance(item, dict):
                # Handle different ffq response structures
                if 'files' in item:
                    for f in item.get('files', {}).values():
                        if isinstance(f, list):
                            files.extend(f)
                        elif isinstance(f, dict):
                            files.append(f)
                elif 'url' in item:
                    files.append(item)

        return json.dumps({
            "accession": accession,
            "file_count": len(files),
            "files": files
        }, indent=2, default=str)
    except ImportError:
        return json.dumps({
            "error": "ffq not properly installed. Run: pip install ffq",
            "accession": accession
        })
    except Exception as e:
        return json.dumps({"error": str(e), "accession": accession})


# ============================================================================
# MANIFEST - Curate datasets for approval
# ============================================================================

@mcp.tool()
def create_manifest(
    name: str,
    description: str,
    accessions: str,
    tags: Optional[str] = None
) -> str:
    """
    Create a manifest of datasets for approval before loading into Hox.

    The manifest captures metadata for each accession and saves it for review.
    Use approve_manifest() after review, then import_to_hox() to load.

    Args:
        name: Short name for this manifest (becomes filename)
        description: What this data is for (e.g., "MDD RNA-seq for treatment response model")
        accessions: Comma-separated accessions (SRR, GSM, GSE, SRP - will extract runs)
        tags: Optional key=value pairs for Hox tags (e.g., "disease=MDD,tissue=brain")

    Returns:
        JSON with manifest summary and file path

    Example:
        create_manifest(
            name="mdd_rnaseq_v1",
            description="Prefrontal cortex RNA-seq from MDD patients for biotype classification",
            accessions="SRR123,SRR124,SRR125",
            tags="disease=MDD,tissue=DLPFC,assay=RNA-seq"
        )
    """
    manifest = {
        "name": name,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "tags": _parse_tags(tags),
        "accessions": [],
        "total_runs": 0
    }

    acc_list = [a.strip() for a in accessions.split(",") if a.strip()]

    for acc in acc_list:
        entry = {"accession": acc, "status": "ok", "runs": []}
        try:
            # Use ffq for SRA/GEO, gget for Ensembl
            if _is_sra_accession(acc):
                data = _fetch_sra_metadata(acc)
                entry["metadata"] = _extract_ffq_summary(acc, data)
            else:
                df = gget.info(acc)
                entry["metadata"] = _extract_metadata_summary(acc, df)

            # Count runs
            if "runs" in entry["metadata"]:
                entry["runs"] = [r["accession"] for r in entry["metadata"]["runs"]]
            elif acc.startswith(("SRR", "ERR", "DRR")):
                entry["runs"] = [acc]

        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)

        manifest["accessions"].append(entry)
        manifest["total_runs"] += len(entry["runs"])

    # Save
    path = MANIFEST_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return json.dumps({
        "created": name,
        "path": str(path),
        "accession_count": len(manifest["accessions"]),
        "total_runs": manifest["total_runs"],
        "status": "pending",
        "next_step": f"Review with list_manifests(), then approve_manifest('{name}')"
    }, indent=2)


def _parse_tags(tags: Optional[str]) -> dict:
    """Parse 'key=val,key2=val2' into dict."""
    if not tags:
        return {}
    result = {}
    for pair in tags.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            result[k.strip()] = v.strip()
    return result


@mcp.tool()
def list_manifests(name: Optional[str] = None) -> str:
    """
    List manifests or get details of a specific manifest.

    Args:
        name: Optional manifest name to get full details. If omitted, lists all.

    Returns:
        JSON with manifest(s) summary or full details

    Examples:
        list_manifests()              # List all
        list_manifests("mdd_rnaseq")  # Get details for one
    """
    if name:
        path = MANIFEST_DIR / f"{name}.json"
        if not path.exists():
            return json.dumps({"error": f"Manifest '{name}' not found"})
        with open(path) as f:
            return f.read()

    manifests = []
    for path in sorted(MANIFEST_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
                manifests.append({
                    "name": data.get("name"),
                    "status": data.get("status"),
                    "description": (data.get("description", "")[:80] + "...") if len(data.get("description", "")) > 80 else data.get("description", ""),
                    "runs": data.get("total_runs", 0),
                    "created": data.get("created_at", "")[:10],
                    "tags": data.get("tags", {})
                })
        except:
            pass

    return json.dumps({"manifests": manifests, "count": len(manifests)}, indent=2)


@mcp.tool()
def approve_manifest(name: str) -> str:
    """
    Mark a manifest as approved for import into Hox.

    Review the manifest first with list_manifests(name), then approve.
    After approval, use import_to_hox(name) to load the data.

    Args:
        name: Manifest name to approve

    Returns:
        JSON confirmation with next steps

    Example:
        approve_manifest("mdd_rnaseq_v1")
    """
    path = MANIFEST_DIR / f"{name}.json"
    if not path.exists():
        return json.dumps({"error": f"Manifest '{name}' not found"})

    with open(path) as f:
        manifest = json.load(f)

    if manifest.get("status") == "approved":
        return json.dumps({"message": "Already approved", "name": name})

    manifest["status"] = "approved"
    manifest["approved_at"] = datetime.now().isoformat()

    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return json.dumps({
        "approved": name,
        "runs_to_import": manifest.get("total_runs", 0),
        "next_step": f"import_to_hox('{name}')"
    }, indent=2)


# ============================================================================
# HOX IMPORT - Load data into warehouse
# ============================================================================

def _run_hox(args: list, profile: Optional[str] = None) -> dict:
    """Run hox CLI command."""
    cmd = ["hox"]
    if profile:
        cmd.append(f"--profile={profile}")
    cmd.extend(args)
    cmd.append("--json")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            try:
                return {"ok": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                return {"ok": True, "data": result.stdout.strip()}
        return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
    except FileNotFoundError:
        return {"ok": False, "error": "hox CLI not found - install from https://hox.io"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Command timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def import_to_hox(
    manifest_name: str,
    set_name: Optional[str] = None,
    profile: Optional[str] = None
) -> str:
    """
    Import all runs from an approved manifest into Hox.

    Creates a Set to group the reads and imports each run from SRA.
    The manifest must be approved first with approve_manifest().

    Args:
        manifest_name: Name of the approved manifest
        set_name: Optional custom name for the Hox Set (defaults to manifest name)
        profile: Optional Hox CLI profile name

    Returns:
        JSON with import results for each run

    Example:
        import_to_hox("mdd_rnaseq_v1")
    """
    path = MANIFEST_DIR / f"{manifest_name}.json"
    if not path.exists():
        return json.dumps({"error": f"Manifest '{manifest_name}' not found"})

    with open(path) as f:
        manifest = json.load(f)

    if manifest.get("status") != "approved":
        return json.dumps({
            "error": f"Manifest must be approved first. Current status: {manifest.get('status')}",
            "fix": f"approve_manifest('{manifest_name}')"
        })

    results = {
        "manifest": manifest_name,
        "set_name": set_name or manifest_name,
        "imports": [],
        "success": 0,
        "failed": 0
    }

    # Create a Set to group the reads
    set_result = _run_hox(["create", "set", f"--name={results['set_name']}"], profile)
    if set_result["ok"]:
        results["set_id"] = set_result["data"].get("id") if isinstance(set_result["data"], dict) else None
    else:
        results["set_error"] = set_result["error"]

    # Collect all runs
    all_runs = []
    for entry in manifest.get("accessions", []):
        all_runs.extend(entry.get("runs", []))

    # Import each run
    for run_acc in all_runs:
        args = ["import", "reads", f"--from-accession={run_acc}"]
        if results.get("set_id"):
            args.append(f"--set={results['set_id']}")

        import_result = _run_hox(args, profile)

        if import_result["ok"]:
            results["success"] += 1
            results["imports"].append({"run": run_acc, "status": "started"})
        else:
            results["failed"] += 1
            results["imports"].append({"run": run_acc, "status": "failed", "error": import_result["error"]})

    # Update manifest
    manifest["status"] = "importing"
    manifest["import_started"] = datetime.now().isoformat()
    manifest["import_results"] = results

    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return json.dumps({
        "started": results["success"],
        "failed": results["failed"],
        "set_id": results.get("set_id"),
        "next_step": "get_import_status() to monitor progress"
    }, indent=2)


@mcp.tool()
def get_import_status(profile: Optional[str] = None) -> str:
    """
    Check status of Hox import jobs.

    Shows running and recent jobs to monitor import progress.

    Args:
        profile: Optional Hox CLI profile name

    Returns:
        JSON with job statuses

    Example:
        get_import_status()
    """
    result = _run_hox(["get", "jobs"], profile)

    if not result["ok"]:
        return json.dumps({"error": result["error"]})

    return json.dumps(result["data"], indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
