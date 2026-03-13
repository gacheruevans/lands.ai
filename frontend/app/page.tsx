'use client'

import { FormEvent, useEffect, useState } from 'react'
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

export default function HomePage() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [question, setQuestion] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [availableTopics, setAvailableTopics] = useState<string[]>([])
  const [availableSourceTypes, setAvailableSourceTypes] = useState<string[]>([])
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [selectedSourceTypes, setSelectedSourceTypes] = useState<string[]>([])

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
    setError(null)
    setLoading(true)
    setResult(null)

    try {
      const response = await askLegalQuestion(question, {
        topics: selectedTopics,
        source_types: selectedSourceTypes,
      })
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-brand-700">lands.ai</h1>
        <p className="text-slate-600">
          Kenya Land Search & Property Legal AI Assistant (citation-first scaffold)
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-3 rounded-xl border bg-white p-5 shadow-sm">
        <label htmlFor="question" className="block text-sm font-medium text-slate-700">
          Ask a legal/property question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Example: What checks should I do before purchasing land in Kenya?"
          className="min-h-28 w-full rounded-lg border border-slate-300 p-3 outline-none ring-brand-500 focus:ring"
          required
        />

        {availableSourceTypes.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Source type filters</p>
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
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Topic filters</p>
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

        {(selectedSourceTypes.length > 0 || selectedTopics.length > 0) && (
          <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Active filters</p>
              <button
                type="button"
                onClick={clearAllFilters}
                className="text-xs font-medium text-brand-700 hover:underline"
              >
                Clear all
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedSourceTypes.map((value) => (
                <button
                  key={`active-source-${value}`}
                  type="button"
                  onClick={() => toggleSelection(value, selectedSourceTypes, setSelectedSourceTypes)}
                  className="rounded-full border border-brand-200 bg-white px-3 py-1 text-xs text-slate-700"
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
                  className="rounded-full border border-brand-200 bg-white px-3 py-1 text-xs text-slate-700"
                  title="Remove topic filter"
                >
                  topic:{value} ×
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-700 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Checking records…' : 'Ask lands.ai'}
        </button>
      </form>

      {error && <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</p>}

      {result && (
        <section className="space-y-4 rounded-xl border bg-white p-5 shadow-sm">
          <h2 className="text-xl font-semibold">Response</h2>
          <p className="text-slate-800">{result.answer}</p>
          <p className="text-xs text-slate-500">
            Evidence confidence: {(result.evidence_confidence * 100).toFixed(1)}% · Final confidence:{' '}
            {(result.confidence * 100).toFixed(1)}%
          </p>

          <div>
            <h3 className="font-medium">Citations</h3>
            <ul className="mt-2 space-y-2">
              {result.citations.map((c) => (
                <li key={`${c.source_id}-${c.chunk_id}`} className="rounded-md border border-slate-200 p-3">
                  <p className="font-medium text-slate-900">
                    {c.title}{' '}
                    <span className="text-xs font-normal uppercase text-slate-500">({c.source_type})</span>
                  </p>
                  <p className="text-sm text-slate-600">{c.snippet}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Score {(c.retrieval_score * 100).toFixed(1)}% · Terms:{' '}
                    {c.matched_terms.length > 0 ? c.matched_terms.join(', ') : 'none'} · Topics:{' '}
                    {c.matched_topics.length > 0 ? c.matched_topics.join(', ') : 'none'}
                  </p>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-sm text-amber-700">{result.disclaimer}</p>
        </section>
      )}
    </main>
  )
}
