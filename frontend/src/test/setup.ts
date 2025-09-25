import '@testing-library/jest-dom';
import { vi } from 'vitest';

if (typeof window.URL.createObjectURL !== 'function') {
  Object.defineProperty(window.URL, 'createObjectURL', {
    value: vi.fn(() => 'blob:mock'),
    writable: true,
  });
}

if (typeof window.URL.revokeObjectURL !== 'function') {
  Object.defineProperty(window.URL, 'revokeObjectURL', {
    value: vi.fn(),
    writable: true,
  });
}

if (typeof HTMLAnchorElement.prototype.click !== 'function' ||
  HTMLAnchorElement.prototype.click === HTMLElement.prototype.click) {
  Object.defineProperty(HTMLAnchorElement.prototype, 'click', {
    value: vi.fn(),
    writable: true,
  });
}
