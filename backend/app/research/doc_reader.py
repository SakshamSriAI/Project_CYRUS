"""CYRUS Sandboxed Document Reader.

Provides secure, sandboxed document reading and summarization for Markdown,
plain text, code, structured configs, and PDF documents.

Enforces:
1. Strict path-traversal prevention: All targets must reside strictly within CYRUS_SANDBOX_PATH.
2. Prompt injection defense: Wraps untrusted document content in <untrusted_content> boundary tags.
3. Resource limits: Prevents excessive memory consumption on Apple Silicon M5.
4. Professional conversational synthesis addressing the user as "Sir".
"""

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import zlib
from backend.app.config import settings
from backend.app.guardian.permissions import ActionRequest, permission_engine
from backend.app.guardian.prompt_injection import prompt_injection_guard

logger = logging.getLogger("cyrus.research.doc_reader")

SUPPORTED_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".text", ".json", ".csv",
    ".py", ".ts", ".tsx", ".js", ".jsx", ".html", ".css",
    ".yml", ".yaml", ".sh", ".env.example", ".log", ".pdf",
}


@dataclass
class DocumentMetadata:
    """Metadata describing a read document."""
    file_path: str
    relative_path: str
    file_size_bytes: int
    line_count: int
    word_count: int
    file_type: str
    headings: List[str] = field(default_factory=list)


@dataclass
class DocumentReadResult:
    """Result of reading a document inside the sandbox."""
    is_allowed: bool
    target_path: str
    raw_content: str
    sanitized_content: str
    summary: str
    metadata: Optional[DocumentMetadata] = None
    error: Optional[str] = None


