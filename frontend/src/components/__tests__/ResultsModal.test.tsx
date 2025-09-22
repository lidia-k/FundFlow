import { vi, beforeAll, afterAll, beforeEach, afterEach, describe, it, expect } from 'vitest';

vi.mock('../../api/client', () => ({
  api: {
    getResultsPreview: vi.fn(),
    downloadTaxReport: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  toast: {
    loading: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ResultsModal from '../ResultsModal';
import { api } from '../../api/client';

const mockedApi = api as unknown as {
  getResultsPreview: ReturnType<typeof vi.fn>;
  downloadTaxReport: ReturnType<typeof vi.fn>;
};

describe('ResultsModal', () => {
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

  beforeAll(() => {
    if (!global.URL.createObjectURL) {
      Object.defineProperty(global.URL, 'createObjectURL', {
        value: () => 'blob:mock',
        writable: true,
      });
    }

    if (!global.URL.revokeObjectURL) {
      Object.defineProperty(global.URL, 'revokeObjectURL', {
        value: () => undefined,
        writable: true,
      });
    }

    createObjectURLSpy = vi
      .spyOn(global.URL, 'createObjectURL')
      .mockReturnValue('blob:report');
    revokeObjectURLSpy = vi
      .spyOn(global.URL, 'revokeObjectURL')
      .mockImplementation(() => undefined);
  });

  afterAll(() => {
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.getResultsPreview.mockResolvedValue({
      session_id: 'session-1',
      status: 'completed',
      preview_data: [
        {
          investor_name: 'Alpha LP',
          entity_type: 'Partnership',
          tax_state: 'CA',
          jurisdiction: 'NY',
          amount: 1500,
          fund_code: 'FUND1',
          period: 'Q1 2025',
          composite_tax_amount: 90,
          withholding_tax_amount: 75,
        },
      ],
      total_records: 1,
      preview_limit: 50,
      showing_count: 1,
    });
    mockedApi.downloadTaxReport.mockResolvedValue(new Blob(['csv'], { type: 'text/csv' }));
  });

  afterEach(() => {
    mockedApi.getResultsPreview.mockReset();
    mockedApi.downloadTaxReport.mockReset();
  });

  it('renders tax values when results load succeeds', async () => {
    render(
      <ResultsModal
        isOpen
        onClose={() => undefined}
        sessionId="session-1"
        filename="results.xlsx"
      />
    );

    await waitFor(() => expect(screen.getByText('Withholding Tax NY')).toBeInTheDocument());
    expect(screen.getByText('Composite Tax NY')).toBeInTheDocument();
    expect(screen.getByText('$1,500.00')).toBeInTheDocument();
    expect(screen.getByText('$75.00')).toBeInTheDocument();
    expect(screen.getByText('$90.00')).toBeInTheDocument();
  });

  it('invokes download when clicking Download Report', async () => {
    render(
      <ResultsModal isOpen onClose={() => undefined} sessionId="session-1" filename="results.xlsx" />
    );

    await waitFor(() => expect(screen.getByText('Download Report')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Download Report'));

    await waitFor(() => expect(mockedApi.downloadTaxReport).toHaveBeenCalledWith('session-1'));
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalled();
  });

  it('shows error message when preview fails', async () => {
    mockedApi.getResultsPreview.mockRejectedValueOnce(new Error('network'));

    render(
      <ResultsModal isOpen onClose={() => undefined} sessionId="session-1" filename="results.xlsx" />
    );

    await waitFor(() =>
      expect(screen.getByText('Unable to load calculation results preview')).toBeInTheDocument()
    );
  });
});
