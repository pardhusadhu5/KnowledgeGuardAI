import React, { useState } from 'react';
import { 
  FileText, 
  Calendar, 
  Tag, 
  CheckCircle, 
  AlertCircle, 
  UserCheck, 
  ChevronDown, 
  ChevronUp, 
  Sparkles,
  ArrowRight,
  ShieldAlert,
  GitBranch,
  Clock
} from 'lucide-react';
import StatusBadge from './StatusBadge';

export const InvestigationResultCard = ({ result, onNewInvestigation }) => {
  const [showSteps, setShowSteps] = useState(false);
  const [humanReviewStatus, setHumanReviewStatus] = useState(null);

  if (!result) return null;

  const {
    claim,
    classification,
    explanation,
    confidence,
    recommendation,
    human_verification_required,
    created_at,
    evidences = [],
    steps = [],
    comparison,
  } = result;

  const handleAction = (statusText) => {
    setHumanReviewStatus(statusText);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Investigation Verdict & Reliability Report
          </span>
          <div className="flex items-center gap-3 mt-1.5">
            <h2 className="text-xl font-bold text-white tracking-tight">
              KNOWLEDGE STATUS
            </h2>
            <StatusBadge status={classification} size="lg" />
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Confidence Meter */}
          <div className="text-right">
            <div className="text-[11px] font-mono text-slate-400">Model Confidence</div>
            <div className="text-lg font-bold font-mono text-indigo-400">
              {confidence.toFixed(1)}%
            </div>
          </div>

          {/* Human Verification Badge */}
          <div className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 ${
            human_verification_required 
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' 
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}>
            <UserCheck className="w-4 h-4" />
            <span>Human Review: {human_verification_required ? 'REQUIRED' : 'NOT REQUIRED'}</span>
          </div>
        </div>
      </div>

      {/* Investigated Claim */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80">
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 block mb-1">
          Investigated Claim
        </span>
        <p className="text-base font-medium text-slate-100 italic">
          "{claim}"
        </p>
      </div>

      {/* Comparison Section */}
      {comparison && (
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-2">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs font-mono uppercase tracking-wider">
            <GitBranch className="w-4 h-4" />
            <span>Temporal & Version Evolution Comparison</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {comparison}
          </p>
        </div>
      )}

      {/* Evidence Panel (Evidence-First Design) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Retrieved Source Evidence ({evidences.length})
          </h3>
          <span className="text-[11px] text-slate-500">
            Ordered by ChromaDB Semantic Distance
          </span>
        </div>

        {evidences.length === 0 ? (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-500 text-center">
            No matching documents found in knowledge base.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {evidences.map((ev, idx) => (
              <div
                key={ev.id || idx}
                className={`p-4 rounded-xl border transition-all ${
                  ev.is_stored_knowledge
                    ? 'bg-slate-950/80 border-slate-700/80'
                    : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium truncate max-w-[180px]">
                    {ev.source || 'Document'}
                  </span>
                  <div className="flex items-center gap-2">
                    {ev.version && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px]">
                        v{ev.version}
                      </span>
                    )}
                    {ev.date && (
                      <span className="flex items-center gap-1 text-[10px] text-slate-400">
                        <Calendar className="w-3 h-3" />
                        {ev.date}
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                  "{ev.evidence_text}"
                </p>

                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Relevance: {(ev.relevance_score * 100).toFixed(1)}%</span>
                  {ev.is_stored_knowledge && (
                    <span className="text-amber-400 text-[10px]">● Stored Baseline</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Reasoning & Explanation */}
      <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-indigo-400">
          <Sparkles className="w-4 h-4" />
          <span>LLM Reasoning & Synthesis</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed">
          {explanation}
        </p>
      </div>

      {/* Actionable Recommendation */}
      <div className="p-5 rounded-xl bg-slate-950/80 border border-indigo-500/20 space-y-2">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-400">
          <ArrowRight className="w-4 h-4" />
          <span>Recommended Next Action</span>
        </div>
        <p className="text-sm text-slate-300 font-medium leading-relaxed">
          {recommendation}
        </p>
      </div>

      {/* Human-in-the-Loop Review Area */}
      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Human-in-the-Loop Review
          </h4>
          <p className="text-xs text-slate-500 mt-0.5">
            {humanReviewStatus ? (
              <span className="text-emerald-400 font-medium">✓ Action Logged: {humanReviewStatus}</span>
            ) : (
              'Verify findings before modifying organization knowledge base.'
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleAction('Approved & Verified as Current')}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 transition-all"
          >
            Mark Verified
          </button>
          <button
            onClick={() => handleAction('Knowledge Flagged for Deprecation')}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 transition-all"
          >
            Flag Deprecated
          </button>
          <button
            onClick={() => handleAction('Pending Architecture Review')}
            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all"
          >
            Escalate Review
          </button>
        </div>
      </div>

      {/* Collapsible LangGraph Agent Workflow Steps */}
      {steps && steps.length > 0 && (
        <div className="pt-2 border-t border-slate-800">
          <button
            onClick={() => setShowSteps(!showSteps)}
            className="w-full flex items-center justify-between text-xs font-mono text-slate-400 hover:text-slate-200 py-1"
          >
            <span>View LangGraph Execution Trace ({steps.length} Steps)</span>
            {showSteps ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showSteps && (
            <div className="mt-3 space-y-2 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
              {steps.map((st, i) => (
                <div key={i} className="flex items-start gap-2.5 pb-2 border-b border-slate-900 last:border-0 last:pb-0">
                  <span className="text-indigo-400 shrink-0">#{i + 1}</span>
                  <div>
                    <span className="text-slate-300 font-semibold">{st.step_name}:</span>{' '}
                    <span className="text-slate-400">{st.description}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InvestigationResultCard;
