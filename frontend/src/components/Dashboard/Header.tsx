import React, { useState, useEffect } from 'react';

interface HeaderProps {
  appName: string;
  version: string;
  status: string;
  lifecycleState: string;
}

export const Header: React.FC<HeaderProps> = ({ appName, version, status, lifecycleState }) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="glass-panel p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-400/40 flex items-center justify-center shadow-lg shadow-cyan-500/10">
            <span className="text-2xl font-bold tracking-wider text-cyan-300">C</span>
          </div>
          <div className="absolute -bottom-1 -right-1">
            <div className={`w-3.5 h-3.5 rounded-full border-2 border-slate-900 ${
              status === 'ONLINE' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-amber-500 shadow-[0_0_8px_#f59e0b]'
            }`} />
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-wide text-slate-100">{appName}</h1>
            <span className="badge-tag mono">v{version}</span>
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/50">
              OWNER: SAKSHAM
            </span>
          </div>
          <p className="text-xs text-slate-400">Cybernetic Yet Responsive Unified System • Local Operating Intelligence</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="text-xs text-slate-400 uppercase tracking-wider">SYSTEM STATE</div>
          <div className="mono font-semibold text-cyan-400 flex items-center justify-end gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            {lifecycleState}
          </div>
        </div>

        <div className="text-right pl-4 border-l border-slate-800">
          <div className="text-xs text-slate-400 uppercase tracking-wider">LOCAL TIME</div>
          <div className="mono font-medium text-slate-200">{time || '00:00:00'}</div>
        </div>
      </div>
    </header>
  );
};
