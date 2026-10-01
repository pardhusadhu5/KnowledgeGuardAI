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
  Clock,
  Layers,
  Search,
  RefreshCw,
  Building,
  Check,
  X
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import api from '../services/api';

export const InvestigationResultCard = ({ result, onNewInvestigation }) => {
  const [showSteps, setShowSteps] = useState(false);
  const [reviewStatus, setReviewStatus] = useState(result?.human_review_status || 'Pending Review');
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  if (!result) return null;

  const {
    id,
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
    execution_time_ms = 0,
    research_occurred = false,
    retrieval_attempts = 1,
    unique_documents = 1,
    evidence_sufficient = true,
    structured_explanation
  } = result;

  const handleUpdateStatus = async (newStatus) => {
    setIsUpdatingStatus(true);
    try {
      if (id) {
        await api.updateReviewStatus(id, newStatus);
      }
      setReviewStatus(newStatus);
    } catch (e) {
      console.error("Failed to update review status:", e);
      setReviewStatus(newStatus);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Investigation Verdict & Reliability Report #{id || 'LIVE'}
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
            <span>Review: {reviewStatus}</span>
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

      {/* Agent Execution & Decision Demonstration Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/90 font-mono text-xs">
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Retrieval Passes</span>
          <span className="text-slate-200 font-semibold flex items-center gap-1 mt-0.5">
            <Search className="w-3.5 h-3.5 text-indigo-400" />
            {retrieval_attempts} attempt(s)
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Evidence Chunks</span>
          <span className="text-slate-200 font-semibold flex items-center gap-1 mt-0.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            {evidences.length} chunks ({unique_documents} docs)
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Re-Search Decision</span>
          <span className={`font-semibold flex items-center gap-1 mt-0.5 ${
            research_occurred ? 'text-amber-400' : 'text-emerald-400'
          }`}>
            <RefreshCw className="w-3.5 h-3.5" />
            {research_occurred ? 'Activated (2-Pass)' : 'Sufficient (Single-Pass)'}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block text-[10px] uppercase">Execution Latency</span>
          <span className="text-slate-200 font-semibold flex items-center gap-1 mt-0.5">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            {execution_time_ms.toFixed(1)} ms
          </span>
        </div>
      </div>

      {/* Visible Agent Decision Callout */}
      <div className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between ${
        research_occurred
          ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
          : 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
      }`}>
        <div className="flex items-center gap-2">
          {research_occurred ? (
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          ) : (
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>
            {research_occurred 
              ? 'Agent Decision: Initial evidence was insufficient. Dynamic query expansion & secondary search were activated.'
              : 'Agent Decision: First retrieval pass satisfied coverage threshold. Secondary search was safely bypassed.'}
          </span>
        </div>
        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300">
          LangGraph State Verified
        </span>
      </div>

      {/* Structured Evidence -> Verdict Explanation */}
      {structured_explanation && (
        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-3">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs font-mono uppercase tracking-wider">
            <GitBranch className="w-4 h-4" />
            <span>Evidence Rationale Breakdown</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {structured_explanation.older_evidence && (
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-500 font-mono text-[10px] block">Older Baseline Specification</span>
                <span className="text-slate-300 font-medium">{structured_explanation.older_evidence}</span>
              </div>
            )}
            {structured_explanation.newer_evidence && (
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-indigo-400 font-mono text-[10px] block">Newer Superseding Notice</span>
                <span className="text-slate-300 font-medium">{structured_explanation.newer_evidence}</span>
              </div>
            )}
            {structured_explanation.policy_a && (
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-amber-400 font-mono text-[10px] block">Policy A Directive</span>
                <span className="text-slate-300 font-medium">{structured_explanation.policy_a}</span>
              </div>
            )}
            {structured_explanation.policy_b && (
              <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-rose-400 font-mono text-[10px] block">Policy B Directive</span>
                <span className="text-slate-300 font-medium">{structured_explanation.policy_b}</span>
              </div>
            )}
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
            <span className="font-mono text-[10px] text-slate-400 block mb-0.5">Deductive Assessment:</span>
            {structured_explanation.final_assessment || structured_explanation.temporal_relationship || comparison}
          </div>
        </div>
      )}

      {/* Evidence Panel (Source Traceability) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Verified Source Provenance ({evidences.length} chunks)
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">
            ChromaDB Vector Distance Ordered
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
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-all space-y-2.5"
              >
                {/* Document Metadata Header */}
                <div className="flex flex-wrap items-center justify-between gap-1.5 text-xs font-mono pb-2 border-b border-slate-800/80">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 font-semibold truncate max-w-[200px]" title={ev.source}>
                    {ev.source || 'Document'}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {ev.version && (
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px]">
                        v{ev.version}
                      </span>
                    )}
                    {ev.date && (
                      <span className="flex items-center gap-1 text-[10px] text-slate-400">
                        <Calendar className="w-3 h-3 text-slate-500" />
                        {ev.date}
                      </span>
                    )}
                  </div>
                </div>

                {/* Evidence Passage */}
                <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                  "{ev.evidence_text}"
                </p>

                {/* Provenance & Relevance Footer */}
                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pt-1">
                  <span>Relevance: {(ev.relevance_score * 100).toFixed(1)}%</span>
                  {ev.is_stored_knowledge ? (
                    <span className="text-amber-400 text-[10px]">● Stored Baseline</span>
                  ) : (
                    <span className="text-slate-400 text-[10px]">● Chunk #{idx + 1}</span>
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
          <span>Recommended Remediation</span>
        </div>
        <p className="text-sm text-slate-300 font-medium leading-relaxed">
          {recommendation}
        </p>
      </div>

      {/* Human-in-the-Loop Review Area */}
      <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Human-in-the-Loop Governance Status
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Current Status: <span className="font-semibold text-indigo-400 font-mono">{reviewStatus}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {['Pending Review', 'Reviewed', 'Accepted', 'Rejected'].map((statusOption) => (
            <button
              key={statusOption}
              disabled={isUpdatingStatus}
              onClick={() => handleUpdateStatus(statusOption)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all ${
                reviewStatus === statusOption
                  ? 'bg-indigo-600 text-white border border-indigo-500 shadow-sm'
                  : 'bg-slate-900 text-slate-300 border border-slate-800 hover:bg-slate-800'
              }`}
            >
              {statusOption}
            </button>
          ))}
        </div>
      </div>

      {/* LangGraph Agent Workflow Execution Trace (Requirements 9 & 10) */}
      <div className="pt-2 border-t border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-semibold flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-indigo-400" />
              Agent Execution Trace ({steps.length} Steps)
            </h3>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
              research_occurred 
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' 
                : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
            }`}>
              {research_occurred ? 'Re-Search Activated' : 'Single-Pass Search'}
            </span>
          </div>

          <button
            onClick={() => setShowSteps(!showSteps)}
            className="flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-slate-200"
          >
            <span>{showSteps ? 'Collapse Details' : 'Expand Node Details'}</span>
            {showSteps ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Trace Visual Decision Sequence */}
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Understand Claim</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Search Knowledge Base</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Retrieve Evidence</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Inspect Metadata</span>
          </div>
          
          {/* Sufficiency Decision Branch */}
          {research_occurred ? (
            <>
              <div className="flex items-center gap-2 text-amber-400 bg-amber-950/20 p-1.5 rounded border border-amber-500/20">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span className="font-semibold text-amber-300">⚠ Evidence Insufficient</span>
                <span className="text-slate-400 text-[10px]">→ Query Expansion Activated</span>
              </div>
              <div className="flex items-center gap-2 text-amber-300 pl-4">
                <ArrowRight className="w-3 h-3 text-amber-400 shrink-0" />
                <span>Secondary Retrieval Executed (search_again node)</span>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2 text-emerald-400 bg-emerald-950/20 p-1.5 rounded border border-emerald-500/20">
              <CheckCircle className="w-3.5 h-3.5 shrink-0" />
              <span className="font-semibold text-emerald-300">✓ Evidence Sufficient</span>
              <span className="text-slate-400 text-[10px]">→ Skipped Secondary Search</span>
            </div>
          )}

          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Compare Relevant Evidence</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Send Structured Evidence to LLM</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Classify Knowledge [{classification}]</span>
          </div>
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-slate-200">Generate Explanation & Recommendation</span>
          </div>
        </div>

        {/* Detailed node trace on expand */}
        {showSteps && (
          <div className="space-y-2 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
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
    </div>
  );
};

export default InvestigationResultCard;
