import EventSource, { MessageEvent } from 'eventsource';
import { createLogger } from './logger';
import { verifyHmacForObject, type HmacConfig } from './security';
import { validateTaskSafe, type Task } from './schemas';
import { HttpTaskPoller } from './httpTaskPoller';

const logger = createLogger('RealtimeClient');

export interface RealtimeClientOptions {
    headers?: Record<string, string>;
    heartbeatMs?: number; // if no messages for this duration, reconnect
    maxReconnectAttempts?: number; // 0 = unlimited
    onPermanentFailure?: () => void; // notify owner to fallback
}

export class RealTimeTaskClient {
    private apiBase: string;
    private workerId: string;
    private es?: EventSource;
    private active = false;
    private reconnectAttempts = 0;
    private readonly maxBackoffMs = 30000;
    private readonly baseBackoffMs = 1000;
    private readonly pollerAdapter: HttpTaskPoller;
    private options: RealtimeClientOptions;
    private heartbeatTimer?: NodeJS.Timeout;
    private lastEventTs = 0;

    constructor(apiBase: string, workerId: string, options?: RealtimeClientOptions) {
        this.apiBase = apiBase;
        this.workerId = workerId;
        // Reuse HttpTaskPoller task handling and submission logic
        this.pollerAdapter = new HttpTaskPoller(apiBase, workerId, 0);
        this.options = options || {};
    }

    public isActive(): boolean {
        return this.active;
    }

    public start() {
        if (this.active) {
            return;
        }
        const url = `${this.apiBase}/tasks/stream?workerId=${encodeURIComponent(this.workerId)}`;
        logger.info(`Starting SSE stream: ${url}`);
        this.connect(url);
    }

    public stop() {
        this.active = false;
        if (this.es) {
            this.es.close();
            this.es = undefined;
        }
        logger.info('Realtime client stopped');
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = undefined;
        }
    }

    private connect(url: string) {
        const init: { headers?: Record<string, string> } = {};
        if (this.options.headers && Object.keys(this.options.headers).length > 0) {
            init.headers = this.options.headers;
        }
        this.es = new EventSource(url, init);
        this.active = true;

        this.es.onopen = () => {
            logger.info('SSE connected');
            this.reconnectAttempts = 0;
            this.lastEventTs = Date.now();
            this.startHeartbeat();
        };

        this.es.onerror = (err: unknown) => {
            let msg: string;
            if (err && typeof err === 'object' && 'message' in (err as Record<string, unknown>)) {
                msg = String((err as Record<string, unknown>).message);
            } else {
                msg = String(err);
            }
            logger.warn(`SSE error: ${msg}`);
            this.es?.close();
            this.active = false;
            this.stopHeartbeat();
            this.scheduleReconnect(url);
        };

        this.es.onmessage = async (ev: MessageEvent) => {
            try {
                const raw = JSON.parse(ev.data);
                const validation = validateTaskSafe(raw as unknown);
                if (!validation.success) {
                    logger.warn(`Invalid task via SSE: ${validation.error}`);
                    return;
                }
                const task = validation.data as Task;
                this.lastEventTs = Date.now();
                // HMAC verification if enabled
                try {
                    // Lazy import to avoid test env hard dependency
                    // eslint-disable-next-line @typescript-eslint/no-var-requires
                    const vscode = require('vscode');
                    const cfg = vscode?.workspace?.getConfiguration?.('gitko');
                    if (cfg) {
                        const hmacCfg: HmacConfig = {
                            enabled: (cfg.get('security.hmac.enabled', false) as boolean) ?? false,
                            secret: (cfg.get('security.hmac.secret', '') as string) || '',
                            signatureField: (cfg.get('security.hmac.signatureField', 'signature') as string) || 'signature',
                            required: (cfg.get('security.hmac.required', true) as boolean) ?? true,
                        };
                        if (hmacCfg.enabled && hmacCfg.secret) {
                            const ok = verifyHmacForObject(task as unknown as Record<string, unknown>, hmacCfg);
                            if (!ok) {
                                logger.warn(`HMAC verification failed for SSE task ${task.task_id}`);
                                return;
                            }
                        }
                    }
                } catch {
                    // ignore if vscode unavailable
                }
                await this.pollerAdapter.handleTask(task);
            } catch (error) {
                logger.error('Failed to process SSE task', error as Error);
            }
        };
    }

    private scheduleReconnect(url: string) {
        this.reconnectAttempts += 1;
        const backoff = Math.min(this.baseBackoffMs * Math.pow(2, this.reconnectAttempts - 1), this.maxBackoffMs);
        const jitter = Math.random() * backoff * 0.1;
        const delay = Math.floor(backoff + jitter);
        const maxAttempts = this.options.maxReconnectAttempts ?? 10;
        if (maxAttempts > 0 && this.reconnectAttempts > maxAttempts) {
            logger.error(`SSE reached max reconnect attempts (${maxAttempts}). Giving up.`);
            this.options.onPermanentFailure?.();
            return;
        }
        logger.info(`Reconnecting SSE in ${delay}ms (attempt #${this.reconnectAttempts})`);
        setTimeout(() => {
            if (!this.active) {
                this.connect(url);
            }
        }, delay);
    }

    private startHeartbeat() {
        const hbMs = this.options.heartbeatMs ?? 15000;
        if (hbMs <= 0) return;
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            const delta = Date.now() - this.lastEventTs;
            if (delta > hbMs) {
                logger.warn(`SSE heartbeat missed (${delta}ms > ${hbMs}ms). Reconnecting...`);
                this.es?.close();
                this.active = false;
                this.stopHeartbeat();
                // Use a small delay to avoid hot loop
                setTimeout(() => this.scheduleReconnect(`${this.apiBase}/tasks/stream?workerId=${encodeURIComponent(this.workerId)}`), 100);
            }
        }, Math.max(Math.floor(hbMs / 2), 500));
    }

    private stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = undefined;
        }
    }

    /**
     * Expose minimal state for testing
     */
    public getDebugState(): { reconnectAttempts: number; active: boolean } {
        return { reconnectAttempts: this.reconnectAttempts, active: this.active };
    }
}
