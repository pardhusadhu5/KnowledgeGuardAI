import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  SearchCode, 
  AlertTriangle, 
  CheckCircle2, 
  GitCompare, 
  HelpCircle, 
  UserCheck, 
  ArrowUpRight, 
  Sparkles,
  Database,
  RefreshCw,
  FolderPlus
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';

export const DashboardPage = ({ setActiveTab, onSelectInvestigation }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState('');

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSeedSamples = async () => {
    try {
      setSeeding(true);
      setMessage('Ingesting sample scenarios into knowledge base...');
      const res = await api.seedSampleDocuments();
      setMessage(res.message);
      await fetchStats();
      setTimeout(() => setMessage(''), 4000);
    } catch (err) {
      setMessage('Failed to seed sample documents.');
    } finally {
      setSeeding(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mr-2 text-indigo-400" />
        Loading dynamic system statistics...
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Knowledge Chunks',
      value: stats?.total_knowledge_items || 0,
      sub: `${stats?.total_documents || 0} Ingested Documents`,
      icon: Database,
      color: 'text-indigo-400',
      border: 'border-indigo-500/20',
      bg: 'bg-indigo-500/5',
    },
    {
      label: 'Current Knowledge',
      value: stats?.current_count || 0,
      sub: 'Verified & Active',
      icon: CheckCircle2,
      color: 'text-emerald-400',
      border: 'border-emerald-500/20',
      bg: 'bg-emerald-500/5',
    },
    {
      label: 'Outdated Knowledge',
      value: stats?.outdated_count || 0,
      sub: 'Superseded / Deprecated',
      icon: AlertTriangle,
      color: 'text-rose-400',
      border: 'border-rose-500/20',
      bg: 'bg-rose-500/5',
    },
    {
      label: 'Conflicting Policies',
      value: stats?.conflicting_count || 0,
      sub: 'Contradictory Rules',
      icon: GitCompare,
      color: 'text-amber-400',
      border: 'border-amber-500/20',
      bg: 'bg-amber-500/5',
    },
    {
      label: 'Uncertain Claims',
      value: stats?.uncertain_count || 0,
      sub: 'Insufficient Evidence',
      icon: HelpCircle,
      color: 'text-sky-400',
      border: 'border-sky-500/20',
      bg: 'bg-sky-500/5',
    },
    {
      label: 'Requires Human Review',
      value: stats?.requires_review_count || 0,
      sub: 'Action Items Pending',
      icon: UserCheck,
      color: 'text-violet-400',
      border: 'border-violet-500/20',
      bg: 'bg-violet-500/5',
    },
  ];

  const totalInv = stats?.total_investigations || 1;
  const currentPct = Math.round(((stats?.current_count || 0) / totalInv) * 100);
  const outdatedPct = Math.round(((stats?.outdated_count || 0) / totalInv) * 100);
  const conflictPct = Math.round(((stats?.conflicting_count || 0) / totalInv) * 100);
  const uncertainPct = Math.round(((stats?.uncertain_count || 0) / totalInv) * 100);

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Knowledge Reliability Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time analytics computed directly from ChromaDB vector indices and SQLite metadata.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center gap-1.5 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleSeedSamples}
            disabled={seeding}
            className="px-3.5 py-2 rounded-lg text-xs font-medium text-indigo-300 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 flex items-center gap-1.5 transition-all disabled:opacity-50"
          >
            <FolderPlus className="w-3.5 h-3.5" />
            {seeding ? 'Seeding Samples...' : 'Load Sample Documents'}
          </button>

          <button
            onClick={() => setActiveTab('investigate')}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
          >
            <SearchCode className="w-3.5 h-3.5" />
            New Investigation
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3.5 rounded-xl bg-indigo-950/60 border border-indigo-500/30 text-xs text-indigo-200 font-mono">
          ℹ {message}
        </div>
      )}

      {/* Dynamic Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div
              key={i}
              className={`p-5 rounded-xl border ${c.border} ${c.bg} backdrop-blur-sm transition-all hover:translate-y-[-2px]`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  {c.label}
                </span>
                <Icon className={`w-4 h-4 ${c.color}`} />
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-white font-mono">
                  {c.value}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">{c.sub}</p>
            </div>
          );
        })}
      </div>

      {/* Distribution Progress Bar */}
      {stats?.total_investigations > 0 && (
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Knowledge Status Distribution ({stats.total_investigations} Total Investigations)</span>
          </div>
          <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden flex">
            <div style={{ width: `${currentPct}%` }} className="bg-emerald-500" title={`Current: ${currentPct}%`}></div>
            <div style={{ width: `${outdatedPct}%` }} className="bg-rose-500" title={`Outdated: ${outdatedPct}%`}></div>
            <div style={{ width: `${conflictPct}%` }} className="bg-amber-500" title={`Conflicting: ${conflictPct}%`}></div>
            <div style={{ width: `${uncertainPct}%` }} className="bg-sky-500" title={`Uncertain: ${uncertainPct}%`}></div>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono pt-1 text-slate-400">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Current ({stats.current_count})</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Outdated ({stats.outdated_count})</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Conflicting ({stats.conflicting_count})</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span> Uncertain ({stats.uncertain_count})</span>
          </div>
        </div>
      )}

      {/* Two Column Layout: Recent Investigations & Recent Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Investigations */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <SearchCode className="w-4 h-4 text-indigo-400" />
              Recent Investigations
            </h3>
            <button
              onClick={() => setActiveTab('history')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {stats?.recent_investigations?.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No investigations run yet. Start one from the Investigate tab!
            </p>
          ) : (
            <div className="space-y-2.5">
              {stats?.recent_investigations?.map((inv) => (
                <div
                  key={inv.id}
                  onClick={() => onSelectInvestigation && onSelectInvestigation(inv)}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-200 truncate">
                      "{inv.claim}"
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                      Confidence: {inv.confidence}% • {new Date(inv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <StatusBadge status={inv.classification} size="sm" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Documents */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              Recently Ingested Knowledge
            </h3>
            <button
              onClick={() => setActiveTab('knowledge-base')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-mono flex items-center gap-1"
            >
              Manage <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {stats?.recent_documents?.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              Knowledge base is empty. Upload documents or load sample dataset.
            </p>
          ) : (
            <div className="space-y-2.5">
              {stats?.recent_documents?.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-200 truncate flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      {doc.filename}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 font-mono">
                      v{doc.version} • {doc.chunk_count} chunk(s) • {doc.topic}
                    </p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {doc.status.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
