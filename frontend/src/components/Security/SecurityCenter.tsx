import React, { useState, useEffect } from 'react';

interface ApprovalRequest {
  id: string;
  actor: string;
  action_type: string;
  target_resource: string;
  consequence_summary: string;
  status: string;
  created_at: string;
  expires_at: string;
}

interface AuditLog {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  target_resource: string;
  risk_level: number;
  decision: string;
}

export const SecurityCenter: React.FC = () => {
  const [isHalted, setIsHalted] = useState(false);
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [actionMessage, setActionMessage] = useState('');

  const fetchSecurityData = async () => {
    try {
      // 1. Fetch Guardian status
      const statusRes = await fetch('/api/v1/guardian/status');
      if (statusRes.ok) {
        const sData = await statusRes.json();
        setIsHalted(sData.emergency_halted || false);
      }

      // 2. Fetch pending approvals
      const appRes = await fetch('/api/v1/guardian/approvals/pending');
      if (appRes.ok) {
        const aData = await appRes.json();
        setApprovals(aData.requests || []);
      }

      // 3. Fetch audit logs
      const auditRes = await fetch('/api/v1/guardian/audit/logs?limit=8');
      if (auditRes.ok) {
        const lData = await auditRes.json();
        setAuditLogs(lData.logs || []);
      }
    } catch {
      // Handled silently
    }
  };

  useEffect(() => {
    fetchSecurityData();
    const interval = setInterval(fetchSecurityData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (reqId: string, approve: boolean) => {
    setActionMessage('');
    try {
      const endpoint = approve ? 'approve' : 'reject';
      const res = await fetch(`/api/v1/guardian/approvals/${reqId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: `Decision made via Security Center by Saksham` }),
      });
      const data = await res.json();
      if (res.ok) {
        setActionMessage(`Action ${approve ? 'APPROVED' : 'REJECTED'} successfully.`);
        fetchSecurityData();
      } else {
        setActionMessage(`Error: ${data.detail || 'Failed'}`);
      }
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`);
    }
  };

  const handleEmergencyStop = async () => {
    try {
      const res = await fetch('/api/v1/guardian/emergency-stop', { method: 'POST' });
      if (res.ok) {
        setIsHalted(true);
        setActionMessage('CYRUS STOP ACTIVATED: All active processes and task queues have been terminated.');
        fetchSecurityData();
      }
    } catch (err: any) {
      setActionMessage(`Failed to trigger Emergency Stop: ${err.message}`);
    }
  };

  const handleResetStop = async () => {
    try {
      const res = await fetch('/api/v1/guardian/reset-stop', { method: 'POST' });
      if (res.ok) {
        setIsHalted(false);
        setActionMessage('Emergency Stop reset. System restored to ACTIVE state.');
        fetchSecurityData();
      }
    } catch (err: any) {
      setActionMessage(`Failed to reset: ${err.message}`);
    }
  };

  return (
    <div className="glass-panel p-5 mb-6">
      {/* Header & Kill Switch Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100">CYRUS GUARDIAN Security Center</h2>
            <span className={`badge-tag mono ${isHalted ? 'bg-rose-950/80 text-rose-400 border-rose-800' : 'bg-emerald-950/80 text-emerald-400 border-emerald-800'}`}>
              {isHalted ? 'EMERGENCY HALTED' : 'SYSTEM PROTECTED'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            4-Tier Permission Boundary • Interactive Human-in-the-Loop Approvals • Append-Only Audit Ledger
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isHalted ? (
            <button
              onClick={handleResetStop}
              className="btn-cyrus bg-emerald-950/60 text-emerald-300 border-emerald-500/50 hover:bg-emerald-900/60"
            >
              ✓ Reset Emergency Stop
            </button>
          ) : (
            <button
              onClick={handleEmergencyStop}
              className="btn-cyrus btn-cyrus-danger font-bold tracking-wider"
              title="Immediately freezes tasks, terminates CYRUS processes, and revokes tokens"
            >
              🛑 CYRUS STOP (Emergency Halt)
            </button>
          )}
        </div>
      </div>

      {actionMessage && (
        <div className="mt-3 p-2.5 rounded bg-cyan-950/50 border border-cyan-800/40 text-xs mono text-cyan-300">
          ℹ {actionMessage}
        </div>
      )}

      {/* Main Grid: Pending Approvals & Live Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-5">
        {/* Pending Approvals Queue */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <span>Pending Action Approvals</span>
              <span className="mono text-xs px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-800/40">
                {approvals.length}
              </span>
            </h3>
            <span className="text-[11px] text-slate-400">Level 4 Restricted</span>
          </div>

          {approvals.length === 0 ? (
            <div className="p-6 rounded-lg bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
              ✓ No pending Level 4 operations. All background and tool actions are within authorized limits.
            </div>
          ) : (
            <div className="space-y-3">
              {approvals.map((req) => (
                <div key={req.id} className="p-3.5 rounded-lg bg-slate-900/80 border border-amber-700/40 shadow-lg">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="mono font-semibold text-amber-300">{req.action_type.toUpperCase()}</span>
                    <span className="text-slate-400 text-[11px] mono">Expires: {new Date(req.expires_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-xs text-slate-300 mb-1">
                    Target: <span className="mono text-cyan-300">{req.target_resource}</span>
                  </div>
                  <div className="text-xs text-slate-400 mb-3 bg-slate-950/60 p-2 rounded border border-slate-800">
                    {req.consequence_summary}
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => handleResolve(req.id, false)}
                      className="px-3 py-1 rounded text-xs bg-rose-950/60 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50"
                    >
                      ✕ Reject
                    </button>
                    <button
                      onClick={() => handleResolve(req.id, true)}
                      className="px-3 py-1 rounded text-xs bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/50 font-semibold"
                    >
                      ✓ Authorize Execution
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Audit Log Ledger */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200">Security Audit Ledger</h3>
            <span className="text-[11px] mono text-slate-400">Append-Only SQLite</span>
          </div>

          <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
            {auditLogs.length === 0 ? (
              <div className="p-6 rounded-lg bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-400">
                Audit logs are loading...
              </div>
            ) : (
              auditLogs.map((log) => (
                <div key={log.id} className="p-2.5 rounded bg-slate-900/50 border border-slate-800/80 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="mono font-semibold text-slate-200">{log.action}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        log.decision === 'ALLOWED' || log.decision === 'APPROVED_BY_USER'
                          ? 'bg-emerald-950/60 text-emerald-400'
                          : log.decision === 'HALTED'
                          ? 'bg-rose-950/80 text-rose-300'
                          : 'bg-amber-950/60 text-amber-300'
                      }`}>
                        {log.decision}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-[280px]">
                      {log.target_resource}
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="badge-tag mono text-[10px]">Tier L{log.risk_level}</span>
                    <div className="text-[10px] text-slate-500 mono mt-0.5">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
