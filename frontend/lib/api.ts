export type Citation = {
  source_id: string
  chunk_id: string
  title: string
  source_type: string
  snippet: string
  retrieval_score: number
  semantic_score: number
  lexical_score: number
  matched_terms: string[]
  matched_topics: string[]
}

export type QueryResponse = {
  answer: string
  citations: Citation[]
  evidence_confidence: number
  confidence: number
  online_research_used?: boolean
  online_docs_ingested?: number
  suggestions?: string[]
  disclaimer: string
  audit_event_id: string
  created_at: string
}

export type TopicStat = {
  topic: string
  chunk_count: number
}

export type SourceTypeStat = {
  source_type: string
  source_count: number
}

export type KnowledgeTopicsResponse = {
  jurisdiction: string
  topics: TopicStat[]
  source_types: SourceTypeStat[]
}

export type QueryFilters = {
  source_types?: string[]
  topics?: string[]
}

export type AuditEvent = {
  id: string
  question: string
  jurisdiction: string
  answer: string
  citations: any[]
  confidence: number
  created_at: string
}

export type IngestRequest = {
  source_id: string
  title: string
  text: string
  source_type: string
  jurisdiction: string
  topics?: string[]
}

export type StampDutyRequest = {
  property_value: number
  property_type: 'urban' | 'rural' | 'agricultural'
}

export type LandRatesRequest = {
  property_value: number
  county: string
}

export type ApiErrorEnvelope = {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

export class ApiClientError extends Error {
  status: number
  code?: string
  details?: unknown

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
    this.details = details
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'

async function buildApiError(response: Response, fallbackMessage: string): Promise<ApiClientError> {
  const status = response.status
  const raw = await response.text()

  let code: string | undefined
  let details: unknown
  let message = `${fallbackMessage} (status ${status})`

  if (raw) {
    try {
      const parsed = JSON.parse(raw) as ApiErrorEnvelope | { detail?: string | unknown }
      if ('error' in parsed && parsed.error) {
        code = parsed.error.code
        details = parsed.error.details
        if (parsed.error.message) {
          message = parsed.error.message
        }
      } else if ('detail' in parsed) {
        if (typeof parsed.detail === 'string') {
          message = parsed.detail
        } else {
          details = parsed.detail
        }
      }
    } catch {
      message = `${fallbackMessage}: ${raw}`
    }
  }

  return new ApiClientError(message, status, code, details)
}

async function assertOk(response: Response, fallbackMessage: string): Promise<void> {
  if (response.ok) {
    return
  }

  throw await buildApiError(response, fallbackMessage)
}

export async function askLegalQuestion(question: string, filters: QueryFilters = {}): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      jurisdiction: 'KE',
      source_types: filters.source_types ?? [],
      topics: filters.topics ?? [],
    }),
    cache: 'no-store',
  })

  await assertOk(response, 'Request failed')

  return (await response.json()) as QueryResponse
}

export async function getKnowledgeTopics(jurisdiction = 'KE'): Promise<KnowledgeTopicsResponse> {
  const params = new URLSearchParams({ jurisdiction })
  const response = await fetch(`${API_BASE}/knowledge/topics?${params.toString()}`, {
    method: 'GET',
    cache: 'no-store',
  })

  await assertOk(response, 'Topics request failed')

  return (await response.json()) as KnowledgeTopicsResponse
}

export async function getSuggestions(): Promise<{ suggestions: string[] }> {
  const response = await fetch(`${API_BASE}/suggestions`, {
    method: 'GET',
    cache: 'no-store',
  })

  await assertOk(response, 'Suggestions request failed')

  return (await response.json()) as { suggestions: string[] }
}

export async function ingestDocument(payload: IngestRequest): Promise<any> {
  const response = await fetch(`${API_BASE}/knowledge/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  })

  await assertOk(response, 'Ingest failed')

  return await response.json()
}

export async function ingestPdfDocument(
  file: File,
  source_id: string,
  title: string,
  jurisdiction = 'KE',
  source_type = 'law',
  topics: string[] = []
): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('source_id', source_id)
  formData.append('title', title)
  formData.append('jurisdiction', jurisdiction)
  formData.append('source_type', source_type)
  formData.append('topics_json', JSON.stringify(topics))

  const response = await fetch(`${API_BASE}/knowledge/ingest/file`, {
    method: 'POST',
    body: formData,
    cache: 'no-store',
  })

  await assertOk(response, 'File ingest failed')

  return await response.json()
}

export async function getAuditEvents(limit = 20): Promise<AuditEvent[]> {
  const response = await fetch(`${API_BASE}/audit/events?limit=${limit}`, {
    method: 'GET',
    cache: 'no-store',
  })

  await assertOk(response, 'Audit events request failed')

  const payload = (await response.json()) as AuditEvent[] | { events?: AuditEvent[] }
  if (Array.isArray(payload)) {
    return payload
  }
  return payload.events ?? []
}

export async function calculateStampDuty(payload: StampDutyRequest): Promise<any> {
  const response = await fetch(`${API_BASE}/calculators/stamp-duty`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  })

  await assertOk(response, 'Stamp duty calculation failed')

  return await response.json()
}

export async function calculateLandRates(payload: LandRatesRequest): Promise<any> {
  const response = await fetch(`${API_BASE}/calculators/land-rates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  })

  await assertOk(response, 'Land rates calculation failed')

  return await response.json()
}
