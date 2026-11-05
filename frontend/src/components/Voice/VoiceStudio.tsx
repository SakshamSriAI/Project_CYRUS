import React, { useState, useEffect, useRef } from 'react';

interface VoiceOption {
  voice_id: string;
  name: string;
  gender: string;
  accent: string;
  description: string;
  is_default: boolean;
}

export const VoiceStudio: React.FC = () => {
  // Voice Settings State
  const [selectedVoice, setSelectedVoice] = useState('am_puck');
  const [speechSpeed, setSpeechSpeed] = useState(1.0);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [engineStatus, setEngineStatus] = useState('KOKORO_NEURAL_ONLINE');

  // Audition State
  const [auditionText, setAuditionText] = useState(
    'Good day, Sir. All systems are operational. I am running natively on your MacBook Air.'
  );
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [feedback, setFeedback] = useState('');

  // Mic Test State
  const [isMicTesting, setIsMicTesting] = useState(false);
  const [micVolume, setMicVolume] = useState(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // 1. Fetch Studio Config on Mount
  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/v1/voice/studio/config');
      if (res.ok) {
        const data = await res.json();
        setSelectedVoice(data.active_voice_id || 'am_puck');
        setSpeechSpeed(data.active_speed || 1.0);
        setVoiceEnabled(data.voice_enabled !== false);
        setVoices(data.voices || []);
        setEngineStatus(data.engine_status || 'KOKORO_NEURAL_ONLINE');
      }
    } catch {
      // Ignored
    }
  };

  useEffect(() => {
    fetchConfig();
    return () => {
      stopMicTest();
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // 2. Save Persistent Preferences
  const savePreferences = async (newVoice?: string, newSpeed?: number, newEnabled?: boolean) => {
    const v = newVoice !== undefined ? newVoice : selectedVoice;
    const s = newSpeed !== undefined ? newSpeed : speechSpeed;
    const e = newEnabled !== undefined ? newEnabled : voiceEnabled;

    try {
      const res = await fetch('/api/v1/voice/studio/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: v, speed: s, voice_enabled: e }),
      });
      if (res.ok) {
        setFeedback('Voice preferences saved to persistent SQLite memory.');
        setTimeout(() => setFeedback(''), 4000);
      }
    } catch {
      setFeedback('Failed to persist preferences.');
    }
  };

  // 3. Puck Signature Preview
  const handlePuckPreview = async () => {
    setIsSynthesizing(true);
    setFeedback('Generating Puck (am_puck) signature preview...');
    try {
      const res = await fetch('/api/v1/voice/studio/preview', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.audio_url) {
        setAudioUrl(data.audio_url);
        playAudio(data.audio_url);
        setFeedback('Playing Puck (am_puck) signature preview.');
      } else {
        setFeedback('Failed to generate preview.');
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  // 4. Custom Audition
  const handleAudition = async () => {
    if (!auditionText.trim()) return;
    setIsSynthesizing(true);
    setFeedback(`Synthesizing with ${selectedVoice} at ${speechSpeed}x speed...`);
    try {
      const res = await fetch('/api/v1/voice/studio/audition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: auditionText.trim(),
          voice_id: selectedVoice,
          speed: speechSpeed,
        }),
      });
      const data = await res.json();
      if (res.ok && data.audio_url) {
        setAudioUrl(data.audio_url);
        playAudio(data.audio_url);
        setFeedback(`Audition ready (${data.duration_seconds}s). Playing now.`);
      } else {
        setFeedback('Audition synthesis failed.');
      }
    } catch (err: any) {
      setFeedback(`Error: ${err.message}`);
    } finally {
      setIsSynthesizing(false);
    }
  };

  // Audio Playback Controls
  const playAudio = (url: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.playbackRate = speechSpeed;

    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => {
      setIsPlaying(false);
      setFeedback('Audio playback error.');
    };
    audio.play();
  };

  const togglePlayPause = () => {
    if (!audioRef.current) {
      if (audioUrl) playAudio(audioUrl);
      return;
    }
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleStopAudio = async () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    await fetch('/api/v1/voice/interrupt', { method: 'POST' }).catch(() => {});
    setFeedback('Playback stopped.');
  };

  // Microphone Testing
  const startMicTest = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      setIsMicTesting(true);

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      const micSource = audioCtx.createMediaStreamSource(stream);
      micSource.connect(analyser);
      analyser.fftSize = 64;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateVol = () => {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length;
        setMicVolume(Math.min(100, Math.round((avg / 128) * 100)));
        animFrameRef.current = requestAnimationFrame(updateVol);
      };
      updateVol();
    } catch (err: any) {
      setFeedback(`Microphone access error: ${err.message}`);
    }
  };

  const stopMicTest = () => {
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
    }
    setIsMicTesting(false);
    setMicVolume(0);
  };

  return (
    <div className="glass-panel p-5 mb-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span>CYRUS Voice Studio</span>
              <span className="badge-tag mono text-cyan-300 border-cyan-500/40">KOKORO TTS</span>
            </h2>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/50 mono">
              DEFAULT: PUCK (am_puck)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Local 24 kHz Neural Synthesis • Natural Conversational Personality • Persistent Settings
          </p>
        </div>

        {/* Global Voice Enable Toggle & Engine Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300">{engineStatus}</span>
          </div>

          <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
            <input
              type="checkbox"
              checked={voiceEnabled}
              onChange={(e) => {
                setVoiceEnabled(e.target.checked);
                savePreferences(undefined, undefined, e.target.checked);
              }}
              className="rounded bg-slate-900 border-slate-700 text-cyan-400 focus:ring-0"
            />
            <span>Voice Enabled</span>
          </label>
        </div>
      </div>

      {feedback && (
        <div className="mt-3 p-2 rounded bg-cyan-950/40 border border-cyan-800/40 text-xs mono text-cyan-300">
          ℹ {feedback}
        </div>
      )}

      {/* Main Grid: Controls & Audition Studio */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-5">
        {/* Left Column: Voice Selection & Pacing Controls */}
        <div className="space-y-4">
          {/* Voice Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Selected Neural Voice
            </label>
            <div className="space-y-2">
              {voices.map((v) => (
                <div
                  key={v.voice_id}
                  onClick={() => {
                    setSelectedVoice(v.voice_id);
                    savePreferences(v.voice_id, undefined, undefined);
                  }}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedVoice === v.voice_id
                      ? 'bg-cyan-950/40 border-cyan-400 shadow-[0_0_15px_rgba(0,229,255,0.15)]'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-bold text-slate-100 flex items-center gap-1.5">
                      <span>{v.name.split(' ')[0]}</span>
                      <span className="mono text-[10px] text-cyan-400">({v.voice_id})</span>
                    </span>
                    {v.is_default && (
                      <span className="badge-tag mono text-[10px] text-emerald-400 border-emerald-800">
                        DEFAULT
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{v.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Speed Slider */}
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="font-semibold text-slate-300 uppercase tracking-wider">Conversational Speed</span>
              <span className="mono text-cyan-300 font-bold">{speechSpeed.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.75"
              max="1.50"
              step="0.05"
              value={speechSpeed}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                setSpeechSpeed(val);
                savePreferences(undefined, val, undefined);
              }}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mono mt-0.5">
              <span>0.75x (Calm/Slow)</span>
              <span>1.0x (Puck Standard)</span>
              <span>1.50x (Brisk)</span>
            </div>
          </div>

          {/* Quick Puck Signature Preview Button */}
          <div className="pt-2">
            <button
              onClick={handlePuckPreview}
              disabled={isSynthesizing}
              className="w-full btn-cyrus justify-center py-2.5 font-semibold text-xs tracking-wide"
            >
              ▶ Listen to Puck (am_puck) Preview
            </button>
          </div>

          {/* Microphone Test Widget */}
          <div className="pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-semibold text-slate-300 uppercase tracking-wider">Microphone Test</span>
              <button
                onClick={isMicTesting ? stopMicTest : startMicTest}
                className={`text-[11px] px-2 py-0.5 rounded font-mono ${
                  isMicTesting
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {isMicTesting ? 'Stop Test' : 'Test Mic'}
              </button>
            </div>

            {isMicTesting && (
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden mb-1">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-75"
                    style={{ width: `${micVolume}%` }}
                  />
                </div>
                <div className="text-[10px] text-slate-400 mono text-right">Input Level: {micVolume}%</div>
              </div>
            )}
          </div>
        </div>

        {/* Right 2 Columns: Custom Audition & Audio Player */}
        <div className="lg:col-span-2 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Custom Text Audition (Test Any Phrase)
            </label>
            <textarea
              value={auditionText}
              onChange={(e) => setAuditionText(e.target.value)}
              rows={4}
              placeholder="Type any sentence here to hear CYRUS speak in the Puck voice..."
              className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 leading-relaxed font-sans"
            />
          </div>

          {/* Audition Preset Buttons */}
          <div className="flex flex-wrap gap-2 text-[11px]">
            <button
              onClick={() =>
                setAuditionText(
                  'Good morning, Sir. All systems are operational. I have reviewed your agenda for today. Shall we begin?'
                )
              }
              className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-300"
            >
              Preset: Morning Briefing
            </button>
            <button
              onClick={() =>
                setAuditionText(
                  'I ran the unit test suite across all modules. 45 tests passed in 0.14 seconds with zero memory leaks.'
                )
              }
              className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-300"
            >
              Preset: Technical Dev Report
            </button>
            <button
              onClick={() =>
                setAuditionText(
                  'Certainly, Sir. I will remember that preference and apply it to all future sessions.'
                )
              }
              className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-300"
            >
              Preset: Memory Confirmation
            </button>
          </div>

          {/* Action Row */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={handleAudition}
              disabled={isSynthesizing || !auditionText.trim()}
              className="btn-cyrus px-6 py-2.5 font-semibold text-xs tracking-wide"
            >
              {isSynthesizing ? 'Synthesizing Audio...' : '⚡ Generate & Audition Voice'}
            </button>

            {audioUrl && (
              <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
                <button
                  onClick={togglePlayPause}
                  className="btn-cyrus text-xs py-2 px-3"
                  title="Play / Pause current audio"
                >
                  {isPlaying ? '⏸ Pause' : '▶ Play'}
                </button>
                <button
                  onClick={handleStopAudio}
                  className="btn-cyrus btn-cyrus-danger text-xs py-2 px-3"
                  title="Stop playback"
                >
                  ⏹ Stop
                </button>
                <a
                  href={audioUrl}
                  download="cyrus_puck_voice.wav"
                  className="px-3 py-2 rounded text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 mono"
                  title="Download sharable 24kHz audio file"
                >
                  ⬇ Download WAV
                </a>
              </div>
            )}
          </div>

          {/* Puck Personality Profile Card */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900/90 to-cyan-950/30 border border-cyan-800/30 mt-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-300 mb-2">
              Puck (`am_puck`) Personality Characteristics
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="flex items-start gap-2">
                <span className="text-cyan-400">✓</span>
                <span className="text-slate-300">Natural & Conversational (Human pacing, no robotic drone)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-400">✓</span>
                <span className="text-slate-300">Warm & Approachable (Engaging, personal companion)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-400">✓</span>
                <span className="text-slate-300">Intelligent & Articulate (Phonetic accuracy on CS terms)</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-400">✓</span>
                <span className="text-slate-300">Calm & Composed (Confident without being aggressive)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
