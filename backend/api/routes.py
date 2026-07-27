"""
routes.py
---------
REST API surface for CloudOps AI.

POST /api/analyze  - upload one infra file, run the full agent pipeline,
                      return a CloudHealthReport.
GET  /api/health    - simple liveness check.
"""

import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from models import CloudHealthReport
from parsers import parse_file, UnsupportedFileError
from agents.controller import run_pipeline

logger = logging.getLogger("cloudops.api")

router = APIRouter()

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB is plenty for IaC/log uploads


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=CloudHealthReport)
async def analyze(file: UploadFile = File(...)):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    try:
        raw_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.")

    try:
        infra = parse_file(file.filename, raw_text)
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Parsing failed for %s", file.filename)
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {exc}")

    try:
        report = await run_pipeline(infra)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent pipeline failed for %s", file.filename)
        raise HTTPException(status_code=502, detail=f"Analysis pipeline failed: {exc}")

    return report
