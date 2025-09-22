import { vi, beforeEach, describe, it, expect } from 'vitest';

vi.mock('../../api/client', () => ({
  api: {
    getSessions: vi.fn(),
    deleteSession: vi.fn(),
  },
}));

vi.mock('../../components/FilePreviewModal', () => ({
  default: () => null,
}));

vi.mock('../../components/DeleteConfirmationModal', () => ({
  default: () => null,
}));

vi.mock('../../components/ResultsModal', () => ({
  default: (props: { isOpen: boolean; sessionId: string }) =>
    props.isOpen ? <div data-testid="results-modal">{props.sessionId}</div> : null,
}));

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';
import { api } from '../../api/client';

const mockedApi = api as unknown as {
  getSessions: ReturnType<typeof vi.fn>;
  deleteSession: ReturnType<typeof vi.fn>;
};

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.getSessions.mockResolvedValue([
      {
        session_id: 'session-42',
        filename: 'results.xlsx',
        status: 'completed',
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      },
    ]);
  });

  it('lists sessions and opens results modal when View Results clicked', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText('results.xlsx')).toBeInTheDocument());

    fireEvent.click(screen.getByText('View Results'));

    expect(await screen.findByTestId('results-modal')).toHaveTextContent('session-42');
    expect(mockedApi.getSessions).toHaveBeenCalled();
  });
});
