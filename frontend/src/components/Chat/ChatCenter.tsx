import React, { useState, useEffect, useRef } from 'react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  detected_language?: string;
  timestamp: string;
  model_used?: string;
}

export const ChatCenter: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<{ connected: boolean; models: string[] }>({
    connected: false,
    models: [],
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check Ollama status
  const checkOllama = async () => {
    try {
      const res = await fetch('/api/v1/chat/models');
      if (res.ok) {
        const data = await res.json();
        setOllamaStatus({
          connected: data.connected || false,
          models: data.available_models || [],
        });
      }
    } catch {
      setOllamaStatus({ connected: false, models: [] });
    }
  };

  useEffect(() => {
    checkOllama();
    const interval = setInterval(checkOllama, 8000);
    return () => clearInterval(interval);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || isLoading) return;

    const tempUserMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    if (!textToSend) setInputText('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMsg: ChatMessage = {
        id: `assist-${Date.now()}`,
        role: 'assistant',
        content: data.response,
        detected_language: data.detected_language,
        timestamp: new Date().toLocaleTimeString(),
        model_used: data.model_used,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error: Unable to connect to CYRUS CORE backend (${err.message}). Please ensure the backend is running.`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    'Good morning, CYRUS.',
    'CYRUS, aaj mera schedule kya hai?',
    'CYRUS, check my business.',
    'CYRUS, what is happening with our website?',
    'CYRUS, help me build an application.',
    'Mujhe batao website mein kya problem hai.',
  ];

  return (
    <div className="glass-panel p-5 flex flex-col h-[560px] mb-6">
      {/* Chat Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_#00e5ff]" />
          <div>
            <h2 className="text-base font-bold text-slate-100">CYRUS Conversation Center</h2>
            <p className="text-xs text-slate-400">
              Multilingual Input (English, Hindi, Hinglish) • Strictly English Responses
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                ollamaStatus.connected ? 'bg-emerald-400' : 'bg-amber-400'
              }`}
            />
            <span className="mono text-slate-300">
              {ollamaStatus.connected
                ? `Ollama: ${ollamaStatus.models.length} model(s)`
                : 'Ollama: Local Baseline'}
            </span>
          </div>

          {sessionId && (
            <span className="badge-tag mono text-[10px]" title={sessionId}>
              {sessionId.slice(0, 14)}...
            </span>
          )}
        </div>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-6">
            <div className="w-12 h-12 rounded-full bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-300 mb-3 text-lg">
              ⚡
            </div>
            <h3 className="text-sm font-semibold text-slate-200">CYRUS CORE is Ready</h3>
            <p className="text-xs text-slate-400 max-w-md mt-1">
              Speak or type to CYRUS in Hindi, Hinglish, or English. All intelligence outputs are delivered exclusively in fluent English.
            </p>

            {/* Quick Prompts */}
            <div className="mt-4 flex flex-wrap justify-center gap-2 max-w-lg">
              {quickPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(prompt)}
                  className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs text-cyan-300 transition-colors"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1 text-[11px] text-slate-400">
                <span className="font-semibold text-slate-300">
                  {msg.role === 'user' ? 'Saksham' : 'CYRUS'}
                </span>
                <span className="mono">{msg.timestamp}</span>
                {msg.detected_language && (
                  <span className="badge-tag text-[10px]">
                    Input: {msg.detected_language}
                  </span>
                )}
                {msg.model_used && (
                  <span className="text-[10px] mono text-slate-500">
                    [{msg.model_used}]
                  </span>
                )}
              </div>

              <div
                className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-cyan-600/30 to-blue-600/30 border border-cyan-500/30 text-slate-100'
                    : 'bg-slate-900/90 border border-slate-800 text-slate-200 shadow-lg'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-2 mb-1 text-[11px] text-slate-400">
              <span className="font-semibold text-cyan-400">CYRUS</span>
              <span className="mono text-slate-500">Processing...</span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl px-4 py-3 text-xs mono text-cyan-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              CYRUS CORE is reasoning and enforcing language governance...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="pt-3 border-t border-slate-800 flex gap-2"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask CYRUS anything in English, Hindi, or Hinglish..."
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
        />
        <button
          type="submit"
          disabled={isLoading || !inputText.trim()}
          className="btn-cyrus px-5"
        >
          Send
        </button>
      </form>
    </div>
  );
};
