import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, ArrowRight } from 'lucide-react';

const WORKFLOW_STEPS = [
  { id: 'understand_claim', label: 'Claim Understood', desc: 'Analyzing claim syntax, entities, and keywords' },
  { id: 'search_knowledge_base', label: 'Searching Knowledge Base', desc: 'Executing vector semantic retrieval in ChromaDB' },
  { id: 'retrieve_evidence', label: 'Evidence Retrieved', desc: 'Curating candidate passages & source references' },
  { id: 'inspect_metadata', label: 'Agent Investigating', desc: 'Inspecting version history, dates, and sufficiency' },
  { id: 'compare_relevant_evidence', label: 'Comparing Evidence', desc: 'Cross-referencing temporal and factual divergences' },
  { id: 'send_structured_evidence_to_llm', label: 'LLM Reasoning', desc: 'Synthesizing evidence-bound logical deduction' },
  { id: 'classify_knowledge', label: 'Generating Result', desc: 'Finalizing classification, confidence, and human review verdict' },
];

export const AgentStepsProgress = ({ isRunning, completedSteps = [] }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (!isRunning) {
      setCurrentStepIndex(WORKFLOW_STEPS.length);
      return;
    }

    // Step simulation progression while waiting for network response
    setCurrentStepIndex(0);
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < WORKFLOW_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 450);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="bg-slate-900/80 border border-indigo-500/20 rounded-xl p-5 backdrop-blur-sm shadow-lg shadow-indigo-950/20">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></div>
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono">
            LangGraph Agent Workflow Execution
          </h3>
        </div>
        <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          {isRunning ? 'RUNNING' : 'COMPLETED'}
        </span>
      </div>

      <div className="space-y-3">
        {WORKFLOW_STEPS.map((step, idx) => {
          const isDone = !isRunning || idx < currentStepIndex;
          const isActive = isRunning && idx === currentStepIndex;
          const isPending = isRunning && idx > currentStepIndex;

          return (
            <div
              key={step.id}
              className={`flex items-start gap-3 p-2.5 rounded-lg border transition-all ${
                isActive
                  ? 'bg-indigo-950/40 border-indigo-500/50 shadow-sm'
                  : isDone
                  ? 'bg-slate-950/30 border-slate-800/80 text-slate-300'
                  : 'bg-transparent border-transparent opacity-40 text-slate-500'
              }`}
            >
              <div className="mt-0.5">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-700 shrink-0"></div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className={`text-xs font-semibold ${isActive ? 'text-indigo-300' : isDone ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.label}
                  </p>
                  <span className="text-[10px] font-mono text-slate-500">
                    Step {idx + 1}/7
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentStepsProgress;
