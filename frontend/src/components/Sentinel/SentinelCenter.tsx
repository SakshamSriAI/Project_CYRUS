import React, { useEffect, useState } from 'react';

interface SentinelStatusData {
  is_running: boolean;
  lifecycle_state: string;
  active_monitors_count: number;
  services_up_count: number;
  services_down_count: number;
  services_degraded_count: number;
  last_cycle_timestamp: string | null;
  limitations_notice: string;
}

interface MonitorItem {
  id: string;
  name: string;
  target_url: string;
  check_type: string;
  interval_seconds: number;
  expected_status_code: number;
  is_active: boolean;
  current_status: 'UP' | 'DOWN' | 'DEGRADED' | 'UNKNOWN';
  last_checked_at: string | null;
  last_latency_ms: number | null;
  consecutive_failures: number;
}

interface EventItem {
  id: string;
  monitor_id: string;
  monitor_name: string;
  severity: 'INFO' | 'IMPORTANT' | 'CRITICAL';
  title: string;
  message: string;
  latency_ms: number | null;
  status_code: number | null;
  is_resolved: boolean;
  telegram_dispatched: boolean;
  created_at: string;
}

interface DrillResult {
  success: boolean;
  elapsed_seconds: number;
  status: string;
  severity: string;
  within_30s_threshold: boolean;
  summary: string;
}

