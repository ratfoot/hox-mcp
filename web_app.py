"""
FastAPI web app wrapping the MCP tool functions.
Serves a vanilla JS frontend for the NCBI SRA Manifest Curator.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from main import (
    search_studies,
    get_study_info,
    list_runs,
    get_file_urls,
    list_manifests,
    approve_manifest,
    import_to_hox,
    get_import_status,
    MANIFEST_DIR,
    _parse_tags,
)

app = FastAPI(title="NCBI SRA Manifest Curator")


# --- Pydantic models for POST bodies ---

class RunInfo(BaseModel):
    accession: str
    sample: str = ""
    strategy: str = ""
    source: str = ""
    platform: str = ""
    spots: str = ""
    bases: str = ""


class StagedStudy(BaseModel):
    accession: str
    title: str = ""
    runs: List[RunInfo]


class ManifestCreate(BaseModel):
    name: str
    description: str
    studies: List[StagedStudy]
    tags: Optional[str] = None


class ImportRequest(BaseModel):
    set_name: Optional[str] = None
    profile: Optional[str] = None


# --- API routes (sync def so FastAPI threads them) ---

@app.get("/api/search")
def api_search(
    query: str,
    database: str = "gds",
    organism: str = "Homo sapiens",
    limit: int = 20,
    year: Optional[str] = None,
):
    result = search_studies(query, database=database, organism=organism, limit=limit, year=year)
    return json.loads(result)


@app.get("/api/study/{accession}")
def api_study(accession: str):
    result = get_study_info(accession)
    return json.loads(result)


@app.get("/api/runs/{study_accession}")
def api_runs(study_accession: str):
    result = list_runs(study_accession)
    return json.loads(result)


@app.get("/api/files/{accession}")
def api_files(accession: str):
    result = get_file_urls(accession)
    return json.loads(result)


@app.post("/api/manifests")
def api_create_manifest(body: ManifestCreate):
    """Fast manifest creation — uses pre-fetched run data from the frontend."""
    accessions = []
    all_runs = []

    for study in body.studies:
        run_accs = [r.accession for r in study.runs]
        all_runs.extend(run_accs)
        accessions.append({
            "accession": study.accession,
            "title": study.title,
            "status": "ok",
            "runs": run_accs,
            "metadata": {
                "accession": study.accession,
                "title": study.title,
                "run_count": len(study.runs),
                "runs": [r.model_dump() for r in study.runs],
            },
        })

    manifest = {
        "name": body.name,
        "description": body.description,
        "created_at": datetime.now().isoformat(),
        "status": "pending",
        "tags": _parse_tags(body.tags),
        "accessions": accessions,
        "total_runs": len(all_runs),
    }

    path = MANIFEST_DIR / f"{body.name}.json"
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    return {
        "created": body.name,
        "path": str(path),
        "accession_count": len(accessions),
        "total_runs": len(all_runs),
        "status": "pending",
    }


@app.get("/api/manifests")
def api_list_manifests(name: Optional[str] = Query(None)):
    result = list_manifests(name=name)
    return json.loads(result)


@app.get("/api/manifests/{name}/export")
def api_export_manifest(name: str):
    """Export a manifest as a clean JSON for hox import iteration."""
    from fastapi.responses import JSONResponse

    path = MANIFEST_DIR / f"{name}.json"
    if not path.exists():
        return JSONResponse({"error": f"Manifest '{name}' not found"}, status_code=404)

    with open(path) as f:
        manifest = json.load(f)

    # Build a clean export: flat list of runs grouped by study
    studies = []
    for entry in manifest.get("accessions", []):
        runs_data = entry.get("metadata", {}).get("runs", [])
        study = {
            "study_accession": entry.get("accession", ""),
            "title": entry.get("title", entry.get("metadata", {}).get("title", "")),
            "runs": [],
        }
        for r in runs_data:
            if isinstance(r, dict):
                study["runs"].append({
                    "accession": r.get("accession", ""),
                    "spots": r.get("spots", ""),
                    "bases": r.get("bases", ""),
                    "strategy": r.get("strategy", ""),
                    "platform": r.get("platform", ""),
                })
            elif isinstance(r, str):
                study["runs"].append({"accession": r})
        # Fallback: if no detailed runs, use the accession list
        if not study["runs"]:
            for acc in entry.get("runs", []):
                study["runs"].append({"accession": acc})
        studies.append(study)

    export = {
        "manifest": name,
        "description": manifest.get("description", ""),
        "status": manifest.get("status", ""),
        "tags": manifest.get("tags", {}),
        "total_runs": manifest.get("total_runs", 0),
        "studies": studies,
        "run_accessions": [
            r["accession"] for s in studies for r in s["runs"]
        ],
    }

    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f'attachment; filename="{name}.json"',
        },
    )


@app.post("/api/manifests/{name}/approve")
def api_approve_manifest(name: str):
    result = approve_manifest(name)
    return json.loads(result)


@app.post("/api/manifests/{name}/import")
def api_import(name: str, body: ImportRequest = ImportRequest()):
    result = import_to_hox(
        manifest_name=name,
        set_name=body.set_name,
        profile=body.profile,
    )
    return json.loads(result)


@app.get("/api/import-status")
def api_import_status(profile: Optional[str] = Query(None)):
    result = get_import_status(profile=profile)
    return json.loads(result)


# --- Static files & SPA fallback ---

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    return FileResponse("static/index.html")
