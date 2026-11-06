import React, { useState, useEffect } from 'react';

interface AgentInfo {
  name: string;
  display_name: string;
  description: string;
  domain: string;
  capabilities: string[];
  icon: string;
  status: string;
}

interface AgentTask {
  id: string;
  session_id: string;
  agent_name: string;
  task_description: string;
  status: string;
  created_at: string;
}

export const AgentCenter: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('AUTO_ROUTE');
  const [taskInput, setTaskInput] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [lastResult, setLastResult] = useState<any | null>(null);
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Fetch agents and task history
  const fetchData = async () => {
    try {
      const [agentsRes, tasksRes] = await Promise.all([
        fetch('/api/v1/agents'),
        fetch('/api/v1/agents/tasks/history?limit=10'),
      ]);

      if (agentsRes.ok) {
        const data = await agentsRes.json();
        setAgents(data.agents || []);
      }
      if (tasksRes.ok) {
        const data = await tasksRes.json();
        setTasks(data.tasks || []);
      }
    } catch {
      // Backend polling error caught gracefully
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDispatch = async () => {
    if (!taskInput.trim() || isExecuting) return;
    setIsExecuting(true);
    setError(null);

    try {
      let res;
      if (selectedAgent === 'AUTO_ROUTE') {
        res = await fetch('/api/v1/agents/delegate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction: taskInput }),
        });
      } else {
        res = await fetch(`/api/v1/agents/${selectedAgent}/dispatch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task_description: taskInput }),
        });
      }

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setLastResult(data);
      fetchData();
    } catch (err: any) {
      setError(err.message || 'Task execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const getAgentColor = (name: string) => {
    switch (name) {
      case 'CYRUS_PERSONAL':
        return 'text-emerald-400 border-emerald-800/60 bg-emerald-950/20';
      case 'CYRUS_BUSINESS':
        return 'text-amber-400 border-amber-800/60 bg-amber-950/20';
      case 'CYRUS_DEV':
        return 'text-cyan-400 border-cyan-800/60 bg-cyan-950/20';
      case 'CYRUS_RESEARCH':
        return 'text-purple-400 border-purple-800/60 bg-purple-950/20';
      case 'CYRUS_EXECUTIVE':
        return 'text-blue-400 border-blue-800/60 bg-blue-950/20';
      default:
        return 'text-slate-400 border-slate-800 bg-slate-900/40';
    }
  };

  return (
    <div className="glass-panel p-6 mb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-wider text-slate-100 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
              CYRUS AGENT FRAMEWORK
            </h2>
            <span className="badge-tag mono">PHASE 6</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 mono">
              5 SPECIALISTS ONLINE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Modular multi-agent coordination governed by CYRUS GUARDIAN security, universal "Sir" address, and English response policies.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="text-xs px-3 py-1.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-colors mono self-start sm:self-auto"
        >
          ↻ Refresh Agents
        </button>
      </div>

      {/* Specialist Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 my-6">
        {agents.map((agent) => {
          const isSelected = selectedAgent === agent.name;
          const colorClass = getAgentColor(agent.name);

          return (
            <div
              key={agent.name}
              onClick={() => setSelectedAgent(agent.name)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'border-cyan-400/80 bg-slate-900/80 ring-1 ring-cyan-500/30'
                  : 'border-slate-800/70 bg-slate-950/40 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] mono px-2 py-0.5 rounded border font-semibold ${colorClass}`}>
                    {agent.name.replace('CYRUS_', '')}
                  </span>
                  <span className="text-[10px] text-emerald-400 mono">OPERATIONAL</span>
                </div>

                <h3 className="text-sm font-bold text-slate-100 mb-1">{agent.display_name}</h3>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-3">{agent.description}</p>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 mono uppercase mb-1">Capabilities:</div>
                <div className="flex flex-wrap gap-1">
                  {agent.capabilities.slice(0, 2).map((cap, idx) => (
                    <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-slate-300 border border-slate-800/80">
                      {cap}
                    </span>
                  ))}
                  {agent.capabilities.length > 2 && (
                    <span className="text-[10px] text-slate-500 self-center">+{agent.capabilities.length - 2} more</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Task Dispatcher */}
      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mono flex items-center gap-2">
            <span>Specialist Task Dispatcher</span>
            <span className="text-cyan-400 font-normal">
              (Target: {selectedAgent === 'AUTO_ROUTE' ? '⚡ Intent Auto-Router' : selectedAgent})
            </span>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 mono">Target Agent:</label>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="text-xs bg-slate-900 border border-slate-800 text-slate-200 rounded px-2 py-1 mono outline-none focus:border-cyan-500"
            >
              <option value="AUTO_ROUTE">⚡ Auto-Route by Intent</option>
              {agents.map((a) => (
                <option key={a.name} value={a.name}>
                  {a.display_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Task Input Box */}
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleDispatch()}
            placeholder="Instruct specialist agent (e.g. 'Prepare morning executive briefing', 'Organize study schedule')..."
            className="flex-1 px-4 py-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/80 mono"
          />
          <button
            onClick={handleDispatch}
            disabled={isExecuting || !taskInput.trim()}
            className="px-6 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-bold mono tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-950"
          >
            {isExecuting ? (
              <>
                <span className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                DISPATCHING...
              </>
            ) : (
              'DISPATCH TASK'
            )}
          </button>
        </div>

        {/* Preset Chips */}
        <div className="flex flex-wrap gap-2 mt-3 text-[11px]">
          <span className="text-slate-500 self-center mono">Quick Actions:</span>
          <button
            onClick={() => {
              setSelectedAgent('CYRUS_EXECUTIVE');
              setTaskInput('Prepare a unified morning executive status briefing.');
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-blue-300"
          >
            🛡️ Executive: Morning Briefing
          </button>
          <button
            onClick={() => {
              setSelectedAgent('CYRUS_PERSONAL');
              setTaskInput('Help me organize my B.Tech Computer Science study schedule.');
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-emerald-300"
          >
            📅 Personal: B.Tech Study Plan
          </button>
          <button
            onClick={() => {
              setSelectedAgent('CYRUS_BUSINESS');
              setTaskInput('Check overdue invoices and active client revenue metrics.');
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-amber-300"
          >
            💼 Business: Revenue & Invoices
          </button>
          <button
            onClick={() => {
              setSelectedAgent('CYRUS_DEV');
              setTaskInput('Run codebase automated test verification and check git state.');
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-300"
          >
            💻 Dev: Code & Test Audit
          </button>
          <button
            onClick={() => {
              setSelectedAgent('CYRUS_RESEARCH');
              setTaskInput('Compare local offline inference vs cloud API models with trade-offs.');
            }}
            className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-purple-300"
          >
            🔬 Research: Comparative Trade-Offs
          </button>
        </div>

        {error && (
          <div className="mt-3 p-2.5 rounded bg-red-950/40 border border-red-800 text-xs text-red-300 mono">
            Error: {error}
          </div>
        )}

        {/* Live Execution Output Window */}
        {lastResult && (
          <div className="mt-4 p-4 rounded-lg bg-slate-900/90 border border-cyan-800/50 shadow-inner">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs mono">
              <span className="text-cyan-400 font-bold flex items-center gap-2">
                ✓ Task Result ({lastResult.agent_display_name || lastResult.agent})
              </span>
              <span className="text-slate-400">ID: {lastResult.task_id}</span>
            </div>
            <div className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed font-sans">
              {lastResult.response}
            </div>
            {lastResult.citations && (
              <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-purple-300 mono">
                <div>Source Citations:</div>
                <ul className="list-disc list-inside mt-1 text-slate-400">
                  {lastResult.citations.map((c: string, idx: number) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Live Recent Tasks Log Table */}
      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mono mb-3 flex items-center justify-between">
          <span>Recent Specialist Tasks Ledger (SQLite: `agent_tasks`)</span>
          <span className="text-[11px] text-slate-500 font-normal">{tasks.length} total recorded tasks</span>
        </div>

        <div className="overflow-x-auto rounded-lg border border-slate-800/80">
          <table className="w-full text-left text-xs text-slate-300 mono">
            <thead className="bg-slate-900/90 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Task ID</th>
                <th className="py-2.5 px-3">Specialist Agent</th>
                <th className="py-2.5 px-3">Task Description</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 bg-slate-950/30">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-slate-500">
                    No tasks recorded yet. Dispatch a task above to execute.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.id} className="hover:bg-slate-900/40">
                    <td className="py-2 px-3 text-cyan-400 text-[11px]">{task.id}</td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-200 border border-slate-800 text-[10px]">
                        {task.agent_name}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-200 font-sans truncate max-w-xs">{task.task_description}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          task.status === 'COMPLETED'
                            ? 'bg-emerald-950/60 border border-emerald-800 text-emerald-400'
                            : task.status === 'RUNNING'
                            ? 'bg-amber-950/60 border border-amber-800 text-amber-400 animate-pulse'
                            : 'bg-red-950/60 border border-red-800 text-red-400'
                        }`}
                      >
                        {task.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-500 text-[10px]">{task.created_at?.slice(0, 19).replace('T', ' ')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
