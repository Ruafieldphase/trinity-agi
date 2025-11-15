import { describe, it, expect } from 'vitest';
import * as os from 'os';
import * as fs from 'fs';
import * as path from 'path';
import { Logger, createLogger } from '../src/logger';

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe('Logger file sink & redaction', () => {
  it('writes to file and redacts sensitive info', async () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'gitko-log-'));
    const logfile = path.join(tmp, 'test.log');

    const core = Logger.getInstance();
    core.enableFileSink(logfile);

    const log = createLogger('FileTest');
    log.info('Hello john.doe@example.com with Bearer ABCDE12345');

    // wait a moment for appendFile callback to complete
    await wait(20);

    const content = fs.readFileSync(logfile, 'utf-8');
    expect(content).toContain('[REDACTED:email]');
    expect(content).toContain('Bearer [REDACTED:token]');

    core.disableFileSink();
  });
});