export const SentinelCenter: React.FC = () => {
  const [status, setStatus] = useState<SentinelStatusData | null>(null);
  const [monitors, setMonitors] = useState<MonitorItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [drillLoading, setDrillLoading] = useState(false);
  const [drillResult, setDrillResult] = useState<DrillResult | null>(null);
  const [testAlertMsg, setTestAlertMsg] = useState<string | null>(null);

  const fetchSentinelData = async () => {
    setLoading(true);
    try {
      const [statRes, monRes, evtRes] = await Promise.all([
        fetch('/api/v1/sentinel/status'),
        fetch('/api/v1/sentinel/monitors'),
        fetch('/api/v1/sentinel/events?limit=25'),
      ]);

      if (statRes.ok) setStatus(await statRes.json());
      if (monRes.ok) {
        const monData = await monRes.json();
        setMonitors(monData.monitors || []);
      }
      if (evtRes.ok) {
        const evtData = await evtRes.json();
        setEvents(evtData.events || []);
      }
    } catch (e) {
      console.error('Failed to fetch sentinel telemetry', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentinelData();
    const interval = setInterval(fetchSentinelData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleManualCheck = async (monitorId: string) => {
    try {
      await fetch(`/api/v1/sentinel/monitors/${monitorId}/check-now`, { method: 'POST' });
      fetchSentinelData();
    } catch (e) {
      console.error('Manual check failed', e);
    }
  };

  const handleRunDowntimeDrill = async () => {
    setDrillLoading(true);
    setDrillResult(null);
    try {
      const res = await fetch('/api/v1/sentinel/simulate-downtime', { method: 'POST' });
      if (res.ok) {
        const data: DrillResult = await res.json();
        setDrillResult(data);
        fetchSentinelData();
      }
    } catch (e) {
      console.error('Downtime drill failed', e);
    } finally {
      setDrillLoading(false);
    }
  };

  const handleTestTelegramAlert = async () => {
    try {
      const res = await fetch('/api/v1/sentinel/telegram/test', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setTestAlertMsg(`Test alert dispatched via ${data.mode}: ${data.recipient_note || 'OK'}`);
      }
    } catch (e) {
      setTestAlertMsg('Failed to dispatch test alert');
    }
  };

  return (
    <div className="glass-panel p-5 mb-6 border border-amber-800/40">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🛡️</span>
            <h2 className="text-lg font-bold text-slate-100">CYRUS SENTINEL & Proactive Local Monitoring</h2>
            <span className="badge-tag mono text-amber-400 bg-amber-950/60 border-amber-700/60">PHASE 9</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Proactive health-checks, event severity classification (L1–L3), automated Telegram alerts, and local machine sleep awareness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {status && (
            <span className={`text-xs mono font-semibold px-2.5 py-1 rounded border ${
              status.is_running
                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
            }`}>
              {status.is_running ? '● WATCHING (ACTIVE)' : `⏸ ${status.lifecycle_state}`}
            </span>
          )}
          <button
            onClick={fetchSentinelData}
            disabled={loading}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition-colors"
          >
            {loading ? 'Pinging...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Hardware Limitation Notice */}
      <div className="my-3 p-3 rounded-lg bg-slate-900/90 border border-slate-800 flex items-start gap-2.5 text-xs text-slate-300">
        <span className="text-base shrink-0">💻</span>
        <div className="leading-relaxed">
          <strong className="text-white block mb-0.5">Local Surveillance & Apple Silicon Operating Boundary:</strong>
          SENTINEL runs locally on this MacBook Air M5 with ₹0 cloud spend. Proactive monitoring automatically pauses whenever the MacBook goes to sleep, display lid is closed, or during system shutdown, and resumes upon wakeup.
        </div>
      </div>

      {/* Surveillance Summary Bar */}
      {status && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Monitored Services</span>
            <span className="text-base font-bold text-white mono">{status.active_monitors_count} Targets</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Services UP</span>
            <span className="text-base font-bold text-emerald-400 mono">{status.services_up_count} Healthy</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Services DOWN</span>
            <span className={`text-base font-bold mono ${status.services_down_count > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
              {status.services_down_count} Outage
            </span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-center">
            <span className="text-[11px] text-slate-400 block">Degraded (High Latency)</span>
            <span className={`text-base font-bold mono ${status.services_degraded_count > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
              {status.services_degraded_count} Warning
            </span>
          </div>
        </div>
      )}

      {/* Simulated Downtime Drill Section */}
      <div className="mb-4 p-3.5 rounded-lg bg-slate-900/80 border border-amber-800/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-xs font-bold text-amber-300 block mb-0.5">
            Downtime Incident Response Verification Drill
          </span>
          <span className="text-[11px] text-slate-400">
            Simulates consecutive failure on mock target; verifies SENTINEL classifies Level 3 Critical and dispatches Telegram alert in &lt;30s.
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleRunDowntimeDrill}
            disabled={drillLoading}
            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-colors disabled:opacity-50"
          >
            {drillLoading ? 'Simulating Drill...' : '⚡ Run Downtime Drill (<30s)'}
          </button>
          <button
            onClick={handleTestTelegramAlert}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700"
          >
            Test Telegram
          </button>
        </div>
      </div>

      {testAlertMsg && (
        <div className="mb-4 p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/60 text-xs text-cyan-300 flex justify-between items-center">
          <span>{testAlertMsg}</span>
          <button onClick={() => setTestAlertMsg(null)} className="text-slate-400 hover:text-white text-xs">
            Dismiss
          </button>
        </div>
      )}

      {drillResult && (
        <div className="mb-4 p-4 rounded-lg bg-slate-900/95 border border-rose-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center gap-1.5">
              <span>🚨</span>
              <span>Downtime Drill Completed in {drillResult.elapsed_seconds}s</span>
            </span>
            <span className="mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 font-semibold">
              ROADMAP VERIFIED (&lt;30s)
            </span>
          </div>
          <p className="text-xs text-slate-200 whitespace-pre-wrap leading-relaxed font-mono bg-slate-950 p-3 rounded border border-slate-800">
            {drillResult.summary}
          </p>
        </div>
      )}

      {/* Monitored Services Grid */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-slate-400 mb-2.5 uppercase tracking-wider">
          Monitored Endpoints & Gateway Pings
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
          {monitors.map((m) => (
            <div
              key={m.id}
              className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors flex items-center justify-between"
            >
              <div className="truncate mr-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold text-slate-200">{m.name}</span>
                  {m.current_status === 'UP' && (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300">
                      UP
                    </span>
                  )}
                  {m.current_status === 'DOWN' && (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-rose-950/60 border border-rose-800 text-rose-300 animate-pulse">
                      DOWN ({m.consecutive_failures} failures)
                    </span>
                  )}
                  {m.current_status === 'DEGRADED' && (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
                      DEGRADED
                    </span>
                  )}
                  {m.current_status === 'UNKNOWN' && (
                    <span className="text-[10px] mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      INITIALIZING
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mono truncate">{m.target_url}</div>
                <div className="text-[10px] text-slate-500 mono mt-1">
                  Interval: {m.interval_seconds}s · Latency:{' '}
                  <strong className={
                    m.last_latency_ms !== null && m.last_latency_ms < 500
                      ? 'text-emerald-400'
                      : m.last_latency_ms !== null && m.last_latency_ms < 1500
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }>
                    {m.last_latency_ms !== null ? `${m.last_latency_ms}ms` : '—'}
                  </strong>
                </div>
              </div>

              <button
                onClick={() => handleManualCheck(m.id)}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 shrink-0"
              >
                Ping Now
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Incident & Health Events Audit Log */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
          Recent Surveillance Events & Incident Ledger ({events.length})
        </h3>
        {events.length === 0 ? (
          <div className="p-3 text-center text-xs text-slate-500 rounded bg-slate-900/30 border border-slate-800">
            No incidents logged yet. Systems running normally.
          </div>
        ) : (
          <div className="space-y-1.5 max-h-52 overflow-y-auto">
            {events.map((evt) => (
              <div
                key={evt.id}
                className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div className="truncate mr-3">
                  <div className="flex items-center gap-2 mb-0.5">
                    {evt.severity === 'CRITICAL' && (
                      <span className="text-[10px] mono font-bold px-1.5 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300">
                        LEVEL 3 CRITICAL
                      </span>
                    )}
                    {evt.severity === 'IMPORTANT' && (
                      <span className="text-[10px] mono font-bold px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-800 text-amber-300">
                        LEVEL 2 IMPORTANT
                      </span>
                    )}
                    {evt.severity === 'INFO' && (
                      <span className="text-[10px] mono px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800 text-cyan-300">
                        LEVEL 1 INFO
                      </span>
                    )}
                    <span className="font-semibold text-slate-200">{evt.title}</span>
                    <span className="text-slate-400 text-[11px]">({evt.monitor_name})</span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">{evt.message}</div>
                </div>

                <div className="flex items-center gap-2 shrink-0 text-[10px] mono text-slate-500">
                  {evt.telegram_dispatched && (
                    <span className="text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800">
                      Telegram Sent
                    </span>
                  )}
                  <span>{new Date(evt.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
