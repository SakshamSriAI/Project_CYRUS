import React from 'react';

interface DiagnosticsProps {
  system: {
    ram_total_gb: number;
    ram_available_gb: number | string;
    ram_percent_used: number;
    cpu_percent: number;
  };
  database: {
    status: string;
    journal_mode: string;
    path: string;
  };
}

export const SystemDiagnostics: React.FC<DiagnosticsProps> = ({ system, database }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Host Machine & Architecture */}
      <div className="glass-panel p-4">
        <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">COMPUTE HARDWARE</div>
        <div className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <span>Apple M5</span>
          <span className="badge-tag mono">ARM64</span>
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>Host Machine:</span>
          <span className="mono text-cyan-300">MacBook Air</span>
        </div>
        <div className="text-xs text-slate-400 mt-1 flex justify-between">
          <span>Target Budget:</span>
          <span className="mono text-emerald-400 font-semibold">₹0 (Local First)</span>
        </div>
      </div>

      {/* 2. Unified Memory Status */}
      <div className="glass-panel p-4">
        <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">UNIFIED MEMORY (RAM)</div>
        <div className="text-lg font-bold text-slate-100 mono">
          {system.ram_total_gb} GB Total
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>Available Headroom:</span>
          <span className="mono text-cyan-300">
            {typeof system.ram_available_gb === 'number' ? `${system.ram_available_gb} GB` : system.ram_available_gb}
          </span>
        </div>
        <div className="text-xs text-slate-400 mt-1 flex justify-between">
          <span>Recommended Model:</span>
          <span className="mono text-slate-300">Qwen 2.5 7B (~4.7 GB)</span>
        </div>
      </div>

      {/* 3. SQLite Database Status */}
      <div className="glass-panel p-4">
        <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">PERSISTENT STORAGE</div>
        <div className="text-lg font-bold flex items-center gap-2">
          <span className="text-slate-100">SQLite Local</span>
          <span className="badge-tag mono uppercase">{database.journal_mode} MODE</span>
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>Database Integrity:</span>
          <span className={`mono font-semibold ${database.status === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}`}>
            {database.status}
          </span>
        </div>
        <div className="text-xs text-slate-400 mt-1 truncate" title={database.path}>
          Path: <span className="mono text-slate-300">{database.path}</span>
        </div>
      </div>

      {/* 4. Guardian Security Protocol */}
      <div className="glass-panel p-4">
        <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">CYRUS GUARDIAN</div>
        <div className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <span>Level 1 to 4</span>
          <span className="badge-tag mono">ENFORCED</span>
        </div>
        <div className="text-xs text-slate-400 mt-2 flex justify-between">
          <span>Sandbox Boundary:</span>
          <span className="mono text-emerald-400">~/Downloads/CYRUS</span>
        </div>
        <div className="text-xs text-slate-400 mt-1 flex justify-between">
          <span>Audit Ledger:</span>
          <span className="mono text-cyan-300">Append-Only Active</span>
        </div>
      </div>
    </div>
  );
};
