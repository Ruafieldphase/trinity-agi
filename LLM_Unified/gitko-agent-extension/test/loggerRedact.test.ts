import { describe, it, expect, vi } from 'vitest';
import { Logger, LogLevel } from '../src/logger';

describe('Logger redaction', () => {
  it('redacts emails and tokens', () => {
    const instance = Logger.getInstance();
    // Force INFO level to ensure write occurs
    instance.setLogLevel(LogLevel.INFO);
    const ch: any = { appendLine: vi.fn(), show: vi.fn(), dispose: vi.fn() };
    // @ts-ignore - access private
    instance['channels'].set('Gitko Extension', ch);

    const msg = 'contact john.doe@example.com; Authorization: Bearer ABCD.1234-token';
    // @ts-ignore - access private
    (instance as any).write('INFO', msg, undefined, undefined);
    const line = ch.appendLine.mock.calls[0][0] as string;
    expect(line).not.toContain('john.doe@example.com');
    expect(line).toContain('[REDACTED:email]');
    expect(line).toContain('Bearer [REDACTED:token]');
  });
});
