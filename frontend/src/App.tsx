import React, { useEffect, useState } from 'react';
import { Header } from './components/Dashboard/Header';
import { SystemDiagnostics } from './components/Dashboard/SystemDiagnostics';
import { LifecycleControls } from './components/Dashboard/LifecycleControls';
import { LanguageIndicator } from './components/Dashboard/LanguageIndicator';
import { ChatCenter } from './components/Chat/ChatCenter';
import { VoiceCenter } from './components/Voice/VoiceCenter';
import { VoiceStudio } from './components/Voice/VoiceStudio';
import { SecurityCenter } from './components/Security/SecurityCenter';
import { MemoryCenter } from './components/Memory/MemoryCenter';
import { AgentCenter } from './components/Agents/AgentCenter';

interface HealthData {
  status: string;
  app_name: string;
  version: string;
  lifecycle_state: string;
  database: {
    status: string;
    journal_mode: string;
    path: string;
  };
  system: {
    ram_total_gb: number;
    ram_available_gb: number | string;
    ram_percent_used: number;
    cpu_percent: number;
  };
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Connecting to backend...');
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 4000);
    return () => clearInterval(interval);
  }, []);

  const defaultHealth: HealthData = {
    status: 'INITIALIZING',
    app_name: 'CYRUS (Cybernetic Yet Responsive Unified System)',
    version: '0.1.0',
    lifecycle_state: 'ACTIVE',
    database: {
      status: 'HEALTHY',
      journal_mode: 'WAL',
      path: 'data/cyrus.db',
    },
    system: {
      ram_total_gb: 16.0,
      ram_available_gb: 11.2,
      ram_percent_used: 30.0,
      cpu_percent: 4.5,
    },
  };

  const activeData = health || defaultHealth;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 min-h-screen">
      <Header
        appName={activeData.app_name}
        version={activeData.version}
        status={health ? activeData.status : 'CONNECTING'}
        lifecycleState={activeData.lifecycle_state}
      />

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-amber-950/40 border border-amber-800/50 text-xs mono text-amber-300 flex items-center justify-between">
          <span>Backend Polling Notice: {error} (Backend server will connect once started)</span>
          <button onClick={fetchHealth} className="px-2 py-1 rounded bg-amber-900/60 text-amber-200 text-xs hover:bg-amber-800">
            Retry
          </button>
        </div>
      )}

      {/* Main Conversation & Intelligence Center */}
      <ChatCenter />

      {/* CYRUS VOICE Center */}
      <VoiceCenter />

      {/* CYRUS VOICE STUDIO (Kokoro TTS & Puck Voice) */}
      <VoiceStudio />

      {/* CYRUS MEMORY Center */}
      <MemoryCenter />

      {/* CYRUS AGENT Center (Phase 6 Specialist Agents) */}
      <AgentCenter />

      {/* CYRUS GUARDIAN Security Center */}
      <SecurityCenter />

      {/* Diagnostics and Telemetry */}
      <SystemDiagnostics
        system={activeData.system}
        database={activeData.database}
      />

      {/* Deterministic Lifecycle Bar */}
      <LifecycleControls
        currentState={activeData.lifecycle_state}
        onStateChange={(newState) => {
          if (health) setHealth({ ...health, lifecycle_state: newState });
        }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LanguageIndicator />

        {/* Phase 2 Architecture Card */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>CYRUS CORE & Local AI</span>
              <span className="badge-tag mono">PHASE 2</span>
            </h2>
            <span className="text-xs text-cyan-400 font-semibold px-2 py-0.5 rounded bg-cyan-950/40 border border-cyan-800/50">
              OPERATIONAL
            </span>
          </div>

          <p className="text-xs text-slate-400 mb-3">
            CYRUS CORE manages conversational context, detects input language, routes prompts to the local LLM, verifies 100% English responses, and persists all history to SQLite.
          </p>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded bg-slate-900/40 border border-slate-800">
              <span className="text-slate-300">Local LLM Interface (Ollama)</span>
              <span className="mono text-cyan-400">Integrated (`qwen2.5:7b-instruct`)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-900/40 border border-slate-800">
              <span className="text-slate-300">Language Policy Enforcer</span>
              <span className="mono text-emerald-400">Active (Devanagari Guard Enforced)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-900/40 border border-slate-800">
              <span className="text-slate-300">Session & Message Persistence</span>
              <span className="mono text-emerald-400">Active (SQLite WAL Logged)</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-slate-900/40 border border-slate-800">
              <span className="text-slate-300">Security Audit Trail</span>
              <span className="mono text-emerald-400">Append-Only `audit_logs` Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
