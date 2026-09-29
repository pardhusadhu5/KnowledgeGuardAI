import React, { useState } from 'react';
import { 
  SearchCode, 
  Sparkles, 
  Send, 
  AlertCircle, 
  CheckCircle2, 
  HelpCircle, 
  RotateCcw,
  Zap,
  Info
} from 'lucide-react';
import api from '../services/api';
import AgentStepsProgress from '../components/AgentStepsProgress';
import InvestigationResultCard from '../components/InvestigationResultCard';

const DEMO_SCENARIOS = [
  {
    title: 'Scenario 1: Outdated API Standard',
    claim: 'Is API v2 still recommended?',
    badge: 'OUTDATED Expected',
    color: 'border-rose-500/30 text-rose-300 bg-rose-500/10'
  },
  {
    title: 'Scenario 2: Active Python Support',
    claim: 'Is Python 3.12 supported?',
    badge: 'CURRENT Expected',
    color: 'border-emerald-500/30 text-emerald-300 bg-emerald-500/10'
  },
  {
    title: 'Scenario 3: Conflicting Auth Policies',
    claim: 'What authentication protocol is required?',
    badge: 'CONFLICTING Expected',
    color: 'border-amber-500/30 text-amber-300 bg-amber-500/10'
  },
  {
    title: 'Scenario 4: Incomplete / Uncertain Research',
    claim: 'Is quantum encryption mandated for all internal APIs?',
    badge: 'UNCERTAIN Expected',
    color: 'border-sky-500/30 text-sky-300 bg-sky-500/10'
  },
];

export const InvestigatePage = ({ currentInvestigation, setCurrentInvestigation }) => {
  const [claim, setClaim] = useState('');
  const [investigating, setInvestigating] = useState(false);
  const [error, setError] = useState('');

  const handleInvestigate = async (e) => {
    if (e) e.preventDefault();
    const query = claim.trim();
    if (!query) {
      setError('Please provide a claim or question to investigate.');
      return;
    }

    try {
      setInvestigating(true);
      setError('');
      setCurrentInvestigation(null);

      const result = await api.investigateClaim(query);
      setCurrentInvestigation(result);
    } catch (err) {
      console.error('Investigation failed:', err);
      setError(err.response?.data?.detail || 'Investigation workflow failed. Please check backend connection.');
    } finally {
      setInvestigating(false);
    }
  };

  const handleScenarioClick = (scenarioClaim) => {
    setClaim(scenarioClaim);
    setError('');
  };

  const handleReset = () => {
    setClaim('');
    setCurrentInvestigation(null);
    setError('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <SearchCode className="w-5 h-5 text-indigo-400" />
          Knowledge Investigation
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Submit any knowledge statement or architectural claim. The LangGraph Knowledge Investigator Agent will query ChromaDB, compare evidence, and synthesize an evidence-grounded verdict.
        </p>
      </div>

      {/* Investigation Input Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <form onSubmit={handleInvestigate} className="space-y-3">
          <label className="block text-xs font-mono uppercase tracking-wider text-slate-400">
            Enter Claim or Question to Investigate *
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="e.g. Is API v2 still recommended? Or does authentication require API keys?"
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
              disabled={investigating}
              className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-sans"
            />
            <button
              type="submit"
              disabled={investigating || !claim.trim()}
              className="px-6 py-3 rounded-xl font-semibold text-xs text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 whitespace-nowrap"
            >
              <Sparkles className="w-4 h-4" />
              {investigating ? 'Investigating...' : 'Investigate Claim'}
            </button>
          </div>
        </form>

        {/* Demo Quick-Click Scenarios */}
        <div className="pt-3 border-t border-slate-800 space-y-2">
          <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Quick Demo Scenarios (Click to test evaluation requirements):
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {DEMO_SCENARIOS.map((sc, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleScenarioClick(sc.claim)}
                disabled={investigating}
                className="text-left p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 hover:border-slate-700 hover:bg-slate-850/60 transition-all flex items-center justify-between gap-2 text-xs"
              >
                <div className="min-w-0">
                  <p className="font-medium text-slate-300 truncate font-sans">
                    {sc.claim}
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {sc.title}
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[9px] font-mono border shrink-0 ${sc.color}`}>
                  {sc.badge}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-xs text-rose-200 font-mono flex items-center gap-3 shadow-lg">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <div className="flex-1">{error}</div>
        </div>
      )}

      {/* Live Agent Execution Progress (Requirement 15 & 28) */}
      {investigating && (
        <AgentStepsProgress isRunning={true} />
      )}

      {/* Result Display */}
      {currentInvestigation && !investigating && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-mono text-slate-400">
              Investigation Verdict Complete
            </span>
            <button
              onClick={handleReset}
              className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Clear Result
            </button>
          </div>

          <InvestigationResultCard result={currentInvestigation} />
        </div>
      )}
    </div>
  );
};

export default InvestigatePage;
