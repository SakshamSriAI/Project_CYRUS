import React, { useState } from 'react';

interface LifecycleControlsProps {
  currentState: string;
  onStateChange: (newState: string) => void;
}

export const LifecycleControls: React.FC<LifecycleControlsProps> = ({ currentState, onStateChange }) => {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string>('');

  const triggerLifecycle = async (action: 'pause' | 'resume' | 'exam-mode') => {
    setLoadingAction(action);
    setMessage('');
    try {
      const res = await fetch(`/api/v1/system/lifecycle/${action}`, { method: 'POST' });
      const data = await res.json();
      setMessage(data.message || 'Operation successful');
      if (action === 'pause') onStateChange('PAUSED');
      if (action === 'resume') onStateChange('ACTIVE');
      if (action === 'exam-mode') onStateChange('EXAM_MODE');
    } catch (err) {
      setMessage(`Failed: ${err}`);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="glass-panel p-5 mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Deterministic Lifecycle Controls</span>
            <span className="text-xs font-normal text-slate-400">
              (Current: <strong className="text-cyan-400 mono">{currentState}</strong>)
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            CYRUS manages its own processes cleanly. Full session state is checkpointed in SQLite before transitions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {currentState === 'PAUSED' ? (
            <button
              onClick={() => triggerLifecycle('resume')}
              disabled={loadingAction !== null}
              className="btn-cyrus"
            >
              ▶ Resume CYRUS
            </button>
          ) : (
            <button
              onClick={() => triggerLifecycle('pause')}
              disabled={loadingAction !== null || currentState === 'EXAM_MODE'}
              className="btn-cyrus"
            >
              ⏸ Pause System
            </button>
          )}

          <button
            onClick={() => triggerLifecycle('exam-mode')}
            disabled={loadingAction !== null || currentState === 'EXAM_MODE'}
            className="btn-cyrus btn-cyrus-danger"
            title="Halts all CYRUS background tasks, guarantees 0% CPU/RAM footprint for exams"
          >
            🛡️ Exam Mode (0% Footprint)
          </button>
        </div>
      </div>

      {message && (
        <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-800/40 text-xs mono text-cyan-300">
          ✓ {message}
        </div>
      )}
    </div>
  );
};
