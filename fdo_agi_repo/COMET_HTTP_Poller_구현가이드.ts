/**
 * HTTP-based Task Poller for Comet Extension
 * 
 * This TypeScript code can be integrated into the Comet VS Code extension
 * to poll for tasks via HTTP instead of file system watching.
 * 
 * Add this to: src/agent_tools/httpTaskPoller.ts
 */

interface Task {
    id: string;
    type: string;
    data: any;
    requester: string;
    status: string;
    created_at: string;
}

interface TaskResult {
    task_id: string;
    worker: string;
    status: 'success' | 'error';
    data: any;
    error_message?: string;
}

export class HttpTaskPoller {
    private apiBase: string;
    private workerId: string;
    private pollingInterval: number;
    private isPolling: boolean = false;
    private pollTimer?: NodeJS.Timeout;

    constructor(apiBase: string = 'http://localhost:8091/api', workerId: string = 'comet-extension') {
        this.apiBase = apiBase;
        this.workerId = workerId;
        this.pollingInterval = 2000; // 2 seconds
    }

    /**
     * Start polling for tasks
     */
    start() {
        if (this.isPolling) {
            console.log('[HttpPoller] Already polling');
            return;
        }

        console.log(`[HttpPoller] Starting (${this.apiBase})`);
        this.isPolling = true;
        this.poll();
    }

    /**
     * Stop polling
     */
    stop() {
        console.log('[HttpPoller] Stopping');
        this.isPolling = false;

        if (this.pollTimer) {
            clearTimeout(this.pollTimer);
            this.pollTimer = undefined;
        }
    }

    /**
     * Poll for next task
     */
    private async poll() {
        if (!this.isPolling) {
            return;
        }

        try {
            const task = await this.getNextTask();

            if (task) {
                console.log(`[HttpPoller] Got task: ${task.id} (${task.type})`);
                await this.handleTask(task);
            }
        } catch (error) {
            console.error('[HttpPoller] Error:', error);
        }

        // Schedule next poll
        if (this.isPolling) {
            this.pollTimer = setTimeout(() => this.poll(), this.pollingInterval);
        }
    }

    /**
     * Get next task from server
     */
    private async getNextTask(): Promise<Task | null> {
        try {
            const response = await fetch(`${this.apiBase}/tasks/next`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    worker_id: this.workerId
                })
            });

            if (response.status === 404) {
                // No tasks available
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.task || null;

        } catch (error) {
            if (error instanceof Error && error.message.includes('ECONNREFUSED')) {
                // Server not running, silently retry
                return null;
            }
            throw error;
        }
    }

    /**
     * Handle task based on type
     */
    private async handleTask(task: Task) {
        let result: TaskResult;

        try {
            let resultData: any;

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

                default:
                    throw new Error(`Unknown task type: ${task.type}`);
            }

            result = {
                task_id: task.id,
                worker: this.workerId,
                status: 'success',
                data: resultData
            };

        } catch (error) {
            result = {
                task_id: task.id,
                worker: this.workerId,
                status: 'error',
                data: {},
                error_message: error instanceof Error ? error.message : String(error)
            };
        }

        // Submit result
        await this.submitResult(task.id, result);
    }

    /**
     * Submit task result to server
     */
    private async submitResult(taskId: string, result: TaskResult) {
        try {
            const response = await fetch(`${this.apiBase}/tasks/${taskId}/result`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(result)
            });

            if (!response.ok) {
                throw new Error(`Failed to submit result: HTTP ${response.status}`);
            }

            console.log(`[HttpPoller] Result submitted for task ${taskId}`);

        } catch (error) {
            console.error(`[HttpPoller] Failed to submit result for ${taskId}:`, error);
        }
    }

    // ==================== Task Handlers ====================

    private async handlePing(task: Task): Promise<any> {
        return {
            message: 'pong',
            worker: this.workerId,
            timestamp: new Date().toISOString(),
            extension_version: '2.0.0'
        };
    }

    private async handleCalculation(data: any): Promise<any> {
        const { operation, numbers } = data;

        let result = 0;

        if (operation === 'add') {
            result = numbers.reduce((a: number, b: number) => a + b, 0);
        } else if (operation === 'multiply') {
            result = numbers.reduce((a: number, b: number) => a * b, 1);
        } else if (operation === 'divide' && numbers.length === 2) {
            result = numbers[0] / numbers[1];
        } else {
            throw new Error(`Unsupported operation: ${operation}`);
        }

        return { result };
    }

    private async handleDataTransform(data: any): Promise<any> {
        const { operation, text } = data;

        if (operation === 'uppercase') {
            return { result: text.toUpperCase() };
        } else if (operation === 'lowercase') {
            return { result: text.toLowerCase() };
        } else if (operation === 'reverse') {
            return { result: text.split('').reverse().join('') };
        }

        throw new Error(`Unknown operation: ${operation}`);
    }

    private async handleBatchCalculation(data: any): Promise<any> {
        const calculations = data.calculations || [];
        const results: any[] = [];

        for (const calc of calculations) {
            const { id, operation, numbers, multiply_by } = calc;
            let result = 0;

            if (operation === 'divide' && numbers.length === 2) {
                result = numbers[0] / numbers[1];
                if (multiply_by) {
                    result *= multiply_by;
                }
            } else if (operation === 'average') {
                result = numbers.reduce((a: number, b: number) => a + b, 0) / numbers.length;
            } else if (operation === 'multiply') {
                result = numbers.reduce((a: number, b: number) => a * b, 1);
            }

            results.push({ id, result });
        }

        return { calculations: results };
    }

    private async handleMonitoringReport(data: any): Promise<any> {
        // This would require file system access in the extension
        // For now, return a placeholder
        return {
            message: 'Monitoring report handler not yet implemented',
            requested_hours: data.hours,
            requested_metrics: data.metrics
        };
    }
}

/**
 * Example usage in Comet extension activation:
 * 
 * ```typescript
 * import { HttpTaskPoller } from './agent_tools/httpTaskPoller';
 * 
 * export function activate(context: vscode.ExtensionContext) {
 *   const poller = new HttpTaskPoller();
 *   poller.start();
 *   
 *   context.subscriptions.push({
 *     dispose: () => poller.stop()
 *   });
 * }
 * ```
 */