class SandboxedDocReader:
    """Secure document reader confined to CYRUS sandbox boundaries."""

    def __init__(self, sandbox_root: Optional[Path] = None):
        self.sandbox_root = (sandbox_root or Path(settings.CYRUS_SANDBOX_PATH)).resolve()

    def is_safe_path(self, target_path_str: str) -> bool:
        """Verifies target path resides strictly inside authorized sandbox."""
        try:
            target = Path(target_path_str).resolve()
            return target == self.sandbox_root or self.sandbox_root in target.parents
        except Exception:
            return False

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        """Extracts text streams from PDF without external binary dependencies."""
        extracted_text_chunks: List[str] = []

        # 1. Search for FlateDecode compressed streams
        stream_matches = re.finditer(b"stream\r?\n(.*?)\r?\nendstream", file_bytes, re.DOTALL)
        for match in stream_matches:
            raw_stream = match.group(1)
            try:
                decompressed = zlib.decompress(raw_stream)
                # Look for text operators like (Text) Tj or [(T)(ext)] TJ
                text_operators = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
                if text_operators:
                    chunk = " ".join(t.decode("utf-8", errors="ignore") for t in text_operators)
                    extracted_text_chunks.append(chunk)
                else:
                    # Generic ASCII tokens inside stream
                    clean_tokens = [
                        w.decode("utf-8", errors="ignore")
                        for w in decompressed.split()
                        if len(w) > 3 and w.isalnum()
                    ]
                    if len(clean_tokens) > 5:
                        extracted_text_chunks.append(" ".join(clean_tokens))
            except Exception:
                continue

        # 2. Fallback to extracting literal ASCII / UTF-8 strings
        if not extracted_text_chunks:
            direct_strings = re.findall(rb"\(([\x20-\x7E\s]{4,})\)", file_bytes)
            if direct_strings:
                extracted_text_chunks.append(
                    " ".join(s.decode("utf-8", errors="ignore") for s in direct_strings)
                )

        if not extracted_text_chunks:
            return "[PDF Binary File: Structured PDF document recognized without uncompressed text stream.]"

        return "\n\n".join(extracted_text_chunks)

    def _extract_headings(self, text: str, ext: str) -> List[str]:
        """Extracts section outlines for markdown documents."""
        if ext not in [".md", ".markdown"]:
            return []
        headings = []
        for line in text.splitlines():
            line_s = line.strip()
            if line_s.startswith("#"):
                headings.append(line_s)
            if len(headings) >= 15:
                break
        return headings

    def _generate_document_summary(
        self, relative_path: str, text: str, line_count: int, word_count: int, headings: List[str]
    ) -> str:
        """Produces a structured document overview addressing the user as Sir."""
        outline_bullet = ""
        if headings:
            outline_bullet = "\n• **Key Headings**:\n  - " + "\n  - ".join(headings[:5])

        excerpt = " ".join(text[:400].splitlines()).strip()
        if len(excerpt) > 250:
            excerpt = excerpt[:250] + "..."

        return (
            f"I have reviewed the document '{relative_path}', Sir:\n\n"
            f"• **Metrics**: {line_count} lines, {word_count} words.\n"
            f"• **Preview**: {excerpt}{outline_bullet}\n\n"
            "The document has been securely processed and isolated from instruction injection, Sir."
        )

    def read_document(self, target_path_str: str, max_chars: int = 100_000) -> DocumentReadResult:
        """Reads and analyzes document content while strictly enforcing sandbox boundaries."""
        try:
            # Resolve relative paths against sandbox root
            path_obj = Path(target_path_str)
            if not path_obj.is_absolute():
                resolved_path = (self.sandbox_root / path_obj).resolve()
            else:
                resolved_path = path_obj.resolve()
        except Exception as e:
            return DocumentReadResult(
                is_allowed=False,
                target_path=target_path_str,
                raw_content="",
                sanitized_content="",
                summary="",
                error=f"Invalid path syntax: {e}",
            )

        # 1. GUARDIAN Sandbox Boundary Verification
        if not self.is_safe_path(str(resolved_path)):
            decision = permission_engine.evaluate_action(
                ActionRequest(
                    actor="DOC_READER",
                    action_type="read_document",
                    target_resource=str(resolved_path),
                )
            )
            logger.warning(
                "Access blocked by GUARDIAN: Target %s is outside sandbox %s",
                resolved_path, self.sandbox_root
            )
            return DocumentReadResult(
                is_allowed=False,
                target_path=str(resolved_path),
                raw_content="",
                sanitized_content="",
                summary=f"Security Alert: Document path '{target_path_str}' is outside authorized sandbox, Sir.",
                error=f"Access blocked by GUARDIAN security: {decision.reason}",
            )

        if not resolved_path.exists():
            return DocumentReadResult(
                is_allowed=True,
                target_path=str(resolved_path),
                raw_content="",
                sanitized_content="",
                summary=f"The requested document '{resolved_path.name}' does not exist, Sir.",
                error="File does not exist.",
            )

        if not resolved_path.is_file():
            return DocumentReadResult(
                is_allowed=True,
                target_path=str(resolved_path),
                raw_content="",
                sanitized_content="",
                summary=f"The target '{resolved_path.name}' is a directory, not a document, Sir.",
                error="Target path is a directory.",
            )

        ext = resolved_path.suffix.lower()
        if ext and ext not in SUPPORTED_EXTENSIONS:
            return DocumentReadResult(
                is_allowed=True,
                target_path=str(resolved_path),
                raw_content="",
                sanitized_content="",
                summary=f"Unsupported file extension '{ext}' for document reading, Sir.",
                error=f"Unsupported extension: {ext}",
            )

        try:
            relative_str = str(resolved_path.relative_to(self.sandbox_root))
        except Exception:
            relative_str = resolved_path.name

        # 2. File Reading & Decoding
        try:
            file_bytes = resolved_path.read_bytes()
            file_size = len(file_bytes)

            if ext == ".pdf":
                raw_text = self._extract_pdf_text(file_bytes)
            else:
                try:
                    raw_text = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    raw_text = file_bytes.decode("latin-1", errors="replace")

            # Enforce max character limit for memory safety on M5
            truncated = False
            if len(raw_text) > max_chars:
                raw_text = raw_text[:max_chars]
                truncated = True

            # 3. Prompt Injection Defense Wrapping
            sanitized = prompt_injection_guard.wrap_untrusted_content(
                raw_text, source=f"local_file://{relative_str}"
            )
            if truncated:
                sanitized += "\n\n<!-- Truncated at 100,000 characters for memory safety -->"

            lines = raw_text.splitlines()
            line_count = len(lines)
            word_count = len(raw_text.split())
            headings = self._extract_headings(raw_text, ext)

            metadata = DocumentMetadata(
                file_path=str(resolved_path),
                relative_path=relative_str,
                file_size_bytes=file_size,
                line_count=line_count,
                word_count=word_count,
                file_type=ext if ext else "unknown",
                headings=headings,
            )

            summary = self._generate_document_summary(
                relative_str, raw_text, line_count, word_count, headings
            )

            return DocumentReadResult(
                is_allowed=True,
                target_path=str(resolved_path),
                raw_content=raw_text,
                sanitized_content=sanitized,
                summary=summary,
                metadata=metadata,
                error=None,
            )

        except Exception as e:
            logger.error("Error reading file %s: %s", resolved_path, e)
            return DocumentReadResult(
                is_allowed=True,
                target_path=str(resolved_path),
                raw_content="",
                sanitized_content="",
                summary=f"An error occurred while reading the file, Sir: {e}",
                error=str(e),
            )

    def list_readable_files(self, subdir: str = "", max_files: int = 50) -> List[Dict[str, Any]]:
        """Lists readable documentation and code files inside sandbox for quick access."""
        base_dir = (self.sandbox_root / subdir).resolve()
        if not self.is_safe_path(str(base_dir)) or not base_dir.exists():
            return []

        ignored_patterns = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        results: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignored_patterns and not d.startswith(".")]
            for f in sorted(files):
                p = Path(root) / f
                if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    try:
                        rel = str(p.relative_to(self.sandbox_root))
                        results.append({
                            "name": f,
                            "path": rel,
                            "extension": p.suffix.lower(),
                            "size_bytes": p.stat().st_size,
                        })
                    except Exception:
                        pass
                if len(results) >= max_files:
                    return results

        return results


sandboxed_doc_reader = SandboxedDocReader()
