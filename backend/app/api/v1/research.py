"""CYRUS Research & Approved Computer Access API Router.

Provides endpoints for:
- Sandboxed document reading and summarization.
- Zero-cost web research and citation extraction.
- Codebase file tree and symbol inspection.
- Safe Git version control inspection and commit drafting.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.app.research.code_inspector import codebase_inspector
from backend.app.research.doc_reader import sandboxed_doc_reader
from backend.app.research.git_assistant import safe_git_assistant
from backend.app.research.web_researcher import web_researcher

router = APIRouter(prefix="/research", tags=["CYRUS Research & Approved Computer Access"])


# --- Request & Response Models ---

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Research query or technical inquiry")


class DocumentReadRequest(BaseModel):
    file_path: str = Field(..., description="Target file path inside the sandbox")
    max_chars: int = Field(default=100000, description="Maximum characters to read")


class SymbolSearchRequest(BaseModel):
    query: str = Field(..., description="Symbol name or partial search term")
    symbol_type: Optional[str] = Field(None, description="Filter: class, function, route, interface")


# --- Web Research Endpoints ---

@router.post("/web-search")
async def execute_web_search(request: WebSearchRequest) -> Dict[str, Any]:
    """Conducts a zero-subscription web research inquiry with source attribution."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    report = await web_researcher.execute_research(request.query)
    return {
        "query": report.query,
        "summary": report.summary,
        "citations": [
            {
                "title": c.title,
                "url": c.url,
                "snippet": c.snippet,
                "source_type": c.source_type,
                "reliability_score": c.reliability_score,
            }
            for c in report.citations
        ],
        "sanitized_raw": report.sanitized_raw,
        "is_offline_fallback": report.is_offline_fallback,
        "status": report.status,
    }


# --- Document Reading Endpoints ---

@router.post("/document/read")
async def read_sandboxed_document(request: DocumentReadRequest) -> Dict[str, Any]:
    """Reads and summarizes a document located strictly within the CYRUS sandbox."""
    result = sandboxed_doc_reader.read_document(
        target_path_str=request.file_path,
        max_chars=request.max_chars,
    )
    if not result.is_allowed:
        raise HTTPException(status_code=403, detail=result.error or "Access denied by GUARDIAN security.")

    return {
        "is_allowed": result.is_allowed,
        "target_path": result.target_path,
        "raw_content": result.raw_content,
        "sanitized_content": result.sanitized_content,
        "summary": result.summary,
        "metadata": {
            "file_path": result.metadata.file_path,
            "relative_path": result.metadata.relative_path,
            "file_size_bytes": result.metadata.file_size_bytes,
            "line_count": result.metadata.line_count,
            "word_count": result.metadata.word_count,
            "file_type": result.metadata.file_type,
            "headings": result.metadata.headings,
        } if result.metadata else None,
        "error": result.error,
    }


@router.get("/document/list")
async def list_readable_documents(
    subdir: str = Query("", description="Subdirectory within sandbox"),
    max_files: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """Lists documentation and source files available for reading in the sandbox."""
    files = sandboxed_doc_reader.list_readable_files(subdir=subdir, max_files=max_files)
    return {"files": files, "count": len(files)}


# --- Codebase Inspection Endpoints ---

@router.get("/codebase/tree")
async def get_codebase_tree(
    subdir: str = Query("", description="Relative path within sandbox"),
    max_depth: int = Query(3, ge=1, le=6),
) -> Dict[str, Any]:
    """Returns a filtered directory tree of the project."""
    return codebase_inspector.get_file_tree(subdir=subdir, max_depth=max_depth)


@router.post("/codebase/symbols")
async def search_codebase_symbols(request: SymbolSearchRequest) -> Dict[str, Any]:
    """Searches classes, functions, FastAPI routes, and TypeScript interfaces."""
    symbols = codebase_inspector.search_symbols(
        query=request.query,
        symbol_type=request.symbol_type,
    )
    return {"query": request.query, "count": len(symbols), "symbols": symbols}


@router.get("/codebase/overview")
async def get_codebase_overview() -> Dict[str, Any]:
    """Computes high-level codebase metrics across the project."""
    return codebase_inspector.get_codebase_overview()


@router.get("/codebase/file")
async def inspect_code_file(
    path: str = Query(..., description="Relative file path within sandbox")
) -> Dict[str, Any]:
    """Provides detailed structural metrics and symbol breakdown for a specific file."""
    return codebase_inspector.inspect_file(path)


# --- Git Assistant Endpoints ---

@router.get("/git/status")
async def get_git_status() -> Dict[str, Any]:
    """Returns current Git branch, modified files, and working tree state."""
    report = safe_git_assistant.get_status()
    return {
        "branch": report.branch,
        "is_clean": report.is_clean,
        "staged_files": [
            {"code": f.status_code, "path": f.file_path, "type": f.change_type}
            for f in report.staged_files
        ],
        "unstaged_files": [
            {"code": f.status_code, "path": f.file_path, "type": f.change_type}
            for f in report.unstaged_files
        ],
        "untracked_files": report.untracked_files,
        "summary": report.summary,
    }


@router.get("/git/commits")
async def get_git_commits(
    limit: int = Query(5, ge=1, le=25)
) -> Dict[str, Any]:
    """Returns recent commit log entries."""
    commits = safe_git_assistant.get_recent_commits(limit=limit)
    return {"commits": commits, "count": len(commits)}


@router.get("/git/diff")
async def get_git_diff(
    staged: bool = Query(False, description="Read staged diff instead of unstaged")
) -> Dict[str, Any]:
    """Reads git diff output safely."""
    return safe_git_assistant.get_diff(staged=staged)


@router.post("/git/draft-commit")
async def draft_git_commit() -> Dict[str, Any]:
    """Analyzes pending changes and automatically prepares a Conventional Commit message draft."""
    return safe_git_assistant.draft_commit_message()
