import React, { useEffect, useState } from 'react';

interface CitationItem {
  title: string;
  url: string;
  snippet: string;
  source_type: string;
  reliability_score: number;
}

interface WebResearchResult {
  query: string;
  summary: string;
  citations: CitationItem[];
  sanitized_raw: string;
  is_offline_fallback: boolean;
  status: string;
}

interface DocumentMetadata {
  file_path: string;
  relative_path: string;
  file_size_bytes: number;
  line_count: number;
  word_count: number;
  file_type: string;
  headings: string[];
}

interface DocumentReadResult {
  is_allowed: boolean;
  target_path: string;
  raw_content: string;
  sanitized_content: string;
  summary: string;
  metadata: DocumentMetadata | null;
  error?: string | null;
}

interface GitStatusData {
  branch: string;
  is_clean: boolean;
  staged_files: Array<{ code: string; path: string; type: string }>;
  unstaged_files: Array<{ code: string; path: string; type: string }>;
  untracked_files: string[];
  summary: string;
}

interface GitCommitItem {
  full_hash: string;
  short_hash: string;
  author: string;
  date: string;
  subject: string;
}

interface CodeOverview {
  stats: {
    python_files: number;
    ts_files: number;
    markdown_files: number;
    other_files: number;
    total_lines: number;
    python_lines: number;
    ts_lines: number;
  };
  summary: string;
}

