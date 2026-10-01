import React from 'react';
import { 
  ShieldCheck, 
  BookOpen, 
  Cpu, 
  Workflow, 
  Layers, 
  GitBranch, 
  AlertTriangle, 
  CheckCircle2, 
  GitCompare, 
  HelpCircle,
  GraduationCap
} from 'lucide-react';

export const AboutPage = () => {
  const syllabusModules = [
    {
      code: 'Module I',
      title: 'LLMs & Intelligent Agents',
      desc: 'Combines Large Language Models with autonomous stateful agents capable of goal-directed reasoning, tool calling, and structured output formatting.',
    },
    {
      code: 'Module V',
      title: 'Inference & Reasoning',
      desc: 'Evaluates logical consistency between historical assertions and newer documents, performing temporal inference and deduction.',
    },
    {
      code: 'Module VI',
      title: 'Knowledge Representation',
      desc: 'Represents organizational knowledge through high-dimensional vector embeddings, chunk metadata (versions, dates, sources), and structured relational schemas.',
    },
    {
      code: 'Module VII',
      title: 'Planning & Agent Workflows',
      desc: 'LangGraph multi-step state graph orchestrating claim analysis, RAG retrieval, sufficiency check with dynamic re-querying, and report generation.',
    },
    {
      code: 'Module VIII',
      title: 'Uncertainty Handling',
      desc: 'Identifies missing, ambiguous, or incomplete evidence and explicitly returns UNCERTAIN with calibrated confidence rather than hallucinating answers.',
    },
    {
      code: 'Module X',
      title: 'Real-World AI Applications',
      desc: 'Addresses real-world AI reliability and knowledge decay in enterprise documentation, microservice APIs, and regulatory policies.',
    },
  ];

  const knowledgeDefinitions = [
    {
      status: 'CURRENT',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/10',
      summary: 'Available evidence supports the stored knowledge.',
      detail: 'Official documentation confirms the specification remains actively endorsed, maintained, and operational without dissenting directives.'
    },
    {
      status: 'OUTDATED',
      icon: AlertTriangle,
      color: 'text-rose-400',
      border: 'border-rose-500/30',
      bg: 'bg-rose-500/10',
      summary: 'Available newer/applicable evidence indicates the stored knowledge is no longer current.',
      detail: 'Newer release notes, version upgrades, or deprecation notices supersede the baseline advice (e.g. API v2 deprecated in favor of API v3).'
    },
    {
      status: 'CONFLICTING',
      icon: GitCompare,
      color: 'text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/10',
      summary: 'Relevant sources contain unresolved contradictory information.',
      detail: 'Multiple concurrent documents specify mutually incompatible policies (e.g. Policy A requiring API keys vs Policy B mandating OAuth 2.0).'
    },
    {
      status: 'UNCERTAIN',
      icon: HelpCircle,
      color: 'text-sky-400',
      border: 'border-sky-500/30',
      bg: 'bg-sky-500/10',
      summary: 'Available evidence is insufficient or ambiguous.',
      detail: 'The knowledge repository lacks conclusive documentation to prove or refute the claim. Human verification and research is required.'
    },
  ];

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Hero Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-4 shadow-xl">
        <div className="flex items-center gap-2.5">
          <div className="p-2.5 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              KnowledgeGuard AI
            </h1>
            <p className="text-xs text-indigo-400 font-mono">
              An Agentic RAG System for Detecting Outdated and Conflicting Knowledge in AI Systems
            </p>
          </div>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed">
          Modern AI systems increasingly rely on external knowledge through documents, vector databases, and enterprise repositories. However, organizational knowledge naturally decays: APIs deprecate, frameworks upgrade, and contradictory policies emerge. Standard RAG systems blindly retrieve matching passages without determining whether the information is still valid or obsolete.
        </p>

        <p className="text-sm text-slate-400 leading-relaxed">
          <strong className="text-slate-200">KnowledgeGuard AI</strong> acts as a dedicated <strong className="text-indigo-300">Knowledge Reliability Layer</strong>. It combines vector search (ChromaDB), an autonomous multi-step agent (LangGraph), and LLM reasoning to investigate whether organizational knowledge is <span className="text-emerald-400">CURRENT</span>, <span className="text-rose-400">OUTDATED</span>, <span className="text-amber-400">CONFLICTING</span>, or <span className="text-sky-400">UNCERTAIN</span>.
        </p>
      </div>

      {/* Required Architecture Workflow */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
          <Workflow className="w-4 h-4 text-indigo-400" />
          End-to-End System Architecture
        </h2>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 text-center">
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-indigo-300">1. User Claim</span>
            <span className="text-slate-600">→</span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-sky-300">2. RAG Retrieval (ChromaDB)</span>
            <span className="text-slate-600">→</span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-purple-300">3. LangGraph Agent</span>
            <span className="text-slate-600">→</span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-emerald-300">4. LLM Reasoning</span>
            <span className="text-slate-600">→</span>
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-amber-300">5. Classification & Human Review</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200">1. RAG Layer</h4>
            <p className="text-slate-400">Splits documents, generates embeddings, stores vectors in ChromaDB, and performs semantic retrieval.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200">2. AI Agent (LangGraph)</h4>
            <p className="text-slate-400">Controls the multi-step investigation graph, evaluates sufficiency, triggers query expansion, and coordinates evidence.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200">3. LLM Reasoning</h4>
            <p className="text-slate-400">Analyzes temporal diffs, identifies deprecation indicators, checks policy conflicts, and formulates recommendations.</p>
          </div>
        </div>
      </div>

      {/* Knowledge Status Definitions (Requirement 20) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          Knowledge Status Definitions
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {knowledgeDefinitions.map((kd) => {
            const Icon = kd.icon;
            return (
              <div
                key={kd.status}
                className={`p-4 rounded-xl border ${kd.border} ${kd.bg} space-y-2`}
              >
                <div className="flex items-center gap-2 font-bold text-sm tracking-wide">
                  <Icon className={`w-4 h-4 ${kd.color}`} />
                  <span className={kd.color}>{kd.status}</span>
                </div>
                <p className="text-xs text-slate-200 font-medium">
                  {kd.summary}
                </p>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {kd.detail}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Syllabus Connections (Requirement 36) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm uppercase tracking-wider font-mono">
          <GraduationCap className="w-5 h-5" />
          <span>Academic Curriculum & AI Syllabus Connection</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {syllabusModules.map((sm, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5"
            >
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-indigo-400 font-bold">{sm.code}</span>
                <span className="text-slate-300 font-semibold">{sm.title}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                {sm.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* System Limitations & Reliability (Requirement 11) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 text-amber-400 font-bold text-sm uppercase tracking-wider font-mono">
          <AlertTriangle className="w-5 h-5" />
          <span>System Limitations & Reliability Considerations</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed font-sans">
          KnowledgeGuard AI is designed as an agentic verification layer, not an infallible oracle. Real-world deployment must acknowledge key engineering and statistical limitations:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">1.</span> Retrieval & Terminology Bounds
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Dense vector similarity search may miss critical evidence if enterprise documents utilize unindexed jargon, distinct phrasing, or non-standard formatting.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">2.</span> Provenance & Metadata Dependency
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Temporal supersedence evaluation directly relies on document effective dates and release version stamps. Omitted or corrupted metadata impedes chronological ordering.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">3.</span> LLM Deductive Bounds
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Generative LLMs may occasionally struggle with deeply nested edge cases or highly domain-specific subtleties without fine-tuning, warranting calibrated confidence scores.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">4.</span> Closed-World Knowledge Boundary
            </h4>
            <p className="text-slate-400 leading-relaxed">
              The platform evaluates claims strictly against knowledge ingested into ChromaDB. Facts outside the indexed corpus appropriately resolve to <code className="text-indigo-400">UNCERTAIN</code>.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">5.</span> Scope of Contradiction
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Not every lexical difference constitutes a substantive conflict; divergent rules between departments may reflect intentional division of responsibilities.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <h4 className="font-semibold text-slate-200 font-mono text-xs flex items-center gap-1.5">
              <span className="text-amber-400">6.</span> Embedding Proximity vs. Truth
            </h4>
            <p className="text-slate-400 leading-relaxed">
              Vector distance indicates contextual proximity, not factual accuracy. KnowledgeGuard enforces post-retrieval LLM deliberation to prevent ungrounded generation.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 text-xs text-slate-300 leading-relaxed">
          <strong className="text-indigo-300 font-mono uppercase block mb-1">Human-in-the-Loop Imperative:</strong>
          Critical infrastructure, security protocols, and compliance decisions should never rely entirely on automated AI verdicts. High-impact findings require verification by authorized engineering leads.
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
