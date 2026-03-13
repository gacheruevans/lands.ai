'use client'

import { FormEvent, useState } from 'react'

import { askLegalQuestion, QueryResponse } from '../lib/api'

export default function HomePage() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setLoading(true)
    setResult(null)

    try {
      const response = await askLegalQuestion(question)
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

          <div>
            <h3 className="font-medium">Citations</h3>
            <ul className="mt-2 space-y-2">
              {result.citations.map((c) => (
                <li key={`${c.source_id}-${c.chunk_id}`} className="rounded-md border border-slate-200 p-3">
                  <p className="font-medium text-slate-900">{c.title}</p>
                  <p className="text-sm text-slate-600">{c.snippet}</p>
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
