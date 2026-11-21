import React from 'react';
import { PlusCircle, MessageSquare, Activity, Settings2 } from 'lucide-react';
import { SessionInfo, TelemetryStats } from '../types';

interface SidebarProps {
  currentSessionId: string;
  onNewSession: () => void;
  recentSessions: SessionInfo[];
  onSelectSession: (sessionId: string) => void;
  systemPrompt: string;
  setSystemPrompt: (val: string) => void;
  telemetry: TelemetryStats;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentSessionId,
  onNewSession,
  recentSessions,
  onSelectSession,
  systemPrompt,
  setSystemPrompt,
  telemetry,
}) => {
  const cacheHitRate =
    telemetry.totalTurns > 0
      ? Math.round((telemetry.cacheHits / telemetry.totalTurns) * 100)
      : 0;

  const avgLiveLatency =
    telemetry.liveTurns > 0
      ? Math.round(telemetry.totalLiveLatency / telemetry.liveTurns)
      : 0;

  const avgCacheLatency =
    telemetry.cacheHits > 0
      ? Math.round(telemetry.totalCacheLatency / telemetry.cacheHits)
      : 0;

  return (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/60 backdrop-blur flex flex-col justify-between h-full">
      <div className="p-4 space-y-5 overflow-y-auto">
        {/* New Session Button */}
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-semibold text-xs shadow-lg shadow-emerald-950 transition-all cursor-pointer"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Session</span>
        </button>

        {/* System Prompt Bar (ALWAYS MOUNTED IN DOM for data-testid contract) */}
        <div className="space-y-2 bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <div className="flex items-center space-x-1.5">
              <Settings2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>System Prompt</span>
            </div>
            <span className="text-[10px] text-slate-500 font-normal">Session scoped</span>
          </div>

          <textarea
            data-testid="system-prompt-input"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Override system prompt (e.g. Answer concisely in bullet points)..."
            rows={2}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-emerald-500/50 resize-none font-sans"
          />
        </div>

        {/* Live Session Telemetry Card */}
        <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 space-y-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300">
            <Activity className="w-3.5 h-3.5 text-teal-400" />
            <span>Session Analytics</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-medium">Cache Hit Rate</div>
              <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                {cacheHitRate}%
              </div>
            </div>

            <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-medium">Failovers</div>
              <div className="text-base font-bold text-amber-400 font-mono mt-0.5">
                {telemetry.failoversCount}
              </div>
            </div>

            <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-medium">Avg Live Latency</div>
              <div className="text-xs font-bold text-slate-200 font-mono mt-1">
                {avgLiveLatency > 0 ? `${avgLiveLatency} ms` : '—'}
              </div>
            </div>

            <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <div className="text-[10px] text-slate-500 font-medium">Avg Cache Latency</div>
              <div className="text-xs font-bold text-emerald-300 font-mono mt-1">
                {avgCacheLatency > 0 ? `${avgCacheLatency} ms` : '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Recent Sessions List */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-1">
            <div className="flex items-center space-x-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
              <span>Recent Sessions</span>
            </div>
            <span className="text-[10px] text-slate-500">{recentSessions.length} stored</span>
          </div>

          <div className="space-y-1 max-h-56 overflow-y-auto">
            {recentSessions.length === 0 ? (
              <div className="text-[11px] text-slate-600 italic px-2 py-2">
                No previous sessions yet
              </div>
            ) : (
              recentSessions.map((sess) => {
                const isActive = sess.session_id === currentSessionId;
                return (
                  <button
                    key={sess.session_id}
                    onClick={() => onSelectSession(sess.session_id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all font-mono flex items-center justify-between ${
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                    }`}
                  >
                    <span className="truncate">{sess.session_id}</span>
                    {isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 ml-1"></span>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800/80 text-[11px] text-slate-500 space-y-1">
        <div className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="font-medium text-slate-400">SQLite WAL Active</span>
        </div>
        <p className="text-[10px] text-slate-600">
          Persistent transactional storage with zero external dependencies.
        </p>
      </div>
    </aside>
  );
};
