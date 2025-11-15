import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { RealTimeTaskClient } from '../src/realtimeTaskClient';
import { vi } from 'vitest';

// Mock vscode for any lazy access
vi.mock('vscode', () => ({
  workspace: { getConfiguration: () => ({ get: () => undefined }) },
  window: {},
}));

// Mock eventsource module
vi.mock('eventsource', () => {
  class MockEventSource {
    onopen: ((ev?: any) => void) | null = null;
    onerror: ((err?: any) => void) | null = null;
    onmessage: ((ev: any) => void) | null = null;
    constructor(public url: string, public init?: any) {
      // Immediately fail to trigger reconnect logic
      setTimeout(() => this.onerror && this.onerror(new Error('connect fail')), 0);
    }
    close() {}
  }
  return { default: MockEventSource };
});

describe('RealTimeTaskClient reconnect behavior', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('stops after reaching max reconnect attempts and calls onPermanentFailure', () => {
    const onFail = vi.fn();
    const client = new RealTimeTaskClient('http://localhost:8091/api', 'worker', {
      maxReconnectAttempts: 3,
      heartbeatMs: 0,
      onPermanentFailure: onFail,
    });
    client.start();

    // Run pending timers until the backoff attempts exceed the max
    // Exponential backoff starting at ~1000ms; simulate ~1 minute
    vi.advanceTimersByTime(60_000);

    const state = client.getDebugState();
    expect(onFail).toHaveBeenCalledOnce();
    expect(state.reconnectAttempts).toBeGreaterThanOrEqual(4);

    client.stop();
  });
});
