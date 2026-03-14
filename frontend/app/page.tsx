'use client'

import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'

import { askLegalQuestion, getKnowledgeTopics, QueryResponse } from '../lib/api'

const URL_KEY_SOURCE_TYPES = 'source_types'
const URL_KEY_TOPICS = 'topics'

function parseCsvParam(value: string | null): string[] {
  if (!value) {
    return []
  }
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function sortedUnique(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b))
}

type ChatMessage = {
  id: string
  role: 'user' | 'assistant' | 'system'
  text: string
  result?: QueryResponse
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export default function HomePage() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'assistant-welcome',
      role: 'assistant',
      text: 'Hi, I’m lands.ai. Ask any Kenya land/property legal process question and I’ll respond with grounded citations.',
    },
  ])
  const [loading, setLoading] = useState(false)
  const [availableTopics, setAvailableTopics] = useState<string[]>([])
  const [availableSourceTypes, setAvailableSourceTypes] = useState<string[]>([])
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [selectedSourceTypes, setSelectedSourceTypes] = useState<string[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const chatEndRef = useRef<HTMLDivElement | null>(null)

  const activeFilters = useMemo(
    () => [...selectedSourceTypes.map((v) => `source:${v}`), ...selectedTopics.map((v) => `topic:${v}`)],
    [selectedSourceTypes, selectedTopics],
  )

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const incomingTopics = sortedUnique(parseCsvParam(searchParams.get(URL_KEY_TOPICS)))
    const incomingSourceTypes = sortedUnique(parseCsvParam(searchParams.get(URL_KEY_SOURCE_TYPES)))

    setSelectedTopics((current) => {
      const currentSerialized = current.join(',')
      const incomingSerialized = incomingTopics.join(',')
      return currentSerialized === incomingSerialized ? current : incomingTopics
    })

    setSelectedSourceTypes((current) => {
      const currentSerialized = current.join(',')
      const incomingSerialized = incomingSourceTypes.join(',')
      return currentSerialized === incomingSerialized ? current : incomingSourceTypes
    })
  }, [searchParams])

  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString())

    const normalizedTopics = sortedUnique(selectedTopics)
    const normalizedSourceTypes = sortedUnique(selectedSourceTypes)

    if (normalizedTopics.length > 0) {
      params.set(URL_KEY_TOPICS, normalizedTopics.join(','))
    } else {
      params.delete(URL_KEY_TOPICS)
    }

    if (normalizedSourceTypes.length > 0) {
      params.set(URL_KEY_SOURCE_TYPES, normalizedSourceTypes.join(','))
    } else {
      params.delete(URL_KEY_SOURCE_TYPES)
    }

    const nextQuery = params.toString()
    const currentQuery = searchParams.toString()
    if (nextQuery !== currentQuery) {
      const nextUrl = nextQuery ? `${pathname}?${nextQuery}` : pathname
      router.replace(nextUrl, { scroll: false })
    }
  }, [pathname, router, searchParams, selectedSourceTypes, selectedTopics])

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [topicsPayload, suggestionsPayload] = await Promise.all([
          getKnowledgeTopics('KE'),
          import('../lib/api').then(m => m.getSuggestions())
        ])
        setAvailableTopics(topicsPayload.topics.map((item) => item.topic))
        setAvailableSourceTypes(topicsPayload.source_types.map((item) => item.source_type))
        setSuggestions(suggestionsPayload.suggestions)
      } catch {
        // Soft-fail: query UX should still function even if filter discovery fails.
      }
    }

    void loadInitialData()
  }, [])

  function toggleSelection(value: string, current: string[], set: (values: string[]) => void) {
    if (current.includes(value)) {
      set(current.filter((item) => item !== value))
      return
    }
    set([...current, value])
  }

  function clearAllFilters() {
    setSelectedTopics([])
    setSelectedSourceTypes([])
  }

  async function handleAsk(questionToAsk?: string) {
    const trimmedQuestion = (questionToAsk || question).trim()
    if (!trimmedQuestion || loading) {
      return
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: trimmedQuestion,
    }

    setMessages((current) => [...current, userMessage])
    if (!questionToAsk) setQuestion('')
    setLoading(true)

    try {
      const response = await askLegalQuestion(trimmedQuestion, {
        topics: selectedTopics,
        source_types: selectedSourceTypes,
      })

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.answer,
        result: response,
      }
      setMessages((current) => [...current, assistantMessage])
    } catch (err) {
      const errText = err instanceof Error ? err.message : 'Unexpected error'
      const systemMessage: ChatMessage = {
        id: `system-${Date.now()}`,
        role: 'system',
        text: `I hit an error while contacting the backend: ${errText}`,
      }
      setMessages((current) => [...current, systemMessage])
    } finally {
      setLoading(false)
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void handleAsk()
  }

  return (
    <main className="mx-auto grid min-h-screen w-full max-w-6xl gap-6 px-4 py-6 md:grid-cols-[300px_1fr] md:px-6 md:py-8 transition-colors duration-500">
      <aside className="h-fit rounded-3xl border border-white/40 bg-white/60 p-5 shadow-xl backdrop-blur-md md:sticky md:top-6 ring-1 ring-black/5">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-brand-700">lands.ai</h1>
          <a href="/admin" id="admin-link-sidebar" className="text-[10px] font-bold text-slate-400 hover:text-brand-600 transition-colors uppercase tracking-widest border border-slate-200 rounded px-1.5 py-0.5">Admin</a>
        </div>
        <p className="text-sm text-slate-600">Kenya Land & Property Legal Assistant</p>

        <div className="mt-5 space-y-4">
          {availableSourceTypes.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Source type filters</p>
              <div className="flex flex-wrap gap-2">
                {availableSourceTypes.map((sourceType) => {
                  const active = selectedSourceTypes.includes(sourceType)
                  return (
                    <button
                      key={sourceType}
                      type="button"
                      onClick={() => toggleSelection(sourceType, selectedSourceTypes, setSelectedSourceTypes)}
                      className={`rounded-full border px-3 py-1 text-xs ${active
                        ? 'border-brand-700 bg-brand-50 text-brand-700'
                        : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                    >
                      {sourceType}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {availableTopics.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Topic filters</p>
              <div className="flex flex-wrap gap-2">
                {availableTopics.map((topic) => {
                  const active = selectedTopics.includes(topic)
                  return (
                    <button
                      key={topic}
                      type="button"
                      onClick={() => toggleSelection(topic, selectedTopics, setSelectedTopics)}
                      className={`rounded-full border px-3 py-1 text-xs ${active
                        ? 'border-brand-700 bg-brand-50 text-brand-700'
                        : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                    >
                      {topic}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Active filters</p>
              <button
                type="button"
                onClick={clearAllFilters}
                className="text-xs font-medium text-brand-700 hover:underline"
                disabled={activeFilters.length === 0}
              >
                Clear all
              </button>
            </div>
            {activeFilters.length === 0 ? (
              <p className="text-xs text-slate-500">No filters selected</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {selectedSourceTypes.map((value) => (
                  <button
                    key={`active-source-${value}`}
                    type="button"
                    onClick={() => toggleSelection(value, selectedSourceTypes, setSelectedSourceTypes)}
                    className="rounded-full border border-brand-200 bg-white px-2.5 py-1 text-xs text-slate-700"
                    title="Remove source filter"
                  >
                    source:{value} ×
                  </button>
                ))}
                {selectedTopics.map((value) => (
                  <button
                    key={`active-topic-${value}`}
                    type="button"
                    onClick={() => toggleSelection(value, selectedTopics, setSelectedTopics)}
                    className="rounded-full border border-brand-200 bg-white px-2.5 py-1 text-xs text-slate-700"
                    title="Remove topic filter"
                  >
                    topic:{value} ×
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>

      <section className="flex min-h-[85vh] flex-col overflow-hidden rounded-3xl border border-white bg-white/70 shadow-2xl backdrop-blur-lg ring-1 ring-black/5">
        <div className="flex items-center justify-between border-b border-slate-100 bg-white/50 px-6 py-4 backdrop-blur-sm">
          <div>
            <p className="text-sm font-bold text-slate-800">Legal Consultation</p>
            <p className="text-[10px] font-medium text-slate-500">Verified Kenyan Legal Intelligence</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500 ring-4 ring-green-100"></span>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Live</span>
          </div>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-4 md:p-6 custom-scrollbar bg-gradient-to-b from-white/50 to-slate-50/50">
          {messages.map((message) => {
            const isUser = message.role === 'user'
            const isSystem = message.role === 'system'

            return (
              <article
                key={message.id}
                className={`flex transform transition-all duration-300 ease-out animate-in slide-in-from-bottom-2 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[90%] md:max-w-[80%] rounded-2xl px-5 py-3.5 text-sm shadow-sm transition-all duration-300 ${isUser
                    ? 'rounded-tr-none bg-gradient-to-br from-brand-700 to-brand-800 text-white shadow-brand-100 hover:shadow-md'
                    : isSystem
                      ? 'rounded-tl-none border border-red-100 bg-red-50 text-red-700'
                      : 'rounded-tl-none border border-slate-100 bg-white text-slate-700 ring-1 ring-black/[0.02] hover:shadow-md'
                    }`}
                >
                  {!isUser && (
                    <div className="mb-2 flex items-center gap-2">
                      <span className={`h-1.5 w-1.5 rounded-full ${isSystem ? 'bg-red-400' : 'bg-brand-500'}`}></span>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                        {isSystem ? 'System' : 'lands.ai'}
                      </p>
                    </div>
                  )}
                  <p className="whitespace-pre-wrap leading-relaxed font-medium">{message.text}</p>

                  {message.result && (
                    <div className="mt-4 space-y-4 border-t border-slate-100 pt-4">
                      <div className="flex flex-wrap gap-3 text-[10px] font-bold uppercase tracking-wider">
                        <div className="flex items-center gap-1.5 rounded-md bg-slate-50 px-2 py-1 text-slate-500 ring-1 ring-black/[0.03]">
                          <span>Evidence:</span> <span className="text-slate-800">{formatPercent(message.result.evidence_confidence)}</span>
                        </div>
                        <div className="flex items-center gap-1.5 rounded-md bg-slate-50 px-2 py-1 text-slate-500 ring-1 ring-black/[0.03]">
                          <span>Final:</span> <span className="text-slate-800">{formatPercent(message.result.confidence)}</span>
                        </div>
                      </div>

                      {message.result.citations.length > 0 && (
                        <div className="space-y-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Supporting Citations</p>
                          <div className="grid gap-3 sm:grid-cols-1">
                            {message.result.citations.map((citation) => (
                              <div key={`${citation.source_id}-${citation.chunk_id}`} className="group relative overflow-hidden rounded-xl border border-slate-100 bg-slate-50/50 p-4 transition-all duration-200 hover:bg-white hover:shadow-lg hover:ring-1 hover:ring-brand-100">
                                <div className="flex items-center justify-between mb-2">
                                  <p className="font-bold text-slate-800 text-xs">
                                    {citation.title}
                                  </p>
                                  <span className="rounded-full bg-white px-2 py-0.5 text-[9px] font-extrabold uppercase text-brand-600 ring-1 ring-brand-100 shadow-sm">
                                    {citation.source_type}
                                  </span>
                                </div>
                                <p className="text-xs leading-relaxed text-slate-600 line-clamp-3 italic">"{citation.snippet}"</p>
                                <div className="mt-3 flex flex-wrap items-center gap-2">
                                  <span className="text-[9px] font-bold text-slate-400 uppercase">Match Score: {formatPercent(citation.retrieval_score)}</span>
                                  {citation.matched_topics.length > 0 && (
                                    <div className="flex gap-1">
                                      {citation.matched_topics.map(t => (
                                        <span key={t} className="text-[8px] font-bold text-brand-500 bg-brand-50/50 px-1.5 py-0.5 rounded uppercase">#{t}</span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {message.result.suggestions && message.result.suggestions.length > 0 && (
                        <div className="space-y-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Suggested Follow-ups</p>
                          <div className="flex flex-wrap gap-2">
                            {message.result.suggestions.map((s, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleAsk(s)}
                                className="rounded-full bg-brand-50/50 px-3 py-1 text-[10px] font-bold text-brand-700 border border-brand-100 hover:bg-brand-100 transition-all duration-200"
                              >
                                {s}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="rounded-lg bg-amber-50/50 p-3 ring-1 ring-amber-100/50">
                        <p className="text-[10px] font-bold italic text-amber-700 leading-tight">⚠ {message.result.disclaimer}</p>
                      </div>
                    </div>
                  )}
                </div>
              </article>
            )
          })}

          {loading && (
            <article className="flex justify-start animate-pulse">
              <div className="max-w-[80%] rounded-2xl rounded-tl-none border border-slate-100 bg-white px-5 py-3.5 text-sm text-slate-500 shadow-sm shadow-slate-100 ring-1 ring-black/[0.02]">
                <div className="mb-2 flex items-center gap-2">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-500"></span>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">lands.ai</p>
                </div>
                <p className="font-medium italic">Consulting local registry and Wikipedia references…</p>
              </div>
            </article>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="border-t border-slate-100 bg-white p-5 md:p-6 lg:p-8 space-y-4">
          {suggestions.length > 0 && messages.length < 3 && (
            <div className="space-y-2">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 px-1">Suggested Questions</p>
              <div className="flex flex-wrap gap-2 pb-1 overflow-x-auto no-scrollbar">
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAsk(s)}
                    className="whitespace-nowrap rounded-full bg-slate-50 px-3.5 py-1.5 text-xs font-semibold text-slate-700 border border-slate-100 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700 transition-all duration-200"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={onSubmit} className="relative group">
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Start typing your land question here..."
              className="min-h-32 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50/30 p-4 pt-5 pr-16 text-sm outline-none transition-all duration-300 font-medium placeholder:text-slate-400 focus:border-brand-300 focus:bg-white focus:ring-4 focus:ring-brand-500/10 active:border-brand-400 group-hover:border-slate-300"
              required
            />
            <button
              type="submit"
              disabled={loading || question.trim().length < 3}
              className={`absolute bottom-4 right-4 flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-300 shadow-md ${question.trim().length >= 3
                  ? 'bg-brand-700 text-white shadow-brand-200 hover:bg-brand-800 hover:scale-105 active:scale-95'
                  : 'bg-blue-400 text-slate-400 cursor-not-allowed grayscale'
                }`}
            >
              {loading ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
              ) : (
                <svg className="h-5 w-5 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </form>
          <div className="flex items-center justify-between px-1">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Shift + Enter to send</p>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Active Filters: {activeFilters.length}</p>
          </div>
        </div>
      </section>
    </main>
  )
}
