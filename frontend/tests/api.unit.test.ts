import {
  ApiClientError,
  askLegalQuestion,
  getAuditEvents,
  getKnowledgeTopics,
  ingestPdfDocument,
} from '../lib/api'

describe('frontend api client (unit)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends query payload and returns parsed response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          answer: 'Grounded answer',
          citations: [],
          evidence_confidence: 0.75,
          confidence: 0.72,
          disclaimer: 'Informational guidance only.',
          audit_event_id: 'evt-1',
          created_at: '2026-03-15T00:00:00Z',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    vi.stubGlobal('fetch', fetchMock)

    const response = await askLegalQuestion('How do I transfer land?', {
      source_types: ['law'],
      topics: ['transfer'],
    })

    expect(response.answer).toBe('Grounded answer')
    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [, init] = fetchMock.mock.calls[0]
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body).toEqual({
      question: 'How do I transfer land?',
      jurisdiction: 'KE',
      source_types: ['law'],
      topics: ['transfer'],
    })
  })

  it('parses backend error envelope into ApiClientError', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'QUERY_FAILED',
            message: 'Unable to process the legal query right now.',
            details: { request_id: 'abc' },
          },
        }),
        { status: 503, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    vi.stubGlobal('fetch', fetchMock)

    await expect(askLegalQuestion('How do I transfer land?')).rejects.toMatchObject({
      name: 'ApiClientError',
      status: 503,
      code: 'QUERY_FAILED',
      message: 'Unable to process the legal query right now.',
    })
  })

  it('falls back gracefully for non-json errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('Gateway timeout', { status: 504 })),
    )

    await expect(getKnowledgeTopics('KE')).rejects.toMatchObject({
      name: 'ApiClientError',
      status: 504,
      message: 'Topics request failed: Gateway timeout',
    })
  })

  it('normalizes audit events payload shape', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            events: [
              {
                id: '1',
                question: 'q',
                jurisdiction: 'KE',
                answer: 'a',
                citations: [],
                confidence: 0.5,
                created_at: '2026-03-15T00:00:00Z',
              },
            ],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const events = await getAuditEvents(10)
    expect(events).toHaveLength(1)
    expect(events[0].id).toBe('1')
  })

  it('throws ApiClientError for pdf ingest failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ error: { code: 'FILE_INGEST_QUEUE_FAILED', message: 'Unable to queue file ingestion right now.' } }),
          { status: 503, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const file = new File(['pdf-data'], 'sample.pdf', { type: 'application/pdf' })

    await expect(ingestPdfDocument(file, 'src-1', 'Test PDF')).rejects.toBeInstanceOf(ApiClientError)
  })
})
