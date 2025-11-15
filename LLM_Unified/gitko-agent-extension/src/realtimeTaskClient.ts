import EventSource, { MessageEvent } from 'eventsource';
import { createLogger } from './logger';
import { validateTaskSafe, type Task } from './schemas';
import { HttpTaskPoller } from './httpTaskPoller';

const logger = createLogger('RealtimeClient');

export class RealTimeTaskClient {
    private apiBase: string;
    private workerId: string;
    private es?: EventSource;
    private active = false;
    private reconnectAttempts = 0;
    private readonly maxBackoffMs = 30000;
    private readonly baseBackoffMs = 1000;
    private readonly pollerAdapter: HttpTaskPoller;

    constructor(apiBase: string, workerId: string) {
        this.apiBase = apiBase;
        this.workerId = workerId;
        // Reuse HttpTaskPoller task handling and submission logic
        this.pollerAdapter = new HttpTaskPoller(apiBase, workerId, 0);
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
    }

    private connect(url: string) {
        this.es = new EventSource(url);
        this.active = true;

        this.es.onopen = () => {
            logger.info('SSE connected');
            this.reconnectAttempts = 0;
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
        logger.info(`Reconnecting SSE in ${delay}ms (attempt #${this.reconnectAttempts})`);
        setTimeout(() => {
            if (!this.active) {
                this.connect(url);
            }
        }, delay);
    }
}
