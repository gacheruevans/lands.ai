'use client'

import { useState, useEffect } from 'react'
import { 
  getAuditEvents,
  ingestDocument, 
  ingestPdfDocument,
  AuditEvent, 
  IngestRequest 
} from '../../lib/api'

export default function AdminDashboard() {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [ingestForm, setIngestForm] = useState<IngestRequest>({
    source_id: '',
    title: '',
    text: '',
    source_type: 'legal_doc',
    jurisdiction: 'KE'
  })
  const [loading, setLoading] = useState(false)
  const [ingestStatus, setIngestStatus] = useState<string | null>(null)
  const [ingestMode, setIngestMode] = useState<'text' | 'pdf'>('text')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  useEffect(() => {
    fetchAuditEvents()
  }, [])

  const fetchAuditEvents = async () => {
    try {
      const response = await getAuditEvents()
      // API returns { "events": [...] }
      setAuditEvents(Array.isArray(response) ? response : (response as any).events || [])
    } catch (error) {
      console.error('Failed to fetch audit events', error)
    }
  }

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setIngestStatus('Ingesting...')
    try {
      if (ingestMode === 'pdf' && selectedFile) {
        await ingestPdfDocument(
          selectedFile,
          ingestForm.source_id,
          ingestForm.title,
          ingestForm.jurisdiction,
          ingestForm.source_type,
          ingestForm.topics || []
        )
      } else {
        await ingestDocument(ingestForm)
      }
      setIngestStatus('Successfully queued for ingestion.')
      setIngestForm({
        source_id: '',
        title: '',
        text: '',
        source_type: 'legal_doc',
        jurisdiction: 'KE'
      })
      setSelectedFile(null)
      fetchAuditEvents()
    } catch (error) {
      setIngestStatus('Ingestion failed.')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8">
      <div className="max-w-6xl mx-auto space-y-12">
        <header className="flex justify-between items-center bg-slate-900/50 backdrop-blur-xl border border-slate-800 p-6 rounded-3xl shadow-2xl">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              lands.ai Admin Control
            </h1>
            <p className="text-slate-400 mt-1 text-sm uppercase tracking-widest font-semibold font-mono">
              Knowledge Ingestion & Audit Trail
            </p>
          </div>
          <a href="/" className="px-5 py-2 rounded-full border border-slate-700 bg-slate-800 hover:bg-slate-700 transition-colors text-sm font-medium">
            ← Knowledge Interface
          </a>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Ingestion Section */}
          <section className="bg-slate-900/40 backdrop-blur-md border border-slate-800 p-8 rounded-3xl shadow-xl">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-3 mb-6">
              <span className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg">↑</span>
              New Knowledge Ingestion
            </h2>
            <form onSubmit={handleIngest} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase ml-1">Source ID</label>
                  <input
                    type="text"
                    placeholder="ke:land:act:2012"
                    className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-mono text-sm"
                    value={ingestForm.source_id}
                    onChange={e => setIngestForm({ ...ingestForm, source_id: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase ml-1">Source Type</label>
                  <select
                    className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm appearance-none"
                    value={ingestForm.source_type}
                    onChange={e => setIngestForm({ ...ingestForm, source_type: e.target.value })}
                  >
                    <option value="legal_doc">Legal Document</option>
                    <option value="procedure">Official Procedure</option>
                    <option value="regulation">County Regulation</option>
                    <option value="fee_schedule">Fee Schedule</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase ml-1">Title</label>
                <input
                  type="text"
                  placeholder="Land Registration Act, 2012"
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm"
                  value={ingestForm.title}
                  onChange={e => setIngestForm({ ...ingestForm, title: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-4 pt-2">
                <div className="flex p-1 bg-slate-950/80 rounded-xl border border-slate-800 w-fit">
                  <button
                    type="button"
                    onClick={() => setIngestMode('text')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${ingestMode === 'text' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    TEXT MODE
                  </button>
                  <button
                    type="button"
                    onClick={() => setIngestMode('pdf')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${ingestMode === 'pdf' ? 'bg-emerald-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    PDF UPLOAD
                  </button>
                </div>

                {ingestMode === 'text' ? (
                  <div className="space-y-2 animate-in fade-in slide-in-from-top-1 duration-300">
                    <label className="text-xs font-semibold text-slate-500 uppercase ml-1">Raw Content</label>
                    <textarea
                      rows={8}
                      placeholder="Paste manual or extracted text here..."
                      className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm resize-none"
                      value={ingestForm.text}
                      onChange={e => setIngestForm({ ...ingestForm, text: e.target.value })}
                      required={ingestMode === 'text'}
                    />
                  </div>
                ) : (
                  <div className="space-y-2 animate-in fade-in slide-in-from-top-1 duration-300">
                    <label className="text-xs font-semibold text-slate-500 uppercase ml-1">PDF Document</label>
                    <div className="relative group">
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        required={ingestMode === 'pdf'}
                      />
                      <div className={`w-full bg-slate-950/50 border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all ${selectedFile ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-slate-800 group-hover:border-slate-700'}`}>
                        <span className="text-2xl mb-2">{selectedFile ? '📄' : '📤'}</span>
                        <p className="text-sm font-medium text-slate-300">
                          {selectedFile ? selectedFile.name : 'Click or drag PDF to upload'}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">Maximum size: 10MB</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98]"
              >
                {loading ? 'Queuing Ingestion...' : 'Execute Ingestion Job'}
              </button>
              {ingestStatus && (
                <p className={`text-center text-sm font-medium ${ingestStatus.includes('failed') ? 'text-red-400' : 'text-emerald-400'}`}>
                  {ingestStatus}
                </p>
              )}
            </form>
          </section>

          {/* Audit Section */}
          <section className="bg-slate-900/40 backdrop-blur-md border border-slate-800 p-8 rounded-3xl shadow-xl flex flex-col h-full">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-3 mb-6">
              <span className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center text-lg">⚖</span>
              Audit Trail
            </h2>
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
              {auditEvents.length === 0 ? (
                <div className="h-full flex items-center justify-center text-slate-600 italic">
                  No events recorded in this session.
                </div>
              ) : (
                auditEvents.map(event => (
                  <div key={event.id} className="p-5 border border-slate-800/50 rounded-2xl bg-slate-950/40 hover:border-slate-700 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-tighter">Event {event.id.slice(0, 8)}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{new Date(event.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-sm font-bold text-slate-200 line-clamp-1 mb-1 italic">"{event.question}"</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-emerald-400" 
                          style={{ width: `${event.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-slate-400">{(event.confidence * 100).toFixed(0)}% confidence</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            <button 
              onClick={fetchAuditEvents}
              className="mt-6 text-xs text-slate-400 hover:text-white transition-colors flex items-center gap-1 justify-center"
            >
              ↻ Refresh logs
            </button>
          </section>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #1e293b;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #334155;
        }
      `}</style>
    </div>
  )
}
