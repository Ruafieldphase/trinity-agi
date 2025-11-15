import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { OfflineResultQueue } from '../src/offlineQueue';

function mkdtemp(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gitko-queue-'));
  return dir;
}

describe('OfflineResultQueue', () => {
  let dir: string;
  beforeEach(() => {
    dir = mkdtemp();
  });

  afterEach(() => {
    try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
  });

  it('enqueues and flushes successfully', async () => {
    const q = OfflineResultQueue.getInstance(dir, true);
    // Monkey-patch trySubmit to simulate success on second attempt
    // @ts-ignore private access (test shim)
    q.trySubmit = async (item: any) => {
      if (item.attempts === 0) return false;
      return true;
    };

    await q.enqueue('http://localhost:8091/api', 't-1', { success: true, data: { ok: 1 } });
    // First flush: will fail and re-write attempts
    await q.flush();
    let files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
    expect(files.length).toBe(1);

    // Second flush: should succeed and remove file
    await q.flush();
    files = fs.readdirSync(dir).filter(f => f.endsWith('.json'));
    expect(files.length).toBe(0);
  });
});
