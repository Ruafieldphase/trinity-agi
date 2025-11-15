import * as vscode from 'vscode';
import { createLogger } from './logger';
import { OfflineResultQueue } from './offlineQueue';
import { PerformanceMonitor } from './performanceMonitor';
import { validateTaskSafe, type Task, type SubmitResult } from './schemas';
import { verifyHmacForObject, type HmacConfig } from './security';

const logger = createLogger('HttpTaskPoller');
const perf = PerformanceMonitor.getInstance();

/**
 * HTTP-based Task Poller for Gitko Extension
 *
 * Polls the Task Queue HTTP API for new tasks and processes them.
 * Replaces the Python http_task_poller.py with native TypeScript implementation.
 *
 * @author Phase 8a Integration
 * @date 2025-10-29
 */

export class HttpTaskPoller {
    private apiBase: string;
    private workerId: string;
    private pollingInterval: number;
    private isPolling: boolean = false;
    private pollTimer?: NodeJS.Timeout;
    private outputCallback?: (message: string) => void;
    private lastUiActionAt: number = 0;
    private minUiActionIntervalMs: number = 150;

    // Backoff and circuit breaker
    private consecutiveErrors: number = 0;
    private readonly maxConsecutiveErrors: number = 5;
    private readonly baseBackoffMs: number = 1000;
    private readonly maxBackoffMs: number = 30000;
    private currentBackoffMs: number = 0;
    private isCircuitOpen: boolean = false;

    constructor(
        apiBase: string = 'http://localhost:8091/api',
        workerId: string = 'gitko-extension',
        pollingInterval: number = 2000
    ) {
        this.apiBase = apiBase;
        this.workerId = workerId;
        this.pollingInterval = pollingInterval;
    }

    /**
     * Set callback for logging output
     */
    setOutputCallback(callback: (message: string) => void) {
        this.outputCallback = callback;
    }

    private log(message: string) {
        if (this.outputCallback) {
            this.outputCallback(message);
        } else {
            logger.info(message);
        }
    }

    /**
     * Start polling for tasks
     */
    start() {
        if (this.isPolling) {
            this.log('[HttpPoller] Already polling');
            return;
        }

        this.log(
            `[HttpPoller] Starting (API: ${this.apiBase}, Worker: ${this.workerId}, Interval: ${this.pollingInterval}ms)`
        );
        this.isPolling = true;
        this.poll();
    }

