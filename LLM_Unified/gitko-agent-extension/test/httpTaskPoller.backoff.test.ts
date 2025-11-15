import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { HttpTaskPoller } from '../src/httpTaskPoller';
import { vi } from 'vitest';

// Mock vscode to avoid runtime dependency in tests
vi.mock('vscode', () => ({
  workspace: { getConfiguration: () => ({ get: () => undefined }) },
  window: {},
}));

const makeFailResponse = () => ({
  ok: false,
  status: 500,
  statusText: 'Server Error',
  json: async () => ({}),
}) as unknown as Response;

describe('HttpTaskPoller backoff & circuit breaker', () => {
  const realFetch = global.fetch;

  beforeEach(() => {
    vi.useFakeTimers();
    // Always return HTTP 500 for /tasks/next
    // @ts-expect-error
    global.fetch = vi.fn(async () => makeFailResponse());
  });

  afterEach(() => {
    vi.useRealTimers();
    // @ts-expect-error
    global.fetch = realFetch;
  });

  it('opens circuit after consecutive errors and applies backoff', async () => {
    const poller = new HttpTaskPoller('http://localhost:8091/api', 'tester', 10);
    poller.start();

    // Incrementally drive timers so async fetch/promises flush between polls
    for (let i = 0; i < 12; i++) {
      await vi.advanceTimersByTimeAsync(25);
    }

    const state = poller.getDebugState();
    expect(state.consecutiveErrors).toBeGreaterThanOrEqual(5);
    expect(state.isCircuitOpen).toBe(true);
    expect(state.currentBackoffMs).toBeGreaterThan(0);

    poller.stop();
  });
});
