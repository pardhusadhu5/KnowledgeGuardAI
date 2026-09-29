import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import InvestigatePage from './pages/InvestigatePage';
import HistoryPage from './pages/HistoryPage';
import AboutPage from './pages/AboutPage';

export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentInvestigation, setCurrentInvestigation] = useState(null);

  const handleSelectInvestigation = (inv) => {
    setCurrentInvestigation(inv);
    setActiveTab('investigate');
  };

  const handleInvestigateTopic = (topicClaim) => {
    setCurrentInvestigation(null);
    setActiveTab('investigate');
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Navigation Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto max-h-screen">
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              {activeTab === 'dashboard' && 'System Dashboard'}
              {activeTab === 'knowledge-base' && 'Knowledge Base Management'}
              {activeTab === 'investigate' && 'Agentic Investigation Console'}
              {activeTab === 'history' && 'Audit History & Results'}
              {activeTab === 'about' && 'System Architecture & Syllabus'}
            </h2>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              FastAPI + LangGraph
            </span>
          </div>
        </header>

        {/* Content Body */}
        <div className="p-6 md:p-8 flex-1 max-w-7xl w-full mx-auto">
          {activeTab === 'dashboard' && (
            <DashboardPage
              setActiveTab={setActiveTab}
              onSelectInvestigation={handleSelectInvestigation}
            />
          )}

          {activeTab === 'knowledge-base' && (
            <KnowledgeBasePage
              onInvestigateTopic={handleInvestigateTopic}
            />
          )}

          {activeTab === 'investigate' && (
            <InvestigatePage
              currentInvestigation={currentInvestigation}
              setCurrentInvestigation={setCurrentInvestigation}
            />
          )}

          {activeTab === 'history' && (
            <HistoryPage />
          )}

          {activeTab === 'about' && (
            <AboutPage />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
