import React, { useState } from 'react';
import { FlaskConical, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';

interface FailoverLabProps {
  activeSimulation: string;
  setActiveSimulation: (val: string) => void;
}

export const FailoverLab: React.FC<FailoverLabProps> = ({
  activeSimulation,
  setActiveSimulation,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [customRule, setCustomRule] = useState('');

  const simulationPresets = [
    { label: 'Normal (No Simulation)', value: '' },
    { label: 'Simulate key_1 = 429 (Rate Limit)', value: 'key_1=429' },
    { label: 'Simulate key_1 = 500 (Internal Error)', value: 'key_1=500' },
    { label: 'Simulate * = 429 (All Keys Down -> 503)', value: '*=429' },
    { label: 'Simulate key_1=429, key_2=502', value: 'key_1=429,key_2=502' },
  ];

  return (
    <div className="border-b border-slate-800 bg-slate-900/40 text-xs">
      <div className="max-w-6xl mx-auto px-6 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FlaskConical className="w-4 h-4 text-amber-400" />
          <span className="font-semibold text-slate-200">Interactive Failover Lab</span>
          <span className="text-slate-400 hidden sm:inline">— Test API key fallback on demand via X-Simulate-Failure</span>
        </div>

        <div className="flex items-center space-x-3">
          {activeSimulation ? (
            <button
              onClick={() => setActiveSimulation('')}
              className="flex items-center space-x-1 text-rose-400 hover:text-rose-300 font-mono text-[11px] px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset to Normal</span>
            </button>
          ) : null}

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center space-x-1 text-slate-400 hover:text-slate-200 py-0.5"
          >
            <span>{isOpen ? 'Collapse Panel' : 'Configure Failover'}</span>
            {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="max-w-6xl mx-auto px-6 pb-4 pt-1 space-y-3 border-t border-slate-800/60">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {simulationPresets.map((preset) => {
              const isSelected = activeSimulation === preset.value;
              return (
                <button
                  key={preset.label}
                  onClick={() => setActiveSimulation(preset.value)}
                  className={`px-3 py-2 text-left rounded-xl border text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-amber-500/10 border-amber-500/40 text-amber-200 shadow-sm'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span>{preset.label}</span>
                    {isSelected && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>}
                  </div>
                  {preset.value && (
                    <div className="mt-1 font-mono text-[10px] text-slate-500">
                      Header: X-Simulate-Failure: {preset.value}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          <div className="flex items-center space-x-2 pt-1">
            <input
              type="text"
              placeholder="Custom rule (e.g. key_1=429,key_2=503)"
              value={customRule}
              onChange={(e) => setCustomRule(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 font-mono text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-amber-500/60"
            />
            <button
              onClick={() => {
                if (customRule.trim()) {
                  setActiveSimulation(customRule.trim());
                  setCustomRule('');
                }
              }}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
            >
              Apply Custom Rule
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
