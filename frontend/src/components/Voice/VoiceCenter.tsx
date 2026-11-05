import React, { useState, useEffect, useRef } from 'react';

type VoiceState = 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING';

export const VoiceCenter: React.FC = () => {
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [lastResponse, setLastResponse] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState('Daniel');
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true);
  const [feedback, setFeedback] = useState('');

  const recognitionRef = useRef<any>(null);

  // Initialize Speech Recognition if supported
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-IN'; // Multilingual Indian English / Hindi recognition

      recognition.onstart = () => {
        setVoiceState('LISTENING');
        setFeedback('Listening... Speak in English, Hindi, or Hinglish.');
      };

      recognition.onresult = async (event: any) => {
        const spokenText = event.results[0][0].transcript;
        setTranscript(spokenText);
        setVoiceState('PROCESSING');
        setFeedback(`Captured: "${spokenText}". Processing through CYRUS CORE...`);

        // Send to backend voice pipeline
        await processVoiceInput(spokenText);
      };

      recognition.onerror = (event: any) => {
        setVoiceState('IDLE');
        setFeedback(`Audio error: ${event.error || 'Recognition stopped'}`);
      };

      recognition.onend = () => {
        if (voiceState === 'LISTENING') {
          setVoiceState('IDLE');
        }
      };

      recognitionRef.current = recognition;
    } else {
      setFeedback('Note: Web Speech API is not supported in this browser. You can test voice via API.');
    }

    return () => {
      // Hardware safety release
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const processVoiceInput = async (spokenText: string) => {
    try {
      const res = await fetch('/api/v1/voice/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: spokenText,
          voice: selectedVoice,
          speak_on_mac: false,
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setLastResponse(data.response_text);
        setDetectedLanguage(data.detected_language);
        setFeedback(`Understood (${data.detected_language} input). Speaking English response...`);

        // Speak response using local Web Speech API
        speakResponse(data.response_text);
      } else {
        setVoiceState('IDLE');
        setFeedback(`Error: ${data.error || 'Failed to process voice'}`);
      }
    } catch (err: any) {
      setVoiceState('IDLE');
      setFeedback(`Voice pipeline error: ${err.message}`);
    }
  };

  const speakResponse = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      setVoiceState('SPEAKING');

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.lang = 'en-US';

      // Select voice if available
      const voices = window.speechSynthesis.getVoices();
      const match = voices.find(
        (v) => v.name.toLowerCase().includes(selectedVoice.toLowerCase()) || v.lang.startsWith('en')
      );
      if (match) utterance.voice = match;

      utterance.onend = () => {
        setVoiceState('IDLE');
        setFeedback('Voice interaction turn complete. Ready for next command.');
      };

      utterance.onerror = () => {
        setVoiceState('IDLE');
      };

      window.speechSynthesis.speak(utterance);
    } else {
      setVoiceState('IDLE');
    }
  };

  const toggleListening = () => {
    if (voiceState === 'LISTENING') {
      recognitionRef.current?.stop();
      setVoiceState('IDLE');
      setFeedback('Microphone hardware released.');
    } else if (voiceState === 'SPEAKING') {
      interruptSpeech();
    } else {
      try {
        recognitionRef.current?.start();
      } catch (e) {
        setFeedback('Click again to start microphone.');
      }
    }
  };

  const interruptSpeech = async () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    // Also notify backend
    await fetch('/api/v1/voice/interrupt', { method: 'POST' }).catch(() => {});
    setVoiceState('IDLE');
    setFeedback('Speech output interrupted by user.');
  };

  // Test simulation for environments without microphone access
  const simulateVoicePrompt = (testPrompt: string) => {
    setTranscript(testPrompt);
    setVoiceState('PROCESSING');
    setFeedback(`Simulating spoken input: "${testPrompt}"...`);
    processVoiceInput(testPrompt);
  };

  return (
    <div className="glass-panel p-5 mb-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100">CYRUS VOICE Interaction Center</h2>
            <span className="badge-tag mono">LOCAL & ₹0 BUDGET</span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Speech-to-Text (Hindi/Hinglish/English) • 100% English Natural Spoken Responses • Transparent Mic Control
          </p>
        </div>

        {/* Voice Selector & Controls */}
        <div className="flex items-center gap-3">
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          >
            <option value="Daniel">Daniel (UK English - Sophisticated)</option>
            <option value="Samantha">Samantha (US English - Natural)</option>
            <option value="Karen">Karen (AU English - Articulate)</option>
          </select>

          {voiceState === 'SPEAKING' && (
            <button onClick={interruptSpeech} className="btn-cyrus btn-cyrus-danger text-xs py-1.5">
              ⏹ Interrupt
            </button>
          )}
        </div>
      </div>

      {/* Visualizer & Interaction Core */}
      <div className="py-6 flex flex-col items-center justify-center">
        {/* Animated Visualizer Orb */}
        <div className="relative mb-5">
          <button
            onClick={toggleListening}
            className={`w-28 h-28 rounded-full flex flex-col items-center justify-center transition-all duration-300 cursor-pointer shadow-2xl ${
              voiceState === 'LISTENING'
                ? 'bg-rose-950/80 border-2 border-rose-500 shadow-[0_0_35px_rgba(244,63,94,0.6)] animate-pulse'
                : voiceState === 'SPEAKING'
                ? 'bg-cyan-950/80 border-2 border-cyan-400 shadow-[0_0_35px_rgba(0,229,255,0.6)]'
                : voiceState === 'PROCESSING'
                ? 'bg-amber-950/80 border-2 border-amber-400 shadow-[0_0_35px_rgba(245,158,11,0.5)]'
                : 'bg-slate-900/90 border border-cyan-500/30 hover:border-cyan-400 hover:shadow-[0_0_20px_rgba(0,229,255,0.3)]'
            }`}
            title="Click to activate / deactivate microphone"
          >
            <div className="text-2xl mb-1">
              {voiceState === 'LISTENING' ? '🎙️' : voiceState === 'SPEAKING' ? '🔊' : voiceState === 'PROCESSING' ? '⚡' : '🎤'}
            </div>
            <span className="mono text-[10px] font-bold tracking-wider uppercase text-slate-200">
              {voiceState}
            </span>
          </button>

          {/* Outer Pulsing Ring */}
          {voiceState === 'LISTENING' && (
            <div className="absolute inset-0 rounded-full border border-rose-400 animate-ping pointer-events-none" />
          )}
          {voiceState === 'SPEAKING' && (
            <div className="absolute inset-0 rounded-full border border-cyan-400 animate-ping pointer-events-none" />
          )}
        </div>

        <p className="text-xs text-slate-300 font-medium mb-1">
          {voiceState === 'LISTENING'
            ? 'Listening... Speak in Hindi, Hinglish, or English'
            : voiceState === 'SPEAKING'
            ? 'CYRUS is speaking in English...'
            : voiceState === 'PROCESSING'
            ? 'Reasoning and enforcing English speech policy...'
            : 'Click the orb or use Push-to-Talk to speak to CYRUS'}
        </p>

        <p className="text-[11px] mono text-slate-500 mb-4">{feedback}</p>

        {/* Quick Voice Simulation Buttons (for fast testing) */}
        <div className="flex flex-wrap justify-center gap-2 max-w-xl">
          <button
            onClick={() => simulateVoicePrompt('Good morning, CYRUS.')}
            className="px-2.5 py-1 rounded bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-cyan-300"
          >
            Spoken [English]: "Good morning, CYRUS."
          </button>
          <button
            onClick={() => simulateVoicePrompt('CYRUS, aaj mera schedule kya hai?')}
            className="px-2.5 py-1 rounded bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-cyan-300"
          >
            Spoken [Hinglish]: "CYRUS, aaj mera schedule kya hai?"
          </button>
          <button
            onClick={() => simulateVoicePrompt('Mujhe batao website mein kya problem hai.')}
            className="px-2.5 py-1 rounded bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-cyan-300"
          >
            Spoken [Hinglish]: "Mujhe batao website..."
          </button>
        </div>
      </div>

      {/* Transcript & Response Display */}
      {(transcript || lastResponse) && (
        <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span>Transcribed Speech:</span>
              {detectedLanguage && <span className="badge-tag text-[10px]">Input: {detectedLanguage}</span>}
            </div>
            <p className="text-slate-100 font-medium">"{transcript}"</p>
          </div>

          <div className="p-3 rounded-lg bg-slate-900/60 border border-cyan-800/40">
            <div className="flex items-center justify-between text-cyan-400 mb-1">
              <span>CYRUS Spoken Response:</span>
              <span className="badge-tag mono text-[10px] text-emerald-400 border-emerald-800">100% English</span>
            </div>
            <p className="text-slate-100 leading-relaxed font-medium">"{lastResponse}"</p>
          </div>
        </div>
      )}
    </div>
  );
};
