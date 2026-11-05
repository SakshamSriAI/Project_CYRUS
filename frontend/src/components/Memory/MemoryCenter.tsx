import React, { useState, useEffect } from 'react';

interface MemoryItem {
  id: string;
  category: string;
  tenant_id: string;
  memory_key: string;
  memory_value: string;
  fact_type: string;
  confidence: number;
  source: string;
  updated_at: string;
}

interface RecoveryBriefing {
  has_previous_session: boolean;
  session_id?: string;
  recovery_status: string;
  is_clean_shutdown: boolean;
  restored_messages_count: number;
  unfinished_tasks_count: number;
  pending_approvals_count: number;
  briefing: string;
}

export const MemoryCenter: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<'personal' | 'business' | 'working'>('personal');
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [briefing, setBriefing] = useState<RecoveryBriefing | null>(null);

  // New Memory form state
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newFactType, setNewFactType] = useState('VERIFIED_FACT');
  const [feedback, setFeedback] = useState('');

  const fetchBriefing = async () => {
    try {
      const res = await fetch('/api/v1/memory/recovery/briefing');
      if (res.ok) {
        const data = await res.json();
        setBriefing(data);
      }
    } catch {
      // Ignored
    }
  };

  const fetchMemories = async () => {
    try {
      let url = `/api/v1/memory/items?category=${activeCategory}`;
      if (searchTerm.trim()) {
        url += `&search=${encodeURIComponent(searchTerm.trim())}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setMemories(data.items || []);
      }
    } catch {
      // Handled silently
    }
  };

  useEffect(() => {
    fetchBriefing();
  }, []);

  useEffect(() => {
    fetchMemories();
  }, [activeCategory, searchTerm]);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;

    try {
      const res = await fetch('/api/v1/memory/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: activeCategory,
          memory_key: newKey.trim(),
          memory_value: newValue.trim(),
          fact_type: newFactType,
          tenant_id: 'default',
        }),
      });

      if (res.ok) {
        setFeedback(`Memory '${newKey}' saved successfully.`);
        setNewKey('');
        setNewValue('');
        fetchMemories();
      } else {
        const err = await res.json();
        setFeedback(`Error: ${err.detail || 'Failed'}`);
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message}`);
    }
  };

  const handleDelete = async (memoryId: string) => {
    try {
      const res = await fetch(`/api/v1/memory/items/${memoryId}`, { method: 'DELETE' });
      if (res.ok) {
        setFeedback('Memory entry deleted.');
        fetchMemories();
      }
    } catch (err: any) {
      setFeedback(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="glass-panel p-5 mb-6">
      {/* Session Recovery Banner */}
      {briefing && briefing.has_previous_session && (
        <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-blue-950/60 to-cyan-950/40 border border-cyan-500/30 flex items-start justify-between gap-4 shadow-lg shadow-cyan-950/20">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-300">
                SESSION RECOVERY & PERSISTENCE
              </h3>
              <span className={`badge-tag mono text-[10px] ${briefing.is_clean_shutdown ? 'text-emerald-400 border-emerald-800' : 'text-amber-400 border-amber-800'}`}>
                {briefing.recovery_status}
              </span>
            </div>
            <p className="text-sm text-slate-100 font-medium leading-relaxed">
              "{briefing.briefing}"
            </p>
          </div>

          <div className="text-right text-xs mono text-slate-400 whitespace-nowrap pl-4 border-l border-slate-800">
            <div>Restored Messages: <strong className="text-cyan-300">{briefing.restored_messages_count}</strong></div>
            <div>Unfinished Tasks: <strong className="text-slate-200">{briefing.unfinished_tasks_count}</strong></div>
          </div>
        </div>
      )}

      {/* Memory Center Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>CYRUS MEMORY Center</span>
            <span className="badge-tag mono">PERSISTENT SQLITE</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Personal Knowledge • Multi-Tenant Business Memory • Working Context
          </p>
        </div>

        {/* Category Tabs */}
        <div className="flex rounded-lg bg-slate-900/80 p-1 border border-slate-800">
          <button
            onClick={() => setActiveCategory('personal')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeCategory === 'personal'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Personal Memory
          </button>
          <button
            onClick={() => setActiveCategory('business')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeCategory === 'business'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Business Memory
          </button>
          <button
            onClick={() => setActiveCategory('working')}
            className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
              activeCategory === 'working'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Working Memory
          </button>
        </div>
      </div>

      {feedback && (
        <div className="mt-3 p-2 rounded bg-cyan-950/40 border border-cyan-800/40 text-xs mono text-cyan-300">
          ✓ {feedback}
        </div>
      )}

      {/* Search & Add Memory Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-5">
        {/* Memory Browser (2 Cols) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={`Search ${activeCategory} memory keys and notes...`}
              className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
            />
            <button onClick={fetchMemories} className="btn-cyrus text-xs py-2">
              Search
            </button>
          </div>

          <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
            {memories.length === 0 ? (
              <div className="p-8 rounded-lg bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                No active records in {activeCategory} memory. Add a record on the right or ask CYRUS to remember in chat!
              </div>
            ) : (
              memories.map((m) => (
                <div
                  key={m.id}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-3 hover:border-slate-700 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="mono font-semibold text-cyan-300 text-xs">{m.memory_key}</span>
                      <span className="badge-tag mono text-[10px]">{m.fact_type}</span>
                      <span className="text-[10px] text-slate-500 mono">Conf: {m.confidence * 100}%</span>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">{m.memory_value}</p>
                    <div className="text-[10px] text-slate-500 mt-1 mono">
                      Source: {m.source} • Updated: {new Date(m.updated_at).toLocaleDateString()}
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(m.id)}
                    className="text-slate-500 hover:text-rose-400 text-xs p-1"
                    title="Delete memory record"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Add Memory Form (1 Col) */}
        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3">
            Add to {activeCategory} Memory
          </h3>

          <form onSubmit={handleAddMemory} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Memory Key / Identifier:</label>
              <input
                type="text"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                placeholder="e.g. study_routine or client_lead"
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Value / Fact to Remember:</label>
              <textarea
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                placeholder="e.g. Study Computer Science 2 hours daily"
                rows={3}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Fact Classification:</label>
              <select
                value={newFactType}
                onChange={(e) => setNewFactType(e.target.value)}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-700 text-slate-200 focus:outline-none focus:border-cyan-400"
              >
                <option value="VERIFIED_FACT">VERIFIED_FACT (Permanent truth)</option>
                <option value="PREFERENCE">PREFERENCE (Personal habit)</option>
                <option value="ROUTINE">ROUTINE (Schedule / agenda)</option>
                <option value="TASK_GOAL">TASK_GOAL (In-flight goal)</option>
                <option value="ASSUMPTION">ASSUMPTION (Working hypothesis)</option>
              </select>
            </div>

            <button type="submit" className="w-full btn-cyrus justify-center py-2">
              + Save to Memory
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
