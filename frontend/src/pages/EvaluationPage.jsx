import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Download, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  Layers, 
  Clock, 
  Activity, 
  FileText,
  Search,
  Filter,
  Eye,
  X,
  Sparkles
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import api from '../services/api';

export const EvaluationPage = () => {
  const [loading, setLoading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState([]);
  const [filterVerdict, setFilterVerdict] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL'); // ALL, PASSED, FAILED
  const [selectedCase, setSelectedCase] = useState(null);

  const fetchLatestEvaluation = async () => {
    setLoading(true);
    try {
      const summaryData = await api.getEvaluationSummary();
      const resultsData = await api.getEvaluationResults();
      setSummary(summaryData);
      setResults(resultsData || []);
    } catch (e) {
      console.error("Error loading evaluation data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestEvaluation();
  }, []);

  const handleRunEvaluation = async () => {
    setIsRunning(true);
    try {
      const runRes = await api.runEvaluation();
      setSummary(runRes.summary);
      setResults(runRes.results || []);
    } catch (e) {
      console.error("Evaluation run failed:", e);
      alert("Evaluation run failed. Check backend logs.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleExportReport = async () => {
    try {
      const blob = await api.exportEvaluationReport();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'KnowledgeGuard_Evaluation_Report.md');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      console.error("Failed to export report:", e);
      alert("Failed to export evaluation report.");
    }
  };

  const filteredResults = results.filter((item) => {
    if (filterStatus === 'PASSED' && !item.is_correct) return false;
    if (filterStatus === 'FAILED' && item.is_correct) return false;
    if (filterVerdict !== 'ALL' && item.expected_verdict !== filterVerdict) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-indigo-400" />
            Evaluation & Benchmark Suite
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Empirical validation of LangGraph agent & generative LLM across structured test cases
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportReport}
            disabled={!summary || summary.total_test_cases === 0}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
          >
            <Download className="w-4 h-4 text-slate-300" />
            Export Report (.md)
          </button>

          <button
            onClick={handleRunEvaluation}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 border border-indigo-500 transition-all disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Running Benchmark...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                Run Full Evaluation
              </>
            )}
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      {summary && summary.total_test_cases > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Total Cases</span>
            <div className="text-2xl font-bold font-mono text-white mt-1">
              {summary.total_test_cases}
            </div>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">24 benchmark items</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Overall Accuracy</span>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              {summary.overall_accuracy}%
            </div>
            <span className="text-[10px] text-emerald-500 font-mono mt-0.5 block">
              {summary.correct_predictions}/{summary.total_test_cases} passed
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Incorrect</span>
            <div className={`text-2xl font-bold font-mono mt-1 ${summary.incorrect_predictions > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
              {summary.incorrect_predictions}
            </div>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Failed assertions</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Avg Confidence</span>
            <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">
              {summary.average_confidence}%
            </div>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Generative certainty</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Avg Latency</span>
            <div className="text-2xl font-bold font-mono text-white mt-1">
              {summary.average_execution_time_ms.toFixed(0)} <span className="text-xs text-slate-500 font-normal">ms</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Per investigation</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-mono text-slate-400 uppercase block">Re-Searches</span>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">
              {summary.total_researches_triggered}
            </div>
            <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">Multi-pass queries</span>
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
          <p className="text-sm text-slate-400 font-medium">
            No evaluation runs recorded yet. Click <strong>"Run Full Evaluation"</strong> above to benchmark the entire knowledge base.
          </p>
        </div>
      )}

      {/* Grid: Class Metrics & Confusion Matrix */}
      {summary && summary.total_test_cases > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Class Performance Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Per-Class Performance Metrics
              </h3>
              <span className="text-[11px] font-mono text-slate-500">Standard P / R / F1</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Target Verdict</th>
                    <th className="py-2.5 px-3 text-right">Precision</th>
                    <th className="py-2.5 px-3 text-right">Recall</th>
                    <th className="py-2.5 px-3 text-right">F1-Score</th>
                    <th className="py-2.5 px-3 text-right">Support</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {summary.class_metrics.map((cm) => (
                    <tr key={cm.verdict} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3">
                        <StatusBadge status={cm.verdict} size="sm" />
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-200 font-semibold">
                        {cm.precision.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-200 font-semibold">
                        {cm.recall.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-right text-indigo-400 font-bold">
                        {cm.f1_score.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-3 text-right text-slate-400">
                        {cm.support}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Confusion Matrix */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                4×4 Verdict Confusion Matrix
              </h3>
              <span className="text-[11px] font-mono text-slate-500">Row: Exp | Col: Pred</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono text-center">
                <thead>
                  <tr className="text-[10px] text-slate-400 border-b border-slate-800 bg-slate-950/80">
                    <th className="p-2 text-left">Expected \ Pred</th>
                    {summary.confusion_matrix.labels.map((lbl) => (
                      <th key={lbl} className="p-2 text-indigo-300 font-semibold">{lbl.slice(0, 4)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {summary.confusion_matrix.labels.map((rowLabel, rIdx) => (
                    <tr key={rowLabel} className="hover:bg-slate-800/20">
                      <td className="p-2 text-left font-bold text-slate-300 bg-slate-950/40">
                        {rowLabel}
                      </td>
                      {summary.confusion_matrix.matrix[rIdx].map((val, cIdx) => {
                        const isDiagonal = rIdx === cIdx;
                        let cellBg = 'bg-slate-950/40 text-slate-500';
                        if (isDiagonal && val > 0) cellBg = 'bg-emerald-950/50 text-emerald-300 border border-emerald-500/30 font-bold';
                        else if (!isDiagonal && val > 0) cellBg = 'bg-rose-950/50 text-rose-300 border border-rose-500/30 font-bold';
                        return (
                          <td key={cIdx} className="p-2">
                            <span className={`inline-block w-8 py-1 rounded text-xs ${cellBg}`}>
                              {val}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Test Results Table */}
      {results && results.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                Benchmark Test Case Audit Trail ({filteredResults.length} of {results.length})
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Every test case reflects genuine execution through the LangGraph agent and ChromaDB
              </p>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {['ALL', 'PASSED', 'FAILED'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setFilterStatus(st)}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                      filterStatus === st
                        ? 'bg-indigo-600 text-white font-semibold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {['ALL', 'CURRENT', 'OUTDATED', 'CONFLICTING', 'UNCERTAIN'].map((v) => (
                  <button
                    key={v}
                    onClick={() => setFilterVerdict(v)}
                    className={`px-2 py-1 rounded text-[11px] font-medium transition-all ${
                      filterVerdict === v
                        ? 'bg-slate-800 text-indigo-300 border border-slate-700'
                        : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {v === 'ALL' ? 'ALL' : v.slice(0, 4)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-3">ID</th>
                  <th className="py-3 px-3">Claim</th>
                  <th className="py-3 px-3">Expected</th>
                  <th className="py-3 px-3">Predicted</th>
                  <th className="py-3 px-3 text-right">Confidence</th>
                  <th className="py-3 px-3 text-center">Status</th>
                  <th className="py-3 px-3 text-center">Re-Search</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {filteredResults.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-3 text-indigo-400 font-semibold">{item.id}</td>
                    <td className="py-3 px-3 font-sans text-slate-200 max-w-sm truncate" title={item.claim}>
                      {item.claim}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={item.expected_verdict} size="sm" />
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={item.predicted_verdict} size="sm" />
                    </td>
                    <td className="py-3 px-3 text-right text-slate-300 font-semibold">
                      {item.confidence.toFixed(1)}%
                    </td>
                    <td className="py-3 px-3 text-center">
                      {item.is_correct ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold">
                          <CheckCircle className="w-3.5 h-3.5" />
                          MATCH
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] text-rose-400 font-semibold">
                          <XCircle className="w-3.5 h-3.5" />
                          DIFF
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span className={`text-[10px] px-2 py-0.5 rounded border ${
                        item.research_occurred 
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' 
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {item.research_occurred ? 'Activated' : 'Single-Pass'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedCase(item)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] flex items-center gap-1 ml-auto"
                      >
                        <Eye className="w-3 h-3" />
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detailed Modal */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono font-bold">
                  {selectedCase.id}
                </span>
                <h3 className="text-sm font-bold text-white font-mono">Test Case Inspection</h3>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs font-sans">
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Claim Evaluated</span>
                <p className="text-sm font-medium text-slate-200 italic">"{selectedCase.claim}"</p>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block">Expected Verdict</span>
                  <div className="mt-1"><StatusBadge status={selectedCase.expected_verdict} size="sm" /></div>
                </div>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase block">Predicted Verdict</span>
                  <div className="mt-1"><StatusBadge status={selectedCase.predicted_verdict} size="sm" /></div>
                </div>
              </div>

              {selectedCase.reason && (
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-indigo-400 uppercase font-semibold">Benchmark Expected Rationale:</span>
                  <p className="text-slate-300 leading-relaxed">{selectedCase.reason}</p>
                </div>
              )}

              {selectedCase.explanation && (
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-emerald-400 uppercase font-semibold">Model Generative Reasoning:</span>
                  <p className="text-slate-300 leading-relaxed">{selectedCase.explanation}</p>
                </div>
              )}

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 font-mono">
                <span className="text-[10px] text-slate-500 uppercase block">Retrieved Grounding Documents:</span>
                {selectedCase.retrieved_documents && selectedCase.retrieved_documents.length > 0 ? (
                  <ul className="list-disc list-inside text-slate-300 space-y-0.5">
                    {selectedCase.retrieved_documents.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-slate-500 italic">No document chunks grounded this query.</span>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCase(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationPage;
