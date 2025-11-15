import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { createLogger } from './logger';

const logger = createLogger('OfflineQueue');

export interface QueuedResult {
  apiBase: string;
  taskId: string;
  payload: unknown;
  enqueuedAt: number;
  attempts: number;
}

/**
 * Disk-backed queue for task results.
 * Each item is stored as a JSON file under queueDir with name `${enqueuedAt}-${taskId}.json`.
 * Atomicity: write to temp file then rename.
 */
export class OfflineResultQueue {
  private static instance: OfflineResultQueue | undefined;
  private queueDir: string;
  private enabled: boolean;
  private workerTimer?: NodeJS.Timeout;
  private baseBackoffMs = 1000;
  private maxBackoffMs = 30000;
  private isFlushing = false;

  private constructor(queueDir?: string, enabled: boolean = true) {
    this.queueDir = queueDir || this.getDefaultQueueDir();
    this.enabled = enabled;
    this.ensureDir();
  }

  public static getInstance(queueDir?: string, enabled: boolean = true): OfflineResultQueue {
    if (!OfflineResultQueue.instance) {
      OfflineResultQueue.instance = new OfflineResultQueue(queueDir, enabled);
    }
    return OfflineResultQueue.instance;
  }

  private getDefaultQueueDir(): string {
    const appData = process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming');
    return path.join(appData, 'gitko', 'queue');
  }

  private ensureDir() {
    try {
      fs.mkdirSync(this.queueDir, { recursive: true });
    } catch (e) {
      // ignore
    }
  }

  public setEnabled(v: boolean) {
    this.enabled = v;
  }

  public setQueueDir(dir: string) {
    this.queueDir = dir;
    this.ensureDir();
  }

  /** Enqueue a failed submission for later retry */
  public async enqueue(apiBase: string, taskId: string, payload: unknown) {
    if (!this.enabled) return;
    const item: QueuedResult = {
      apiBase,
      taskId,
      payload,
      enqueuedAt: Date.now(),
      attempts: 0,
    };
    const tmpPath = path.join(this.queueDir, `${item.enqueuedAt}-${taskId}.json.tmp`);
    const finalPath = tmpPath.replace(/\.tmp$/, '');
    await fs.promises.writeFile(tmpPath, JSON.stringify(item));
    await fs.promises.rename(tmpPath, finalPath);
    logger.warn(`Enqueued result for offline retry: ${taskId}`);
  }

  /** Start background worker to flush queued results */
  public startWorker(intervalMs: number = 5000) {
    if (this.workerTimer) return;
    this.workerTimer = setInterval(() => {
      this.flush().catch(() => {});
    }, intervalMs);
    logger.info(`Offline queue worker started (interval ${intervalMs}ms)`);
  }

  public stopWorker() {
    if (this.workerTimer) {
      clearInterval(this.workerTimer);
      this.workerTimer = undefined;
      logger.info('Offline queue worker stopped');
    }
  }

  /** Flush once: best-effort submit all items */
  public async flush() {
    if (this.isFlushing) return;
    this.isFlushing = true;
    try {
      const files = await fs.promises.readdir(this.queueDir);
      for (const file of files) {
        if (!file.endsWith('.json')) continue;
        const full = path.join(this.queueDir, file);
        const raw = await fs.promises.readFile(full, 'utf-8');
        let item: QueuedResult;
        try {
          item = JSON.parse(raw) as QueuedResult;
        } catch (e) {
          logger.error(`Corrupted queue file, deleting: ${file}`);
          await fs.promises.unlink(full);
          continue;
        }
        const ok = await this.trySubmit(item);
        if (ok) {
          await fs.promises.unlink(full);
          logger.info(`Flushed queued result: ${item.taskId}`);
        } else {
          // Update attempts/backoff in place
          item.attempts = (item.attempts || 0) + 1;
          const tmp = full + '.tmp';
          await fs.promises.writeFile(tmp, JSON.stringify(item));
          await fs.promises.rename(tmp, full);
        }
      }
    } finally {
      this.isFlushing = false;
    }
  }

  private async trySubmit(item: QueuedResult): Promise<boolean> {
    const url = `${item.apiBase}/tasks/${encodeURIComponent(item.taskId)}/result`;
    const backoff = Math.min(this.baseBackoffMs * Math.pow(2, item.attempts), this.maxBackoffMs);
    if (item.attempts > 0) {
      await new Promise((r) => setTimeout(r, backoff));
    }
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item.payload),
      });
      if (res.ok) return true;
      // Treat idempotent conflicts as success
      if (res.status === 409 || res.status === 208) return true;
      logger.warn(`Retry submit failed HTTP ${res.status} for ${item.taskId}`);
      return false;
    } catch (e) {
      return false;
    }
  }
}
