import React, { useState } from 'react';

export const LanguageIndicator: React.FC = () => {
  const [testInput, setTestInput] = useState('');
  const [detectedType, setDetectedType] = useState<string | null>(null);

  // Client-side visual tester mirroring backend language governance
  const analyzeInput = (text: string) => {
    setTestInput(text);
    if (!text.trim()) {
      setDetectedType(null);
      return;
    }
    // Check Devanagari regex
    if (/[\u0900-\u097F]/.test(text)) {
      setDetectedType('Hindi (Devanagari Script)');
      return;
    }
    // Hinglish keywords check
    const hinglishMarkers = ['aaj', 'kya', 'hai', 'karo', 'mujhe', 'batao', 'kaise', 'kab', 'mera', 'meri', 'karna', 'theek', 'shuru', 'bhai', 'yaar'];
    const words = text.toLowerCase().split(/\s+/);
    const hasMarker = words.some(w => hinglishMarkers.includes(w.replace(/[^a-z]/g, '')));
    if (hasMarker) {
      setDetectedType('Hinglish (Hindi in Latin Script)');
    } else {
      setDetectedType('English');
    }
  };

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
          <span>Centralized Language Policy</span>
          <span className="badge-tag mono">MANDATORY RULE</span>
        </h2>
        <span className="text-xs text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/50">
          OUTPUT: 100% ENGLISH ONLY
        </span>
      </div>

      <p className="text-xs text-slate-400 mb-4">
        You can speak or type to CYRUS in <strong>Hindi</strong>, <strong>Hinglish</strong>, or <strong>English</strong>. 
        CYRUS centrally guarantees every response, notification, and alert is delivered in clean English.
      </p>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Test Language Gate Comprehension:
          </label>
          <input
            type="text"
            value={testInput}
            onChange={(e) => analyzeInput(e.target.value)}
            placeholder="Try typing: 'CYRUS, aaj mera kya schedule hai?' or 'Website check karo'"
            className="w-full px-3 py-2 rounded-lg bg-slate-900/80 border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
        </div>

        {detectedType && (
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400">Detected Input Language:</span>
            <span className="mono font-semibold text-cyan-300">{detectedType}</span>
          </div>
        )}
      </div>
    </div>
  );
};
