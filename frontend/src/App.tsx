import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { FailoverLab } from './components/FailoverLab';
import { Message, HealthStatus, SessionInfo, TelemetryStats } from './types';
import { fetchHealth, sendChatMessage, fetchSessionMessages } from './api';
import { Bot, Sparkles } from 'lucide-react';

function generateNewSessionId(): string {
  // Always generates a fresh unique session ID
  try {
    return `s-${crypto.randomUUID().slice(0, 8)}`;
  } catch {
    return `s-${Math.random().toString(36).substring(2, 10)}`;
  }
}

export const App: React.FC = () => {
  // On every fresh page load, ALWAYS generate a brand-new session_id and empty chat view
  const [currentSessionId, setCurrentSessionId] = useState<string>(generateNewSessionId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [systemPrompt, setSystemPrompt] = useState<string>('');
  const [activeSimulation, setActiveSimulation] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Health state
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);

  // Sidebar history & telemetry
  const [recentSessions, setRecentSessions] = useState<SessionInfo[]>(() => {
    try {
      const saved = localStorage.getItem('lyftr_recent_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [telemetry, setTelemetry] = useState<TelemetryStats>({
    totalTurns: 0,
    cacheHits: 0,
    liveTurns: 0,
    totalLiveLatency: 0,
    totalCacheLatency: 0,
    failoversCount: 0,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load health status on mount
  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Gateway health check failed:', err);
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  // Save session to recent sessions list
  const recordSession = (sessionId: string, lastText?: string) => {
    setRecentSessions((prev) => {
      const filtered = prev.filter((s) => s.session_id !== sessionId);
      const updated = [
        {
          session_id: sessionId,
          lastMessage: lastText || 'Chat session',
          timestamp: Date.now(),
        },
        ...filtered,
      ].slice(0, 15);
      try {
        localStorage.setItem('lyftr_recent_sessions', JSON.stringify(updated));
      } catch {
        // Ignore localStorage error
      }
      return updated;
    });
  };

  // Start fresh new session
  const handleNewSession = () => {
    const newId = generateNewSessionId();
    setCurrentSessionId(newId);
    setMessages([]);
    setInputMessage('');
    // Keep system prompt if user set one, or clear
  };

  // Switch to an existing session from history
  const handleSelectSession = async (sessionId: string) => {
    if (sessionId === currentSessionId) return;
    setCurrentSessionId(sessionId);
    setIsLoading(true);
    try {
      const storedMsgs = await fetchSessionMessages(sessionId);
      const mapped: Message[] = storedMsgs.map((m, idx) => ({
        id: `${sessionId}-${idx}`,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        metadata: m.metadata,
      }));
      setMessages(mapped);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Send message
  const handleSendMessage = async (textToSend?: string) => {
    const message = (textToSend !== undefined ? textToSend : inputMessage).trim();
    if (!message || isLoading) return;

    // MUST clear input immediately after sending
    setInputMessage('');

    const userMsgId = `usr-${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      role: 'user',
      content: message,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(
        currentSessionId,
        message,
        systemPrompt,
        activeSimulation,
      );

      const assistantMsg: Message = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        metadata: response.metadata,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      recordSession(currentSessionId, message);

      // Update session telemetry
      setTelemetry((prev) => {
        const isCache = response.metadata.resolution_source === 'LLM_CACHE';
        return {
          totalTurns: prev.totalTurns + 1,
          cacheHits: isCache ? prev.cacheHits + 1 : prev.cacheHits,
          liveTurns: !isCache ? prev.liveTurns + 1 : prev.liveTurns,
          totalLiveLatency: !isCache
            ? prev.totalLiveLatency + response.metadata.latency_ms
            : prev.totalLiveLatency,
          totalCacheLatency: isCache
            ? prev.totalCacheLatency + response.metadata.latency_ms
            : prev.totalCacheLatency,
          failoversCount:
            prev.failoversCount + (response.metadata.fallback_attempts > 0 ? 1 : 0),
        };
      });
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: 'error',
        content: error?.message || 'Unknown network error. Check gateway connection.',
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 flex-col font-sans">
      {/* Top Header */}
      <Header
        health={health}
        healthLoading={healthLoading}
        onRefreshHealth={checkHealth}
        activeSimulation={activeSimulation}
      />

      {/* Failover Simulator Bar */}
      <FailoverLab
        activeSimulation={activeSimulation}
        setActiveSimulation={setActiveSimulation}
      />

      {/* Main Workspace: Sidebar + Chat Window */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          currentSessionId={currentSessionId}
          onNewSession={handleNewSession}
          recentSessions={recentSessions}
          onSelectSession={handleSelectSession}
          systemPrompt={systemPrompt}
          setSystemPrompt={setSystemPrompt}
          telemetry={telemetry}
        />

        {/* Center Chat View */}
        <main className="flex-1 flex flex-col justify-between overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900/20 to-slate-950">
          {/* Scrollable Message Container */}
          <div className="flex-1 overflow-y-auto px-6 py-6 max-w-4xl w-full mx-auto">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-6 py-12">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 flex items-center justify-center shadow-xl">
                  <Bot className="w-7 h-7 text-emerald-400" />
                </div>

                <div className="space-y-2 max-w-md">
                  <h2 className="text-xl font-bold tracking-tight text-white">
                    Lyftr AI LLM Gateway
                  </h2>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Connected to deterministic key failover pool and LiteLLM response caching.
                    Active Session: <code className="text-emerald-400 font-mono">{currentSessionId}</code>
                  </p>
                </div>

                {/* Clickable Demo Prompts */}
                <div className="space-y-2 w-full max-w-md text-left">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
                    Demo Prompt Starters
                  </div>
                  <div className="space-y-2">
                    {[
                      'What is the capital of France?',
                      'Explain LLM response caching in 2 sentences.',
                      'Give me 3 tips for resilient APIs.',
                    ].map((promptText) => (
                      <button
                        key={promptText}
                        onClick={() => handleSendMessage(promptText)}
                        className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 hover:border-emerald-500/40 text-xs text-slate-300 transition-all flex items-center justify-between group cursor-pointer"
                      >
                        <span>{promptText}</span>
                        <Sparkles className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition-colors shrink-0 ml-2" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Bottom Chat Input */}
          <ChatInput
            inputMessage={inputMessage}
            setInputMessage={setInputMessage}
            onSend={() => handleSendMessage()}
            isLoading={isLoading}
          />
        </main>
      </div>
    </div>
  );
};
