"""CYRUS Research & Approved Computer Access Subsystem.

Contains sandboxed document reader, web researcher, codebase inspector,
and safe Git assistant.
"""

from backend.app.research.code_inspector import CodebaseInspector, codebase_inspector
from backend.app.research.doc_reader import SandboxedDocReader, sandboxed_doc_reader
from backend.app.research.git_assistant import SafeGitAssistant, safe_git_assistant
from backend.app.research.web_researcher import WebResearcher, web_researcher

__all__ = [
    "SandboxedDocReader",
    "sandboxed_doc_reader",
    "WebResearcher",
    "web_researcher",
    "CodebaseInspector",
    "codebase_inspector",
    "SafeGitAssistant",
    "safe_git_assistant",
]
