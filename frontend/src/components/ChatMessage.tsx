import React from 'react';
import { Bot, User, AlertTriangle, Database, Zap, ArrowRight, ShieldAlert } from 'lucide-react';
import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  if (message.role === 'error') {
    return (
      <div className="my-4 p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex items-start space-x-3 text-sm shadow-md">
        <ShieldAlert className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
        <div className="flex-1 space-y-1">
          <div className="font-semibold text-rose-300">Request Error</div>
          <p className="text-rose-200/90 leading-relaxed font-mono text-xs">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.role === 'user') {
    return (
      <div className="my-4 flex justify-end">
        <div className="flex items-start max-w-[80%] space-x-3 flex-row-reverse space-x-reverse">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
            <User className="w-4 h-4" />
          </div>
          <div className="bg-indigo-600/90 text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm leading-relaxed shadow-sm">
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          </div>
        </div>
      </div>
    );
  }

  // Assistant message
  const metadata = message.metadata;
  const isCache = metadata?.resolution_source === 'LLM_CACHE';

  return (
    <div className="my-5 flex justify-start">
      <div
        data-testid="assistant-message"
        className="flex items-start max-w-[88%] space-x-3 w-full"
      >
        <div
          className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-md ${
            isCache
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-slate-800 text-blue-400 border border-slate-700'
          }`}
        >
          {isCache ? <Database className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        <div className="flex-1 min-w-0 bg-slate-900/90 border border-slate-800/80 rounded-2xl rounded-tl-sm px-5 py-4 text-slate-200 shadow-sm space-y-3">
          {/* Main reply content */}
          <div className="text-sm leading-relaxed whitespace-pre-wrap break-words font-sans text-slate-100">
            {message.content}
          </div>

          {/* Strict Metadata Section */}
          {metadata && (
            <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
              {/* Resolution Source Pill */}
              <div
                className={`inline-flex items-center px-2 py-0.5 rounded-md font-mono text-[11px] font-semibold border ${
                  isCache
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                }`}
              >
                <span data-testid="meta-source">{metadata.resolution_source}</span>
              </div>

              {/* Model Pill */}
              <div className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-800/90 border border-slate-700/60 text-slate-300 font-mono text-[11px]">
                <span className="text-slate-500">model:</span>
                <span data-testid="meta-model">{metadata.model}</span>
              </div>

              {/* Latency Pill */}
              <div className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-800/90 border border-slate-700/60 text-slate-300 font-mono text-[11px]">
                <Zap className="w-3 h-3 text-amber-400" />
                <span data-testid="meta-latency">{metadata.latency_ms} ms</span>
              </div>

              {/* Token Usage Pill */}
              <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-slate-800/90 border border-slate-700/60 text-slate-300 font-mono text-[11px]">
                <span className="text-slate-500">In:</span>
                <span data-testid="meta-input-tokens">{metadata.input_tokens}</span>
                <span className="text-slate-600">•</span>
                <span className="text-slate-500">Out:</span>
                <span data-testid="meta-output-tokens">{metadata.output_tokens}</span>
              </div>

              {/* Standout Bonus: Key ID Badge (Outside required testids) */}
              <div className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-800/60 text-slate-400 border border-slate-800 font-mono text-[11px]">
                <span>key:</span>
                <span className="text-slate-300 font-medium">
                  {metadata.key_id ? metadata.key_id : 'cached'}
                </span>
              </div>

              {/* Standout Bonus: Failover Alert Badge when fallback_attempts > 0 */}
              {metadata.fallback_attempts > 0 && (
                <div className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-[11px]">
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  <span>Failover: {metadata.fallback_attempts} retry</span>
                  <ArrowRight className="w-2.5 h-2.5 text-amber-400" />
                  <span className="font-semibold text-amber-200">{metadata.key_id}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
