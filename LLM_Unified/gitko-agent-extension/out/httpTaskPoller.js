"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.HttpTaskPoller = void 0;
const vscode = __importStar(require("vscode"));
const logger_1 = require("./logger");
const performanceMonitor_1 = require("./performanceMonitor");
const schemas_1 = require("./schemas");
const logger = (0, logger_1.createLogger)('HttpTaskPoller');
const perf = performanceMonitor_1.PerformanceMonitor.getInstance();
/**
 * HTTP-based Task Poller for Gitko Extension
 *
 * Polls the Task Queue HTTP API for new tasks and processes them.
 * Replaces the Python http_task_poller.py with native TypeScript implementation.
 *
 * @author Phase 8a Integration
 * @date 2025-10-29
 */
class HttpTaskPoller {
    constructor(apiBase = 'http://localhost:8091/api', workerId = 'gitko-extension', pollingInterval = 2000) {
        this.isPolling = false;
        this.lastUiActionAt = 0;
        this.minUiActionIntervalMs = 150;
        // Backoff and circuit breaker
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = 5;
        this.baseBackoffMs = 1000;
        this.maxBackoffMs = 30000;
        this.currentBackoffMs = 0;
        this.isCircuitOpen = false;
        this.apiBase = apiBase;
        this.workerId = workerId;
        this.pollingInterval = pollingInterval;
    }
    /**
     * Set callback for logging output
     */
    setOutputCallback(callback) {
        this.outputCallback = callback;
    }
    log(message) {
        if (this.outputCallback) {
            this.outputCallback(message);
        }
        else {
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
        this.log(`[HttpPoller] Starting (API: ${this.apiBase}, Worker: ${this.workerId}, Interval: ${this.pollingInterval}ms)`);
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
    isActive() {
        return this.isPolling;
    }
    /**
     * Poll for next task
     */
    async poll() {
        if (!this.isPolling) {
            return;
        }
        // Check circuit breaker
        if (this.isCircuitOpen) {
            if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                this.log(`[HttpPoller] ⚠️ Circuit breaker OPEN (${this.consecutiveErrors} errors). Backing off ${this.currentBackoffMs}ms`);
            }
        }
        const opId = perf.startOperation('http.poll');
        try {
            const task = await this.getNextTask();
            if (task) {
                this.log(`[HttpPoller] 📥 Task received: ${task.task_id} (${task.type})`);
                await this.handleTask(task);
            }
            // Success: reset backoff
            this.onSuccess();
            perf.endOperation(opId, true);
        }
        catch (error) {
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
     * Handle successful operation - reset backoff
     */
    onSuccess() {
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
    onError(error) {
        // Suppress common connection/API errors to reduce noise
        const errorMsg = error instanceof Error ? error.message : String(error);
        const shouldSuppress = errorMsg.includes('ECONNREFUSED') ||
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
            this.log(`[HttpPoller] ⚠️ Error #${this.consecutiveErrors}: ${errorMsg} (backoff: ${this.currentBackoffMs}ms)`);
        }
    }
    /**
     * Get next task from server
     */
    async getNextTask() {
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
            const data = (await response.json());
            // Handle empty queue response: {task: null}
            if (data && data.task === null) {
                return null;
            }
            // Validate task schema
            if (data) {
                const validation = (0, schemas_1.validateTaskSafe)(data);
                if (!validation.success) {
                    this.log(`[HttpPoller] ⚠️ Invalid task schema: ${validation.error}`);
                    return null;
                }
                return validation.data;
            }
            return null;
        }
        catch (error) {
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
    async handleTask(task) {
        let result;
        // Queue latency if provided
        let queueLatencyMs;
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
            let resultData;
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
        }
        catch (error) {
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
    async submitResult(taskId, result) {
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
        }
        catch (error) {
            this.log(`[HttpPoller] ❌ Failed to submit result for ${taskId}: ${error instanceof Error ? error.message : String(error)}`);
            perf.endOperation(opId, false, { task_id: taskId, error: error instanceof Error ? error.message : String(error) });
        }
    }
    // ==================== Task Handlers ====================
    async handlePing(task) {
        return {
            message: 'pong',
            worker: this.workerId,
            timestamp: new Date().toISOString(),
            extension: 'gitko-agent-extension',
            version: '2.0.0',
        };
    }
    async handleCalculation(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }
        const { operation, numbers } = data;
        if (!operation || typeof operation !== 'string') {
            throw new Error('Invalid data: operation string required');
        }
        if (!numbers || !Array.isArray(numbers)) {
            throw new Error('Invalid data: numbers array required');
        }
        const numArray = numbers;
        let result = 0;
        if (operation === 'add') {
            result = numArray.reduce((a, b) => a + b, 0);
        }
        else if (operation === 'multiply') {
            result = numArray.reduce((a, b) => a * b, 1);
        }
        else if (operation === 'divide' && numArray.length === 2) {
            if (numArray[1] === 0) {
                throw new Error('Division by zero');
            }
            result = numArray[0] / numArray[1];
        }
        else if (operation === 'average') {
            result = numArray.reduce((a, b) => a + b, 0) / numArray.length;
        }
        else {
            throw new Error(`Unsupported operation: ${operation}`);
        }
        return {
            result,
            operation,
            input: numArray,
        };
    }
    async handleDataTransform(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }
        const { operation, text } = data;
        if (!text || typeof text !== 'string') {
            throw new Error('Invalid data: text field required');
        }
        if (!operation || typeof operation !== 'string') {
            throw new Error('Invalid data: operation field required');
        }
        if (operation === 'uppercase') {
            return { result: text.toUpperCase() };
        }
        else if (operation === 'lowercase') {
            return { result: text.toLowerCase() };
        }
        else if (operation === 'reverse') {
            return { result: text.split('').reverse().join('') };
        }
        else if (operation === 'length') {
            return { result: text.length };
        }
        throw new Error(`Unknown operation: ${operation}`);
    }
    async handleBatchCalculation(data) {
        const calculations = data.calculations || [];
        const results = [];
        for (const calc of calculations) {
            const { id, operation, numbers, multiply_by } = calc;
            try {
                let result = 0;
                if (operation === 'divide' && numbers.length === 2) {
                    if (numbers[1] === 0) {
                        throw new Error('Division by zero');
                    }
                    result = numbers[0] / numbers[1];
                    if (multiply_by) {
                        result *= multiply_by;
                    }
                }
                else if (operation === 'average') {
                    result = numbers.reduce((a, b) => a + b, 0) / numbers.length;
                }
                else if (operation === 'multiply') {
                    result = numbers.reduce((a, b) => a * b, 1);
                }
                else if (operation === 'add') {
                    result = numbers.reduce((a, b) => a + b, 0);
                }
                results.push({ id, result, status: 'success' });
            }
            catch (error) {
                results.push({
                    id,
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
    async handleMonitoringReport(data) {
        // Placeholder for monitoring report generation
        // This could be extended to call Gitko agents or generate reports
        return {
            message: 'Monitoring report generation not yet implemented in extension',
            requested_hours: data.hours,
            requested_metrics: data.metrics || [],
            suggestion: 'Use Python scripts for full monitoring reports',
        };
    }
    // ==================== Computer Use handlers ====================
    async handleCuScan() {
        this.ensureCuEnabled();
        const { ComputerUseAgent } = await Promise.resolve().then(() => __importStar(require('./computerUse')));
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const elements = await agent.scanScreen();
        logger.info(`Scanned screen: ${elements.length} elements found`);
        return { elements };
    }
    async handleCuFind(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }
        const { text } = data;
        if (typeof text !== 'string' || !text.trim()) {
            throw new Error('Invalid data: { text: string } required');
        }
        this.ensureCuEnabled();
        const { ComputerUseAgent } = await Promise.resolve().then(() => __importStar(require('./computerUse')));
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const element = await agent.findElementByText(text);
        logger.info(`Found element: ${text}`);
        return { element };
    }
    async handleCuClick(data) {
        this.ensureCuEnabled();
        const { ComputerUseAgent } = await Promise.resolve().then(() => __importStar(require('./computerUse')));
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        let ok = false;
        if (data && typeof data === 'object') {
            const clickData = data;
            if (typeof clickData.x === 'number' && typeof clickData.y === 'number') {
                ok = await agent.clickAt(clickData.x, clickData.y);
                logger.info(`Clicked at (${clickData.x}, ${clickData.y})`);
            }
            else if (typeof clickData.text === 'string' && clickData.text.trim()) {
                ok = await agent.clickElementByText(clickData.text);
                logger.info(`Clicked element: ${clickData.text}`);
            }
            else {
                throw new Error('Invalid data: provide either { x:number, y:number } or { text:string }');
            }
        }
        else {
            throw new Error('Invalid data: object required');
        }
        return { success: ok };
    }
    async handleCuType(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data: object required');
        }
        const { text } = data;
        if (typeof text !== 'string') {
            throw new Error('Invalid data: { text: string } required');
        }
        this.ensureCuEnabled();
        const { ComputerUseAgent } = await Promise.resolve().then(() => __importStar(require('./computerUse')));
        const agent = new ComputerUseAgent();
        await this.enforceUiCooldown();
        const ok = await agent.type(text);
        logger.info(`Typed text: ${text.substring(0, 20)}...`);
        return { success: ok };
    }
    async enforceUiCooldown() {
        const cfg = vscode.workspace.getConfiguration('gitko');
        const interval = cfg.get('minUiActionIntervalMs', 150);
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
    ensureCuEnabled() {
        const cfg = vscode.workspace.getConfiguration('gitko');
        const enabled = cfg.get('enableComputerUseOverHttp', true);
        if (!enabled) {
            throw new Error('Computer Use over HTTP is disabled by settings (gitko.enableComputerUseOverHttp=false)');
        }
    }
}
exports.HttpTaskPoller = HttpTaskPoller;
//# sourceMappingURL=httpTaskPoller.js.map