    /**
     * Stop polling
     */
    stop() {
        this.log('[HttpPoller] Stopping');
        this.isPolling = false;

        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
            this.pollTimer = undefined;
        }
    }

    /**
     * Check if currently polling
     */
    isActive(): boolean {
        return this.isPolling;
    }

    /**
     * Poll for next task
     */
    private async poll() {
        if (!this.isPolling) {
            return;
        }

        // Check circuit breaker
        if (this.isCircuitOpen) {
            if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                this.log(
                    `[HttpPoller] ⚠️ Circuit breaker OPEN (${this.consecutiveErrors} errors). Backing off ${this.currentBackoffMs}ms`
                );
            }
        }

        const opId = perf.startOperation('http.poll');
        try {
            const task = await this.getNextTask();

            if (task) {
                this.log(`[HttpPoller] 📥 Task received: ${task.task_id} (${task.type})`);
                // HMAC verification if enabled
                const cfg = vscode.workspace.getConfiguration('gitko');
                const hmacCfg: HmacConfig = {
                    enabled: (cfg.get('security.hmac.enabled', false) as boolean) ?? false,
                    secret: (cfg.get('security.hmac.secret', '') as string) || '',
                    signatureField: (cfg.get('security.hmac.signatureField', 'signature') as string) || 'signature',
                    required: (cfg.get('security.hmac.required', true) as boolean) ?? true,
                };
                if (hmacCfg.enabled && hmacCfg.secret) {
                    const ok = verifyHmacForObject(task as unknown as Record<string, unknown>, hmacCfg);
                    if (!ok) {
                        this.log(`[HttpPoller] ❌ HMAC verification failed for task ${task.task_id}`);
                        throw new Error('Task signature verification failed');
                    }
                }
                await this.handleTask(task);
            }

            // Success: reset backoff
            this.onSuccess();
            perf.endOperation(opId, true);
        } catch (error) {
            // Error: apply backoff
            this.onError(error);
            perf.endOperation(opId, false, { error: error instanceof Error ? error.message : String(error) });
        }

        // Schedule next poll with backoff
        if (this.isPolling) {
            const interval = this.isCircuitOpen ? this.currentBackoffMs : this.pollingInterval;
            this.pollTimer = setTimeout(() => this.poll(), interval);
        }
    }

    /**
     * Expose internal backoff/circuit state for testing and diagnostics
     */
    public getDebugState(): {
        consecutiveErrors: number;
        currentBackoffMs: number;
        isCircuitOpen: boolean;
    } {
        return {
            consecutiveErrors: this.consecutiveErrors,
            currentBackoffMs: this.currentBackoffMs,
            isCircuitOpen: this.isCircuitOpen,
        };
    }

    /**
     * Handle successful operation - reset backoff
     */
    private onSuccess() {
        if (this.consecutiveErrors > 0 || this.isCircuitOpen) {
            this.log(`[HttpPoller] ✅ Recovered from errors. Resetting backoff.`);
        }
        this.consecutiveErrors = 0;
        this.currentBackoffMs = 0;
        this.isCircuitOpen = false;
    }

    /**
     * Handle error - apply exponential backoff with jitter
     */
    private onError(error: unknown) {
        // Suppress common connection/API errors to reduce noise
        const errorMsg = error instanceof Error ? error.message : String(error);
        const shouldSuppress =
            errorMsg.includes('ECONNREFUSED') ||
            errorMsg.includes('HTTP 405') ||
            errorMsg.includes('Method Not Allowed') ||
            errorMsg.includes('ENOTFOUND') ||
            errorMsg.includes('fetch failed');

        this.consecutiveErrors++;

        // Calculate exponential backoff with jitter
        const baseBackoff = Math.min(this.baseBackoffMs * Math.pow(2, this.consecutiveErrors - 1), this.maxBackoffMs);
        const jitter = Math.random() * baseBackoff * 0.1; // 10% jitter
        this.currentBackoffMs = Math.floor(baseBackoff + jitter);

        // Open circuit breaker if too many errors
        if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
            this.isCircuitOpen = true;
        }

        if (!shouldSuppress || this.consecutiveErrors >= 3) {
            this.log(
                `[HttpPoller] ⚠️ Error #${this.consecutiveErrors}: ${errorMsg} (backoff: ${this.currentBackoffMs}ms)`
            );
        }
    }

    /**
     * Get next task from server
     */
    private async getNextTask(): Promise<Task | null> {
        try {
            const response = await fetch(`${this.apiBase}/tasks/next`, {
                method: 'GET',
                headers: {
                    Accept: 'application/json',
                },
            });

            if (response.status === 204) {
                // No tasks available (normal)
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = (await response.json()) as unknown;

            // Handle empty queue response: {task: null}
            if (
                data &&
                typeof data === 'object' &&
                data !== null &&
                'task' in data &&
                (data as { task: unknown }).task === null
            ) {
                return null;
            }

            // Validate task schema
            if (data) {
                const validation = validateTaskSafe(data);
                if (!validation.success) {
                    this.log(`[HttpPoller] ⚠️ Invalid task schema: ${validation.error}`);
                    return null;
                }
                return validation.data;
            }

            return null;
        } catch (error) {
            if (error instanceof Error) {
                const msg = error.message;
                // Suppress common connection errors
                if (msg.includes('ECONNREFUSED') || msg.includes('fetch failed') || msg.includes('ENOTFOUND')) {
                    return null; // Server not running, silently retry
                }
            }
            throw error;
        }
    }

    /**
     * Handle task based on type
     */
    public async handleTask(task: Task) {
        let result: SubmitResult;
        // Queue latency if provided
        let queueLatencyMs: number | undefined;
        if (task.created_at) {
            const created = Date.parse(task.created_at);
            if (!Number.isNaN(created)) {
                queueLatencyMs = Date.now() - created;
            }
        }

        const opId = perf.startOperation(`http.task.${task.type}`, {
            task_id: task.task_id,
            queueLatencyMs,
        });

        try {
            let resultData: unknown;

            // Handle different task types
            switch (task.type) {
                case 'ping':
                    resultData = await this.handlePing(task);
                    break;

                case 'calculation':
                    resultData = await this.handleCalculation(task.data);
                    break;

                case 'data_transform':
                    resultData = await this.handleDataTransform(task.data);
                    break;

                case 'batch_calculation':
                    resultData = await this.handleBatchCalculation(task.data);
                    break;

                case 'monitoring_report':
                    resultData = await this.handleMonitoringReport(task.data);
                    break;

                // === Computer Use (OCR/RPA) tasks ===
                case 'computer_use.scan':
                    resultData = await this.handleCuScan();
                    break;
                case 'computer_use.find':
                    resultData = await this.handleCuFind(task.data);
                    break;
                case 'computer_use.click':
                    resultData = await this.handleCuClick(task.data);
                    break;
                case 'computer_use.type':
                    resultData = await this.handleCuType(task.data);
                    break;

                default:
                    this.log(`[HttpPoller] ⚠️ Unknown task type: ${task.type}`);
                    throw new Error(`Unknown task type: ${task.type}`);
            }

            result = {
                success: true,
                data: resultData,
            };

            this.log(`[HttpPoller] ✅ Task completed: ${task.task_id}`);
            perf.endOperation(opId, true, { task_id: task.task_id, queueLatencyMs });
        } catch (error) {
            result = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };

            this.log(`[HttpPoller] ❌ Task failed: ${task.task_id} - ${result.error}`);
            perf.endOperation(opId, false, { task_id: task.task_id, queueLatencyMs, error: result.error });
        }

        // Submit result
        await this.submitResult(task.task_id, result);
    }

    /**
     * Submit task result to server
     */
    public async submitResult(taskId: string, result: SubmitResult) {
        const opId = perf.startOperation('http.submit', { task_id: taskId, success: result.success });
        try {
            const response = await fetch(`${this.apiBase}/tasks/${taskId}/result`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(result),
            });

            if (!response.ok) {
                throw new Error(`Failed to submit result: HTTP ${response.status}`);
            }

            this.log(`[HttpPoller] 📤 Result submitted: ${taskId}`);
            perf.endOperation(opId, true, { task_id: taskId });
        } catch (error) {
            this.log(
                `[HttpPoller] ❌ Failed to submit result for ${taskId}: ${error instanceof Error ? error.message : String(error)}`
            );
            perf.endOperation(opId, false, {
                task_id: taskId,
                error: error instanceof Error ? error.message : String(error),
            });
                // Offline queue fallback
                try {
                    const q = OfflineResultQueue.getInstance();
                    await q.enqueue(this.apiBase, taskId, result);
                    this.log(`[HttpPoller] 💾 Queued result for offline retry: ${taskId}`);
                } catch (e) {
                    this.log(`[HttpPoller] ⚠️ Offline queue enqueue failed`);
                }
        }
    }

    // ==================== Task Handlers ====================

    private async handlePing(_task: Task): Promise<{
        message: string;
        worker: string;
        timestamp: string;
        extension: string;
        version: string;
    }> {
        return {
            message: 'pong',
            worker: this.workerId,
            timestamp: new Date().toISOString(),
            extension: 'gitko-agent-extension',
            version: '2.0.0',
        };
    }

    private async handleCalculation(data: unknown): Promise<{
        result: number;
        operation: string;
        input: number[];
    }> {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }

        const { operation, numbers } = data as { operation?: string; numbers?: unknown };

        if (!operation || typeof operation !== 'string') {
            throw new Error('Invalid data: operation string required');
        }

        if (!numbers || !Array.isArray(numbers)) {
            throw new Error('Invalid data: numbers array required');
        }

        const numArray = numbers as number[];
        let result = 0;

        if (operation === 'add') {
            result = numArray.reduce((a, b) => a + b, 0);
        } else if (operation === 'multiply') {
            result = numArray.reduce((a, b) => a * b, 1);
        } else if (operation === 'divide' && numArray.length === 2) {
            if (numArray[1] === 0) {
                throw new Error('Division by zero');
            }
            result = numArray[0] / numArray[1];
        } else if (operation === 'average') {
            result = numArray.reduce((a, b) => a + b, 0) / numArray.length;
        } else {
            throw new Error(`Unsupported operation: ${operation}`);
        }

        return {
            result,
            operation,
            input: numArray,
        };
    }

    private async handleDataTransform(data: unknown): Promise<{ result: string | number }> {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }

        const { operation, text } = data as { operation?: string; text?: string };

        if (!text || typeof text !== 'string') {
            throw new Error('Invalid data: text field required');
        }

        if (!operation || typeof operation !== 'string') {
            throw new Error('Invalid data: operation field required');
        }

        if (operation === 'uppercase') {
            return { result: text.toUpperCase() };
        } else if (operation === 'lowercase') {
            return { result: text.toLowerCase() };
        } else if (operation === 'reverse') {
            return { result: text.split('').reverse().join('') };
        } else if (operation === 'length') {
            return { result: text.length };
        }

        throw new Error(`Unknown operation: ${operation}`);
    }

    private async handleBatchCalculation(data: unknown): Promise<{
        calculations: Array<{ id: string | number; result: number | null; status: 'success' | 'error'; error?: string }>;
        total: number;
        successful: number;
    }> {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }

        const req = data as { calculations?: Array<{ id?: unknown; operation?: unknown; numbers?: unknown; multiply_by?: unknown }> };
        const calculations = Array.isArray(req.calculations) ? req.calculations : [];
        const results: Array<{ id: string | number; result: number | null; status: 'success' | 'error'; error?: string }> = [];

        for (const calc of calculations) {
            const id = (calc && calc.id) as unknown;
            const operation = (calc && calc.operation) as unknown;
            const numbers = (calc && calc.numbers) as unknown;
            const multiply_by = (calc && calc.multiply_by) as unknown;

            try {
                let result = 0;

                if (operation === 'divide' && Array.isArray(numbers) && numbers.length === 2) {
                    if (numbers[1] === 0) {
                        throw new Error('Division by zero');
                    }
                    result = Number(numbers[0]) / Number(numbers[1]);
                    if (typeof multiply_by === 'number') {
                        result *= multiply_by;
                    }
                } else if (operation === 'average' && Array.isArray(numbers) && numbers.length > 0) {
                    const arr = numbers.map((n) => Number(n));
                    result = arr.reduce((a, b) => a + b, 0) / arr.length;
                } else if (operation === 'multiply' && Array.isArray(numbers)) {
                    const arr = numbers.map((n) => Number(n));
                    result = arr.reduce((a, b) => a * b, 1);
                } else if (operation === 'add' && Array.isArray(numbers)) {
                    const arr = numbers.map((n) => Number(n));
                    result = arr.reduce((a, b) => a + b, 0);
                }

                results.push({ id: (typeof id === 'string' || typeof id === 'number') ? id : String(id), result, status: 'success' });
            } catch (error) {
                results.push({
                    id: (typeof id === 'string' || typeof id === 'number') ? id : String(id),
                    result: null,
                    status: 'error',
                    error: error instanceof Error ? error.message : String(error),
                });
            }
        }

        return {
            calculations: results,
            total: calculations.length,
            successful: results.filter((r) => r.status === 'success').length,
        };
    }

    private async handleMonitoringReport(data: unknown): Promise<{ message: string; requested_hours: number | undefined; requested_metrics: unknown[]; suggestion: string }> {
        // Placeholder for monitoring report generation
        // This could be extended to call Gitko agents or generate reports
        const d = (data && typeof data === 'object') ? (data as { hours?: unknown; metrics?: unknown[] }) : {};
        return {
            message: 'Monitoring report generation not yet implemented in extension',
            requested_hours: typeof d.hours === 'number' ? d.hours : undefined,
            requested_metrics: Array.isArray(d.metrics) ? d.metrics : [],
            suggestion: 'Use Python scripts for full monitoring reports',
        };
    }

    // ==================== Computer Use handlers ====================
    private async handleCuScan(): Promise<{ elements: unknown[] }> {
        this.ensureCuEnabled();
        const guard = (await import('./securityGuardrails')).SecurityGuardrails.getInstance();
        const chk = await guard.checkAction('computer_use.scan', {});
        if (!chk.allowed) throw new Error(chk.reason || 'Security policy rejected action');
        const { ComputerUseAgent } = await import('./computerUse');
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const elements = await agent.scanScreen();
        logger.info(`Scanned screen: ${elements.length} elements found`);
        return { elements };
    }

    private async handleCuFind(data: unknown): Promise<{ element: unknown }> {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }

        const { text } = data as { text?: unknown };

        if (typeof text !== 'string' || !text.trim()) {
            throw new Error('Invalid data: { text: string } required');
        }

        this.ensureCuEnabled();
        const guard = (await import('./securityGuardrails')).SecurityGuardrails.getInstance();
        const chk = await guard.checkAction('computer_use.find', { text });
        if (!chk.allowed) throw new Error(chk.reason || 'Security policy rejected action');
        const { ComputerUseAgent } = await import('./computerUse');
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const element = await agent.findElementByText(text);
        logger.info(`Found element: ${text}`);
        return { element };
    }

    private async handleCuClick(data: unknown): Promise<{ success: boolean }> {
        this.ensureCuEnabled();
        const guard = (await import('./securityGuardrails')).SecurityGuardrails.getInstance();
        const { ComputerUseAgent } = await import('./computerUse');
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();

        let ok = false;

        if (data && typeof data === 'object') {
            const clickData = data as { x?: unknown; y?: unknown; text?: unknown };

            if (typeof clickData.x === 'number' && typeof clickData.y === 'number') {
                const chk = await guard.checkAction('computer_use.click', { x: clickData.x, y: clickData.y });
                if (!chk.allowed) throw new Error(chk.reason || 'Security policy rejected action');
                ok = await agent.clickAt(clickData.x, clickData.y);
                logger.info(`Clicked at (${clickData.x}, ${clickData.y})`);
            } else if (typeof clickData.text === 'string' && clickData.text.trim()) {
                const chk = await guard.checkAction('computer_use.click', { text: clickData.text });
                if (!chk.allowed) throw new Error(chk.reason || 'Security policy rejected action');
                ok = await agent.clickElementByText(clickData.text);
                logger.info(`Clicked element: ${clickData.text}`);
            } else {
                throw new Error('Invalid data: provide either { x:number, y:number } or { text:string }');
            }
        } else {
            throw new Error('Invalid data: object required');
        }

        return { success: ok };
    }

    private async handleCuType(data: unknown): Promise<{ success: boolean }> {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }

        const { text } = data as { text?: unknown };

        if (typeof text !== 'string') {
            throw new Error('Invalid data: { text: string } required');
        }

        this.ensureCuEnabled();
        const guard = (await import('./securityGuardrails')).SecurityGuardrails.getInstance();
        const chk = await guard.checkAction('computer_use.type', { text });
        if (!chk.allowed) throw new Error(chk.reason || 'Security policy rejected action');
        const { ComputerUseAgent } = await import('./computerUse');
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const ok = await agent.type(text);
        logger.info(`Typed text: ${text.substring(0, 20)}...`);
        return { success: ok };
    }

    private async enforceUiCooldown(): Promise<void> {
        const cfg = vscode.workspace.getConfiguration('gitko');
        const interval = cfg.get<number>('minUiActionIntervalMs', 150);
        if (typeof interval === 'number' && interval >= 0) {
            this.minUiActionIntervalMs = interval;
        }
        const now = Date.now();
        const elapsed = now - this.lastUiActionAt;
        if (elapsed < this.minUiActionIntervalMs) {
            await new Promise((res) => setTimeout(res, this.minUiActionIntervalMs - elapsed));
        }
        this.lastUiActionAt = Date.now();
    }

    private ensureCuEnabled(): void {
        const cfg = vscode.workspace.getConfiguration('gitko');
        const enabled = cfg.get<boolean>('enableComputerUseOverHttp', true);
        if (!enabled) {
            throw new Error('Computer Use over HTTP is disabled by settings (gitko.enableComputerUseOverHttp=false)');
        }
    }
}
