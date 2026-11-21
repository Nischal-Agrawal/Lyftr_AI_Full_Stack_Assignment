import React from 'react';
import { RefreshCw, Zap } from 'lucide-react';
import { HealthStatus } from '../types';

interface HeaderProps {
  health: HealthStatus | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
  activeSimulation: string;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  onRefreshHealth,
  activeSimulation,
}) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/70 backdrop-blur px-6 flex items-center justify-between z-10">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-[1px] flex items-center justify-center shadow-lg shadow-emerald-500/10">
          <div className="w-full h-full bg-slate-950 rounded-[11px] flex items-center justify-center">
            <Zap className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-base tracking-tight text-white">Lyftr AI Gateway</h1>
            <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              v1.0 Production
            </span>
          </div>
          <p className="text-xs text-slate-400 font-normal">
            Deterministic Key Failover • Response Caching • Per-Request Token Tracking
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {activeSimulation && (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono font-medium animate-pulse">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            <span>Simulating: {activeSimulation}</span>
          </div>
        )}

        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
          <div className="flex items-center space-x-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'ok'
                  ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-300 font-medium">
              {health?.status === 'ok'
                ? `Gateway Online • ${health.keys_configured} Keys • Cache Active`
                : 'Connecting to Gateway...'}
            </span>
          </div>
          <button
            onClick={onRefreshHealth}
            disabled={healthLoading}
            title="Refresh Health Status"
            className="text-slate-400 hover:text-slate-200 transition-colors p-0.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
