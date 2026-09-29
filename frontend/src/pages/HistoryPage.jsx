import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  Calendar, 
  FileText, 
  Eye, 
  RefreshCw,
  X,
  UserCheck
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import InvestigationResultCard from '../components/InvestigationResultCard';

export const HistoryPage = () => {
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getInvestigations();
      setInvestigations(data);
    } catch (err) {
      console.error('Failed to load investigation history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredItems = investigations.filter((inv) => {
    const matchesSearch = inv.claim.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || inv.classification.toUpperCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Investigation History & Audit Trail
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Complete record of past knowledge evaluations, evidence trails, and human verification flags.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          className="px-3.5 py-1.5 rounded-lg text-xs font-mono text-slate-300 bg-slate-850 hover:bg-slate-800 border border-slate-700 flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh History
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search investigations by claim..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-1.5">
          {['ALL', 'CURRENT', 'OUTDATED', 'CONFLICTING', 'UNCERTAIN'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                statusFilter === status
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {filteredItems.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs font-mono">
            {investigations.length === 0
              ? 'No investigations recorded yet. Run your first investigation from the Investigate tab.'
              : 'No investigations matched your filter criteria.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Investigated Claim</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Evidence</th>
                  <th className="py-3 px-4">Human Review</th>
                  <th className="py-3 px-4 text-right">View</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredItems.map((inv) => (
                  <tr
                    key={inv.id}
                    onClick={() => setSelectedInvestigation(inv)}
                    className="hover:bg-slate-850/40 transition-colors cursor-pointer"
                  >
                    <td className="py-3.5 px-4 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                      {new Date(inv.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-white max-w-[320px] truncate" title={inv.claim}>
                      "{inv.claim}"
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={inv.classification} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-indigo-300">
                      {inv.confidence.toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">
                      {inv.evidences?.length || 0} passage(s)
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
                        inv.human_verification_required
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                      }`}>
                        {inv.human_verification_required ? 'REQUIRED' : 'NO'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedInvestigation(inv);
                        }}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                        title="View Full Report"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Investigation Details Modal */}
      {selectedInvestigation && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl relative">
            <button
              onClick={() => setSelectedInvestigation(null)}
              className="absolute top-5 right-5 p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
            <InvestigationResultCard result={selectedInvestigation} />
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
