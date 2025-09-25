import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../../api/client', () => ({
  api: {
    uploadFile: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('../../components/ResultsModal', () => ({
  default: (props: { isOpen: boolean; sessionId: string }) =>
    props.isOpen ? <div data-testid="results-modal">{props.sessionId}</div> : null,
}));

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Upload from '../Upload';
import { api } from '../../api/client';

const mockedApi = api as unknown as {
  uploadFile: ReturnType<typeof vi.fn>;
};

describe('Upload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.uploadFile.mockResolvedValue({
      session_id: 'session-upload',
      filename: 'sample.xlsx',
      status: 'completed',
      message: 'ok',
      created_at: new Date().toISOString(),
    });
  });

  it('opens results modal after successful upload', async () => {
    const { container } = render(<Upload />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'sample.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    const calculateButton = await screen.findByRole('button', { name: /calculate salt/i });
    fireEvent.click(calculateButton);

    await waitFor(() => expect(mockedApi.uploadFile).toHaveBeenCalled());
    expect(await screen.findByTestId('results-modal')).toHaveTextContent('session-upload');
  });
});
