import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  Trash2, 
  Eye, 
  SearchCode, 
  Calendar, 
  Tag, 
  CheckCircle2, 
  AlertCircle, 
  Loader2,
  RefreshCw,
  FolderPlus,
  X
} from 'lucide-react';
import api from '../services/api';

const UPLOAD_STAGES = [
  'Uploading...',
  'Extracting text...',
  'Creating chunks...',
  'Generating embeddings...',
  'Indexing knowledge...',
  'Complete'
];

export const KnowledgeBasePage = ({ onInvestigateTopic }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [source, setSource] = useState('');
  const [version, setVersion] = useState('1.0');
  const [topic, setTopic] = useState('General');
  const [docDate, setDocDate] = useState(new Date().toISOString().split('T')[0]);
  
  const [uploading, setUploading] = useState(false);
  const [uploadStage, setUploadStage] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Chunk Inspection Modal
  const [viewingDoc, setViewingDoc] = useState(null);
  const [chunksLoading, setChunksLoading] = useState(false);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      if (!source) {
        setSource(file.name);
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select a file to upload (.pdf or .txt).');
      return;
    }

    try {
      setUploading(true);
      setErrorMessage('');
      setSuccessMessage('');
      setUploadStage(0);

      // Simulate visual progress stages
      const interval = setInterval(() => {
        setUploadStage((prev) => (prev < 4 ? prev + 1 : prev));
      }, 350);

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('source', source || selectedFile.name);
      formData.append('version', version || '1.0');
      formData.append('topic', topic || 'General');
      formData.append('document_date', docDate);

      const res = await api.uploadDocument(formData);
      clearInterval(interval);
      setUploadStage(5);

      setSuccessMessage(`Document '${res.filename}' successfully processed and indexed into ChromaDB!`);
      setSelectedFile(null);
      setSource('');
      await fetchDocuments();
      setTimeout(() => {
        setUploading(false);
        setUploadStage(0);
      }, 1000);
    } catch (err) {
      setUploading(false);
      setErrorMessage(err.response?.data?.detail || 'Failed to process and index document.');
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete '${filename}' and its vector embeddings?`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
      setSuccessMessage(`Document #${docId} removed from database and ChromaDB.`);
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to delete document.');
    }
  };

  const handleViewChunks = async (docId) => {
    try {
      setChunksLoading(true);
      const details = await api.getDocumentById(docId);
      setViewingDoc(details);
    } catch (err) {
      alert('Failed to retrieve chunks for document.');
    } finally {
      setChunksLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Knowledge Repository
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ingest authoritative enterprise documents, policies, and specifications for vector indexing.
          </p>
        </div>

        <button
          onClick={fetchDocuments}
          className="px-3.5 py-1.5 rounded-lg text-xs font-mono text-slate-300 bg-slate-850 hover:bg-slate-800 border border-slate-700 flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh List
        </button>
      </div>

      {/* Alerts */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/30 text-xs text-rose-200 font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
      {successMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-xs text-emerald-200 font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Document Upload Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono flex items-center gap-2">
          <Upload className="w-4 h-4 text-indigo-400" />
          Ingest New Document (PDF or TXT)
        </h3>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* File Selector */}
            <div className="lg:col-span-2">
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Select Document (.pdf, .txt) *
              </label>
              <input
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                disabled={uploading}
                className="w-full text-xs text-slate-300 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600/20 file:text-indigo-300 hover:file:bg-indigo-600/30 file:cursor-pointer border border-slate-700 rounded-lg p-1.5 bg-slate-950"
              />
            </div>

            {/* Source / Title */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Source / Provenance Title
              </label>
              <input
                type="text"
                placeholder="e.g. Architecture Guide"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                disabled={uploading}
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Version */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Specification Version
              </label>
              <input
                type="text"
                placeholder="e.g. 2.0"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                disabled={uploading}
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Topic */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Topic Category
              </label>
              <input
                type="text"
                placeholder="e.g. API Architecture"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={uploading}
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Document Date */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Document Effective Date
              </label>
              <input
                type="date"
                value={docDate}
                onChange={(e) => setDocDate(e.target.value)}
                disabled={uploading}
                className="w-full text-xs bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Upload Progress Stepper (Requirement 28) */}
          {uploading && (
            <div className="p-4 rounded-xl bg-slate-950 border border-indigo-500/30 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-indigo-300">
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                  Processing Status: {UPLOAD_STAGES[uploadStage]}
                </span>
                <span>Stage {uploadStage + 1} / 6</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full transition-all duration-300"
                  style={{ width: `${((uploadStage + 1) / 6) * 100}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-all flex items-center gap-2 shadow-md shadow-indigo-600/20"
            >
              <Upload className="w-4 h-4" />
              {uploading ? 'Processing Document...' : 'Ingest & Chunk Document'}
            </button>
          </div>
        </form>
      </div>

      {/* Stored Documents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" />
            Ingested Documents ({documents.length})
          </h3>
          <span className="text-xs font-mono text-slate-500">
            Vectorized in ChromaDB
          </span>
        </div>

        {documents.length === 0 ? (
          <div className="p-10 text-center text-slate-500 text-xs font-mono">
            No documents in repository. Upload a file above or click 'Load Sample Documents' on the Dashboard.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 border-b border-slate-800 text-slate-400 uppercase font-mono text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Source / Org</th>
                  <th className="py-3 px-4">Version</th>
                  <th className="py-3 px-4">Topic</th>
                  <th className="py-3 px-4">Doc Date</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-850/40 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                      <span className="truncate max-w-[200px]" title={doc.filename}>{doc.filename}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 truncate max-w-[150px]">{doc.source}</td>
                    <td className="py-3.5 px-4 font-mono">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                        v{doc.version}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{doc.topic}</td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">{doc.document_date || 'N/A'}</td>
                    <td className="py-3.5 px-4 font-mono text-indigo-300">{doc.chunk_count}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleViewChunks(doc.id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                        title="View Extracted Chunks"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-colors"
                        title="Delete Document & Vectors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* View Chunks Modal */}
      {viewingDoc && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  Chunks for: {viewingDoc.filename}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5 font-mono">
                  Version {viewingDoc.version} • {viewingDoc.chunks?.length || 0} indexed vector chunks
                </p>
              </div>
              <button
                onClick={() => setViewingDoc(null)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {viewingDoc.chunks?.map((chk) => (
                <div key={chk.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span>Chunk #{chk.chunk_index + 1}</span>
                    <span>Length: {chk.chunk_text.length} chars</span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed font-sans">
                    {chk.chunk_text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBasePage;
