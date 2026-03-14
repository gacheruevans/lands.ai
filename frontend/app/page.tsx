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
    async function loadFilters() {
      try {
        const payload = await getKnowledgeTopics('KE')
        setAvailableTopics(payload.topics.map((item) => item.topic))
        setAvailableSourceTypes(payload.source_types.map((item) => item.source_type))
      } catch {
        // Soft-fail: query UX should still function even if filter discovery fails.
      }
    }

    void loadFilters()
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

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || loading) {
      return
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: trimmedQuestion,
    }

    setMessages((current) => [...current, userMessage])
    setQuestion('')
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

  return (
    <main className="mx-auto grid min-h-screen w-full max-w-6xl gap-6 px-4 py-6 md:grid-cols-[300px_1fr] md:px-6 md:py-8">
      <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:sticky md:top-6">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-brand-700">lands.ai</h1>
          <p className="text-sm text-slate-600">Kenya Land & Property Legal Assistant</p>
        </div>

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
                      className={`rounded-full border px-3 py-1 text-xs ${
                        active
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
                      className={`rounded-full border px-3 py-1 text-xs ${
                        active
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

      <section className="flex min-h-[75vh] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-4 py-3 md:px-5">
          <p className="text-sm font-medium text-slate-700">Chat</p>
          <p className="text-xs text-slate-500">Grounded answers with citations and confidence metrics</p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50/70 p-4 md:p-5">
          {messages.map((message) => {
            const isUser = message.role === 'user'
            const isSystem = message.role === 'system'

            return (
              <article
                key={message.id}
                className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                    isUser
                      ? 'rounded-br-md bg-brand-700 text-white'
                      : isSystem
                        ? 'rounded-bl-md border border-red-200 bg-red-50 text-red-700'
                        : 'rounded-bl-md border border-slate-200 bg-white text-slate-800'
                  }`}
                >
                  {!isUser && (
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                      {isSystem ? 'System' : 'lands.ai'}
                    </p>
                  )}
                  <p className="whitespace-pre-wrap leading-relaxed">{message.text}</p>

                  {message.result && (
                    <div className="mt-3 space-y-3 border-t border-slate-200 pt-3 text-xs text-slate-600">
                      <p>
                        Evidence confidence: {formatPercent(message.result.evidence_confidence)} · Final confidence:{' '}
                        {formatPercent(message.result.confidence)}
                      </p>

                      {message.result.citations.length > 0 && (
                        <div className="space-y-2">
                          <p className="font-semibold text-slate-700">Citations</p>
                          <ul className="space-y-2">
                            {message.result.citations.map((citation) => (
                              <li key={`${citation.source_id}-${citation.chunk_id}`} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                                <p className="font-medium text-slate-700">
                                  {citation.title}{' '}
                                  <span className="font-normal uppercase text-slate-500">({citation.source_type})</span>
                                </p>
                                <p className="mt-1 text-slate-600">{citation.snippet}</p>
                                <p className="mt-1 text-[11px] text-slate-500">
                                  Score {formatPercent(citation.retrieval_score)} · Terms:{' '}
                                  {citation.matched_terms.length > 0 ? citation.matched_terms.join(', ') : 'none'} · Topics:{' '}
                                  {citation.matched_topics.length > 0 ? citation.matched_topics.join(', ') : 'none'}
                                </p>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <p className="text-amber-700">{message.result.disclaimer}</p>
                    </div>
                  )}
                </div>
              </article>
            )
          })}

          {loading && (
            <article className="flex justify-start">
              <div className="max-w-[85%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">lands.ai</p>
                <p>Checking records and citations…</p>
              </div>
            </article>
          )}
          <div ref={chatEndRef} />
        </div>

        <form onSubmit={onSubmit} className="border-t border-slate-200 bg-white p-4 md:p-5">
          <label htmlFor="question" className="sr-only">
            Ask a legal/property question
          </label>
          <div className="space-y-3">
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask: How much is stamp duty in Nairobi?"
              className="min-h-24 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none ring-brand-500 placeholder:text-slate-400 focus:ring"
              required
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">Tip: filters on the left affect this and all future messages.</p>
              <button
                type="submit"
                disabled={loading || question.trim().length < 3}
                className="rounded-lg bg-brand-700 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? 'Thinking…' : 'Send'}
              </button>
            </div>
          </div>
        </form>
      </section>
    </main>
  )
}
