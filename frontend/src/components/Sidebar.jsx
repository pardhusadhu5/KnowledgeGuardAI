import React from 'react';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  Database, 
  SearchCode, 
  History, 
  Info,
  Cpu,
  Layers,
  Activity
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'knowledge-base', label: 'Knowledge Base', icon: Database },
    { id: 'investigate', label: 'Investigate', icon: SearchCode },
    { id: 'history', label: 'Investigation History', icon: History },
    { id: 'evaluation', label: 'Evaluation & Benchmarks', icon: Activity },
    { id: 'about', label: 'About & Syllabus', icon: Info },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 backdrop-blur-md">
      <div>
        {/* Brand */}
        <div className="p-5 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
              <ShieldCheck className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-wide text-white leading-none">
                KnowledgeGuard<span className="text-indigo-400">.AI</span>
              </h1>
              <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider font-mono">
                Agentic Reliability Layer
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm shadow-indigo-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info Box */}
      <div className="p-4 border-t border-slate-800/80 space-y-3">
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              RAG Pipeline
            </span>
            <span className="text-emerald-400 font-semibold">ONLINE</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            ChromaDB + LangGraph Agent + SQLite
          </p>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 px-1 font-mono">
          <span>KnowledgeGuard v1.0</span>
          <span>MVP Ready</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
