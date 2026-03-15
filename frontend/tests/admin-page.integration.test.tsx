import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import AdminDashboard from '../app/admin/page'
import { getAuditEvents, ingestDocument, ingestPdfDocument } from '../lib/api'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>()
  return {
    ...actual,
    getAuditEvents: vi.fn(),
    ingestDocument: vi.fn(),
    ingestPdfDocument: vi.fn(),
  }
})

describe('Admin dashboard integration', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(getAuditEvents).mockResolvedValue([])
    vi.mocked(ingestPdfDocument).mockResolvedValue({ source_id: 'src-1' })
    vi.mocked(ingestDocument).mockResolvedValue({ source_id: 'src-1' })
  })

  it('loads audit data and submits text ingestion successfully', async () => {
    render(<AdminDashboard />)

    await waitFor(() => {
      expect(getAuditEvents).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByText('No events recorded in this session.')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('ke:land:act:2012'), {
      target: { value: 'ke:land:act:2012' },
    })
    fireEvent.change(screen.getByPlaceholderText('Land Registration Act, 2012'), {
      target: { value: 'Land Registration Act, 2012' },
    })
    fireEvent.change(screen.getByPlaceholderText('Paste manual or extracted text here...'), {
      target: { value: 'This is a long enough legal document text for ingestion in tests.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Execute Ingestion Job' }))

    await waitFor(() => {
      expect(ingestDocument).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByText('Successfully queued for ingestion.')).toBeInTheDocument()
  })

  it('shows graceful error message when ingestion fails', async () => {
    vi.mocked(ingestDocument).mockRejectedValue(new Error('Backend unavailable'))

    render(<AdminDashboard />)

    fireEvent.change(screen.getByPlaceholderText('ke:land:act:2012'), {
      target: { value: 'ke:land:act:2012' },
    })
    fireEvent.change(screen.getByPlaceholderText('Land Registration Act, 2012'), {
      target: { value: 'Land Registration Act, 2012' },
    })
    fireEvent.change(screen.getByPlaceholderText('Paste manual or extracted text here...'), {
      target: { value: 'This is a long enough legal document text for ingestion in tests.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Execute Ingestion Job' }))

    await waitFor(() => {
      expect(screen.getByText(/Ingestion failed:/)).toBeInTheDocument()
    })
  })
})