export const ResearchCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'web' | 'doc' | 'code' | 'git'>('web');

  // Web Research state
  const [webQuery, setWebQuery] = useState('Apple Silicon M5 unified memory architecture');
  const [webLoading, setWebLoading] = useState(false);
  const [webResult, setWebResult] = useState<WebResearchResult | null>(null);
  const [webError, setWebError] = useState<string | null>(null);

  // Document Reader state
  const [docPath, setDocPath] = useState('README.md');
  const [docLoading, setDocLoading] = useState(false);
  const [docResult, setDocResult] = useState<DocumentReadResult | null>(null);
  const [docError, setDocError] = useState<string | null>(null);

  // Codebase Inspector state
  const [codeOverview, setCodeOverview] = useState<CodeOverview | null>(null);
  const [symbolQuery, setSymbolQuery] = useState('BaseAgent');
  const [symbolResults, setSymbolResults] = useState<any[]>([]);
  const [symbolLoading, setSymbolLoading] = useState(false);

  // Git Assistant state
  const [gitStatus, setGitStatus] = useState<GitStatusData | null>(null);
  const [gitCommits, setGitCommits] = useState<GitCommitItem[]>([]);
  const [commitDraft, setCommitDraft] = useState<string | null>(null);
  const [gitLoading, setGitLoading] = useState(false);

  // Run initial lightweight fetches
  useEffect(() => {
    fetchGitStatus();
    fetchCodeOverview();
  }, []);

  // Web Research
  const handleWebSearch = async () => {
    if (!webQuery.trim()) return;
    setWebLoading(true);
    setWebError(null);
    try {
      const res = await fetch('/api/v1/research/web-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: webQuery.trim() }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: WebResearchResult = await res.json();
      setWebResult(data);
    } catch (err: any) {
      setWebError(err.message || 'Web research request failed');
    } finally {
      setWebLoading(false);
    }
  };

  // Document Reader
  const handleReadDocument = async (overridePath?: string) => {
    const target = overridePath || docPath;
    if (!target.trim()) return;
    setDocLoading(true);
    setDocError(null);
    try {
      const res = await fetch('/api/v1/research/document/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: target.trim(), max_chars: 100000 }),
      });
      const data = await res.json();
      if (!res.ok) {
        setDocError(data.detail || `Access denied: HTTP ${res.status}`);
        setDocResult(null);
      } else {
        setDocResult(data);
        if (overridePath) setDocPath(overridePath);
      }
    } catch (err: any) {
      setDocError(err.message || 'Document read failed');
      setDocResult(null);
    } finally {
      setDocLoading(false);
    }
  };

  // Codebase Overview & Symbol Search
  const fetchCodeOverview = async () => {
    try {
      const res = await fetch('/api/v1/research/codebase/overview');
      if (res.ok) {
        const data = await res.json();
        setCodeOverview(data);
      }
    } catch (e) {
      // Handled silently
    }
  };

  const handleSymbolSearch = async () => {
    if (!symbolQuery.trim()) return;
    setSymbolLoading(true);
    try {
      const res = await fetch('/api/v1/research/codebase/symbols', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: symbolQuery.trim() }),
      });
      if (res.ok) {
        const data = await res.json();
        setSymbolResults(data.symbols || []);
      }
    } catch (e) {
      // Handled silently
    } finally {
      setSymbolLoading(false);
    }
  };

  // Git Status & Commits
  const fetchGitStatus = async () => {
    setGitLoading(true);
    try {
      const [statusRes, commitsRes] = await Promise.all([
        fetch('/api/v1/research/git/status'),
        fetch('/api/v1/research/git/commits?limit=5'),
      ]);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setGitStatus(statusData);
      }
      if (commitsRes.ok) {
        const commitsData = await commitsRes.json();
        setGitCommits(commitsData.commits || []);
      }
    } catch (e) {
      // Handled silently
    } finally {
      setGitLoading(false);
    }
  };

  const handleDraftCommit = async () => {
    try {
      const res = await fetch('/api/v1/research/git/draft-commit', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setCommitDraft(data.draft || data.summary);
      }
    } catch (e) {
      // Handled silently
    }
  };

  return (
    <div className="glass-panel p-5 mb-6 border border-cyan-800/40">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🔬</span>
            <h2 className="text-lg font-bold text-slate-100">CYRUS Research & Approved Computer Access</h2>
            <span className="badge-tag mono text-cyan-400 bg-cyan-950/60 border-cyan-700/60">PHASE 7</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Sandboxed document parsing, zero-cost web research, codebase symbol inspection, and safe Git version control under GUARDIAN supervision.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs font-medium">
          <button
            onClick={() => setActiveTab('web')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'web' ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Web Research
          </button>
          <button
            onClick={() => setActiveTab('doc')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'doc' ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Doc Reader
          </button>
          <button
            onClick={() => setActiveTab('code')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'code' ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Code Inspector
          </button>
          <button
            onClick={() => setActiveTab('git')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'git' ? 'bg-cyan-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Safe Git
          </button>
        </div>
      </div>

      {/* --- TAB 1: WEB RESEARCH --- */}
      {activeTab === 'web' && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={webQuery}
                onChange={(e) => setWebQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleWebSearch()}
                placeholder="Enter technical topic or scientific inquiry (e.g., Quantum Computing, Fast Fourier Transform)..."
                className="flex-1 bg-slate-900/70 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={handleWebSearch}
                disabled={webLoading}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1"
              >
                {webLoading ? 'Researching...' : 'Search'}
              </button>
            </div>

            {/* Quick Presets */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
              <span className="text-slate-500">Inquiry Presets:</span>
              {[
                'Apple Silicon M5 unified memory',
                'Local ONNX Runtime inference optimization',
                'FastAPI SQLite WAL concurrency',
              ].map((chip) => (
                <button
                  key={chip}
                  onClick={() => {
                    setWebQuery(chip);
                  }}
                  className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-cyan-300 hover:border-cyan-600/60"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {webError && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
              {webError}
            </div>
          )}

          {webResult && (
            <div className="space-y-3">
              <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-cyan-300 uppercase tracking-wider">
                    Executive Research Synthesis
                  </span>
                  {webResult.is_offline_fallback ? (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
                      OFFLINE LOCAL SYNTHESIS
                    </span>
                  ) : (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                      LIVE SOURCE VERIFIED
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">{webResult.summary}</p>
              </div>

              {/* Citations List */}
              {webResult.citations.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-slate-400 mb-2">
                    Verified Technical Citations ({webResult.citations.length})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {webResult.citations.map((cite, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-xs font-semibold text-slate-200 truncate">{cite.title}</span>
                          <span className="text-[10px] mono px-1.5 py-0.5 rounded bg-cyan-950/50 text-cyan-400 border border-cyan-800/40">
                            {Math.round(cite.reliability_score * 100)}% RELIABLE
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-2 mb-1.5">{cite.snippet}</p>
                        <span className="text-[10px] mono text-cyan-400/80 truncate block">{cite.source_type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* --- TAB 2: SANDBOXED DOCUMENT READER --- */}
      {activeTab === 'doc' && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-col gap-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={docPath}
                onChange={(e) => setDocPath(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleReadDocument()}
                placeholder="Relative file path within sandbox (e.g. README.md, ARCHITECTURE.md)..."
                className="flex-1 bg-slate-900/70 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={() => handleReadDocument()}
                disabled={docLoading}
                className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {docLoading ? 'Reading...' : 'Read Document'}
              </button>
            </div>

            {/* Quick Pick Document Chips */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-400">
              <span className="text-slate-500">Sandbox Files:</span>
              {['README.md', 'ARCHITECTURE.md', 'SECURITY.md', 'DEVELOPMENT_ROADMAP.md', 'CHANGELOG.md'].map((file) => (
                <button
                  key={file}
                  onClick={() => handleReadDocument(file)}
                  className="px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-cyan-300 hover:border-cyan-600/60"
                >
                  {file}
                </button>
              ))}
              {/* Path Traversal Drill Button */}
              <button
                onClick={() => handleReadDocument('../../../../etc/passwd')}
                className="px-2 py-0.5 rounded bg-rose-950/60 border border-rose-800 text-rose-300 hover:bg-rose-900/80 font-mono text-[10px]"
                title="Test GUARDIAN sandbox path traversal defense"
              >
                ⚠️ Test Path Traversal (/etc/passwd)
              </button>
            </div>
          </div>

          {docError && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
              <div className="font-semibold mb-1">GUARDIAN Security Boundary Active</div>
              <div>{docError}</div>
            </div>
          )}

          {docResult && docResult.metadata && (
            <div className="space-y-3">
              {/* Document Metrics Card */}
              <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
                <div>
                  <span className="text-slate-400">Target File: </span>
                  <span className="mono font-semibold text-cyan-300">{docResult.metadata.relative_path}</span>
                </div>
                <div className="flex items-center gap-4 text-slate-300 mono text-[11px]">
                  <span>Lines: <strong className="text-white">{docResult.metadata.line_count}</strong></span>
                  <span>Words: <strong className="text-white">{docResult.metadata.word_count}</strong></span>
                  <span>Size: <strong className="text-white">{(docResult.metadata.file_size_bytes / 1024).toFixed(1)} KB</strong></span>
                  <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                    ISOLATED
                  </span>
                </div>
              </div>

              {/* Headings Outline */}
              {docResult.metadata.headings.length > 0 && (
                <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-400 block mb-1.5">Document Outline:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {docResult.metadata.headings.slice(0, 8).map((h, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {h}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              <div className="p-4 rounded-lg bg-slate-900/90 border border-slate-800">
                <span className="text-xs font-semibold text-cyan-300 uppercase tracking-wider block mb-2">
                  Executive Document Briefing
                </span>
                <p className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">{docResult.summary}</p>
              </div>

              {/* Untrusted Isolation Banner */}
              <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-800/40 text-[11px] text-cyan-300 flex items-center justify-between">
                <span>Content quarantined inside &lt;untrusted_content&gt; tags to defend against prompt injection.</span>
                <span className="mono text-[10px] bg-cyan-900/50 px-2 py-0.5 rounded">Prompt Guard Active</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* --- TAB 3: CODEBASE INSPECTOR --- */}
      {activeTab === 'code' && (
        <div className="mt-4 space-y-4">
          {codeOverview && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 block">Python Engine</span>
                <span className="text-base font-bold text-cyan-400 mono">{codeOverview.stats.python_files} files</span>
                <span className="text-[10px] text-slate-500 block mono">{codeOverview.stats.python_lines} lines</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 block">TypeScript Frontend</span>
                <span className="text-base font-bold text-emerald-400 mono">{codeOverview.stats.ts_files} files</span>
                <span className="text-[10px] text-slate-500 block mono">{codeOverview.stats.ts_lines} lines</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 block">Documentation</span>
                <span className="text-base font-bold text-amber-400 mono">{codeOverview.stats.markdown_files} docs</span>
                <span className="text-[10px] text-slate-500 block mono">Architecture specs</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
                <span className="text-[11px] text-slate-400 block">Total Monitored</span>
                <span className="text-base font-bold text-white mono">{codeOverview.stats.total_lines} lines</span>
                <span className="text-[10px] text-slate-500 block mono">Local sandbox</span>
              </div>
            </div>
          )}

          {/* Symbol Search Bar */}
          <div className="flex gap-2">
            <input
              type="text"
              value={symbolQuery}
              onChange={(e) => setSymbolQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSymbolSearch()}
              placeholder="Search code symbols (classes, functions, routes, interfaces)..."
              className="flex-1 bg-slate-900/70 border border-slate-700/80 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={handleSymbolSearch}
              disabled={symbolLoading}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
            >
              {symbolLoading ? 'Scanning...' : 'Find Symbols'}
            </button>
          </div>

          {/* Symbol Results */}
          {symbolResults.length > 0 && (
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              <span className="text-[11px] font-semibold text-slate-400 block">
                Matching Symbols ({symbolResults.length}):
              </span>
              {symbolResults.map((s, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div className="truncate mr-2">
                    <span className="mono font-semibold text-cyan-300 mr-2">{s.name}</span>
                    <span className="mono text-[11px] text-slate-400">{s.signature}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] mono text-slate-500">{s.file}:{s.line}</span>
                    <span className="text-[10px] mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {s.type}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* --- TAB 4: SAFE GIT ASSISTANT --- */}
      {activeTab === 'git' && (
        <div className="mt-4 space-y-4">
          {gitStatus && (
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Branch:</span>
                <span className="mono font-bold text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/60">
                  {gitStatus.branch}
                </span>
                {gitStatus.is_clean ? (
                  <span className="text-[10px] mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                    CLEAN WORKING TREE
                  </span>
                ) : (
                  <span className="text-[10px] mono px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
                    CHANGES DETECTED
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleDraftCommit}
                  className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs border border-slate-700 font-medium"
                >
                  Draft Commit Message
                </button>
                <button
                  onClick={fetchGitStatus}
                  disabled={gitLoading}
                  className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
                >
                  Refresh
                </button>
              </div>
            </div>
          )}

          {/* Commit Message Draft */}
          {commitDraft && (
            <div className="p-3 rounded-lg bg-slate-900/90 border border-cyan-800/50">
              <span className="text-xs font-semibold text-cyan-300 block mb-1.5">
                Suggested Conventional Commit Draft:
              </span>
              <pre className="mono text-xs text-emerald-300 bg-slate-950/80 p-2 rounded border border-slate-800 overflow-x-auto whitespace-pre-wrap">
                {commitDraft}
              </pre>
            </div>
          )}

          {/* Pending Changes List */}
          {gitStatus && !gitStatus.is_clean && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400 block">Pending Workspace Changes:</span>
              <div className="space-y-1 text-xs mono">
                {gitStatus.staged_files.map((f, idx) => (
                  <div key={idx} className="p-1.5 rounded bg-slate-900/40 border border-slate-800 flex justify-between">
                    <span className="text-emerald-400">{f.path}</span>
                    <span className="text-emerald-500 text-[10px]">STAGED {f.type}</span>
                  </div>
                ))}
                {gitStatus.unstaged_files.map((f, idx) => (
                  <div key={idx} className="p-1.5 rounded bg-slate-900/40 border border-slate-800 flex justify-between">
                    <span className="text-amber-300">{f.path}</span>
                    <span className="text-amber-400 text-[10px]">UNSTAGED {f.type}</span>
                  </div>
                ))}
                {gitStatus.untracked_files.map((f, idx) => (
                  <div key={idx} className="p-1.5 rounded bg-slate-900/40 border border-slate-800 flex justify-between">
                    <span className="text-slate-400">{f}</span>
                    <span className="text-slate-500 text-[10px]">UNTRACKED</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Commits Log */}
          {gitCommits.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400 block">Recent Repository Commits:</span>
              <div className="space-y-1.5">
                {gitCommits.map((c, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-slate-900/40 border border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div className="truncate mr-3">
                      <span className="mono text-cyan-400 text-[11px] mr-2">[{c.short_hash}]</span>
                      <span className="text-slate-200">{c.subject}</span>
                    </div>
                    <span className="text-[10px] mono text-slate-500 shrink-0">{c.date}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Safety Notice */}
          <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              Destructive operations (`git reset --hard`, `git push --force`) are strictly blocked by GUARDIAN L4.
            </span>
            <span className="text-emerald-400 font-mono text-[10px]">GUARDIAN Supervised</span>
          </div>
        </div>
      )}
    </div>
  );
};
