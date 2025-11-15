import * as vscode from 'vscode';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { createNonce } from './webviewUtil';
import { createLogger } from './logger';

const logger = createLogger('TaskQueueMonitor');

// Axios retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Data shapes from API
interface TaskQueueHealth {
    status: string;
    queue_size: number;
    success_rate: number;
    avg_duration_ms: number;
}

interface PendingTask {
    task_id: string;
    task_type?: string;
    priority?: string;
    created_at: string | number | Date;
}

interface InflightTask {
    task_id: string;
    task_type?: string;
    leased_at: string | number | Date;
}

interface InflightData {
    count: number;
    tasks: InflightTask[];
}

interface ResultItem {
    task_id: string;
    task_type?: string;
    status: 'completed' | 'failed' | string;
    created_at: string | number | Date;
    completed_at?: string | number | Date;
    error?: string;
}

async function axiosWithRetry<T>(config: AxiosRequestConfig, retries = MAX_RETRIES): Promise<T> {
    try {
        const response = await axios(config);
        return response.data as T;
    } catch (error) {
        const axiosError = error as AxiosError;
        if (retries > 0 && shouldRetry(axiosError)) {
            logger.warn(`Request failed, retrying... (${MAX_RETRIES - retries + 1}/${MAX_RETRIES})`);
            await delay(RETRY_DELAY);
            return axiosWithRetry<T>(config, retries - 1);
        }
        logger.error('Request failed after all retries', axiosError);
        throw error;
    }
}

function shouldRetry(error: AxiosError): boolean {
    return (
        !error.response ||
        (error.response.status >= 500 && error.response.status < 600) ||
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT'
    );
}

function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

export class TaskQueueMonitor {
    public static currentPanel: TaskQueueMonitor | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _updateInterval: NodeJS.Timeout | undefined;
    private _serverUrl: string;

    // Basic HTML escaping to prevent markup injection in WebView
    private _esc(value: unknown): string {
        const str = String(value ?? '');
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    public static createOrShow(extensionUri: vscode.Uri, serverUrl: string = 'http://127.0.0.1:8091') {
        const column = vscode.ViewColumn.Two;
        if (TaskQueueMonitor.currentPanel) {
            TaskQueueMonitor.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('taskQueueMonitor', '🎯 Task Queue Monitor', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [extensionUri],
        });
        TaskQueueMonitor.currentPanel = new TaskQueueMonitor(panel, extensionUri, serverUrl);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, serverUrl: string) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._serverUrl = serverUrl;

        this._update();
        this._updateInterval = setInterval(() => this._update(), 2000);

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(
            (message) => {
                switch (message.command) {
                    case 'refresh':
                        this._update();
                        return;
                    case 'clearCompleted':
                        this._clearCompleted();
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    private async _update() {
        try {
            const [health, tasks, inflight, results] = await Promise.all([
                this._fetchHealth(),
                this._fetchTasks(),
                this._fetchInflight(),
                this._fetchResults(),
            ]);
            this._panel.webview.html = this._getHtmlContent(health, tasks, inflight, results);
        } catch (error) {
            this._panel.webview.html = this._getErrorHtml(error);
        }
    }

    private async _fetchHealth(): Promise<TaskQueueHealth> {
        return axiosWithRetry<TaskQueueHealth>({ method: 'GET', url: `${this._serverUrl}/api/health` });
    }
    private async _fetchTasks(): Promise<PendingTask[]> {
        return axiosWithRetry<PendingTask[]>({ method: 'GET', url: `${this._serverUrl}/api/tasks` });
    }
    private async _fetchInflight(): Promise<InflightData> {
        return axiosWithRetry<InflightData>({ method: 'GET', url: `${this._serverUrl}/api/inflight` });
    }
    private async _fetchResults(): Promise<ResultItem[]> {
        return axiosWithRetry<ResultItem[]>({ method: 'GET', url: `${this._serverUrl}/api/results` });
    }

    private async _clearCompleted(): Promise<void> {
        try {
            await axiosWithRetry<void>({ method: 'POST', url: `${this._serverUrl}/api/clear-completed` });
            vscode.window.showInformationMessage('✅ Completed tasks cleared');
            this._update();
        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`❌ Failed to clear tasks: ${errorMsg}`);
        }
    }

    private _getHtmlContent(
        health: TaskQueueHealth,
        tasks: PendingTask[],
        inflight: InflightData,
        results: ResultItem[]
    ): string {
        const pendingCount = tasks.length;
        const inflightCount = inflight?.count || 0;
        const completedCount = results.filter((r) => r.status === 'completed').length;
        const failedCount = results.filter((r) => r.status === 'failed').length;

        const healthColor = health.status === 'healthy' ? '#4CAF50' : '#FF5722';
        const successRate = (health.success_rate * 100).toFixed(1);

        const nonce = createNonce();
        const cspSource = this._panel.webview.cspSource;
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} https: data:; style-src 'unsafe-inline' ${cspSource}; font-src ${cspSource}; script-src 'nonce-${nonce}';">
    <title>Task Queue Monitor</title>
    <style>
        .skip-link { position: absolute; left: -9999px; top: auto; width: 1px; height: 1px; overflow: hidden; }
        .skip-link:focus { position: static; width: auto; height: auto; padding: 8px 12px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border-radius: 4px; }
        .sr-only { position: absolute !important; width: 1px !important; height: 1px !important; padding: 0 !important; margin: -1px !important; overflow: hidden !important; clip: rect(0,0,0,0) !important; white-space: nowrap !important; border: 0 !important; }
        body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background-color: var(--vscode-editor-background); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { margin: 0; font-size: 24px; }
        .buttons { display: flex; gap: 10px; align-items: center; }
        .button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; font-size: 14px; }
        .button:hover { background: var(--vscode-button-hoverBackground); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 30px; }
        .stat-card { background: var(--vscode-editor-inactiveSelectionBackground); padding: 16px; border-radius: 8px; border-left: 4px solid var(--vscode-button-background); }
        .stat-value { font-size: 32px; font-weight: bold; margin: 8px 0; }
        .stat-label { font-size: 14px; opacity: 0.8; }
        .health-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: ${healthColor}; margin-right: 8px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.5;} }
        .section { margin-bottom: 30px; }
        .section h2 { font-size: 18px; margin-bottom: 12px; border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 8px; }
        .task-list { max-height: 300px; overflow-y: auto; }
        .task-item { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--vscode-widget-border); }
        .task-type { background: var(--vscode-editor-inactiveSelectionBackground); color: var(--vscode-foreground); padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px; }
        .status-completed { background: #2e7d32; color: #fff; }
        .status-failed { background: #c62828; color: #fff; }
        .status-inflight { background: #0277bd; color: #fff; }
    </style>
</head>
<body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <div id="sr-status" aria-live="polite" class="sr-only"></div>

    <div class="header" role="banner">
        <h1>🎯 Task Queue Monitor</h1>
        <div class="buttons" role="group" aria-label="Actions">
            <span class="health-indicator" title="${this._esc(health.status)}"></span>
            <span>${this._esc(successRate)}% success</span>
            <button class="button" onclick="refresh()" aria-label="Refresh data">🔄 Refresh</button>
            <button class="button" onclick="clearCompleted()" aria-label="Clear completed tasks">🧹 Clear Completed</button>
        </div>
    </div>

    <main id="main" role="main" tabindex="-1">
      <section class="stats" aria-label="Queue statistics">
        <div class="stat-card" role="group" aria-label="Pending tasks ${this._esc(pendingCount)}">
            <div class="stat-label"><span aria-hidden="true">📋</span> Pending</div>
            <div class="stat-value">${pendingCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="In flight tasks ${this._esc(inflightCount)}">
            <div class="stat-label"><span aria-hidden="true">🔄</span> In Flight</div>
            <div class="stat-value status-inflight">${inflightCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Completed tasks ${this._esc(completedCount)}">
            <div class="stat-label"><span aria-hidden="true">✅</span> Completed</div>
            <div class="stat-value status-completed">${completedCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Failed tasks ${this._esc(failedCount)}">
            <div class="stat-label"><span aria-hidden="true">❌</span> Failed</div>
            <div class="stat-value status-failed">${failedCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Average duration ${health.avg_duration_ms.toFixed(0)} milliseconds">
            <div class="stat-label"><span aria-hidden="true">⏱️</span> Avg Duration</div>
            <div class="stat-value">${health.avg_duration_ms.toFixed(0)}ms</div>
        </div>
      </section>

    <section class="section" role="region" aria-label="Pending tasks list with ${this._esc(pendingCount)} items">
        <h2><span aria-hidden="true">📋</span> Pending Tasks (${pendingCount})</h2>
        <ul class="task-list" role="list">
            ${
                tasks
                    .slice(0, 10)
                    .map(
                        (task: PendingTask) => `
                <li class="task-item" role="listitem" aria-label="${this._esc(task.task_type || 'unknown')} priority ${this._esc(task.priority || 'normal')} id ${this._esc(task.task_id)} created ${this._esc(new Date(task.created_at).toLocaleString())}">
                    <div>
                        <strong>${this._esc(task.task_type || 'unknown')}</strong>
                        <span class="task-type">${this._esc(task.priority || 'normal')}</span>
                    </div>
                    <div class="task-id">ID: ${this._esc(task.task_id)}</div>
                    <div class="timestamp">Created: ${this._esc(new Date(task.created_at).toLocaleString())}</div>
                </li>
            `
                    )
                    .join('') || '<li class="task-item" role="listitem">No pending tasks</li>'
            }
        </ul>
    </section>

    <section class="section" role="region" aria-label="In flight tasks list with ${this._esc(inflightCount)} items">
        <h2><span aria-hidden="true">🔄</span> In Flight Tasks (${inflightCount})</h2>
        <ul class="task-list" role="list">
            ${
                inflight?.tasks
                    ?.slice(0, 5)
                    .map(
                        (task: InflightTask) => `
                <li class="task-item" role="listitem" aria-label="${this._esc(task.task_type || 'unknown')} running id ${this._esc(task.task_id)} started ${this._esc(new Date(task.leased_at).toLocaleString())}">
                    <div>
                        <strong>${this._esc(task.task_type || 'unknown')}</strong>
                        <span class="task-type status-inflight">RUNNING</span>
                    </div>
                    <div class="task-id">ID: ${this._esc(task.task_id)}</div>
                    <div class="timestamp">Started: ${this._esc(new Date(task.leased_at).toLocaleString())}</div>
                </li>
            `
                    )
                    .join('') || '<li class="task-item" role="listitem">No tasks in flight</li>'
            }
        </ul>
    </section>

    <section class="section" role="region" aria-label="Recent results list">
        <h2><span aria-hidden="true">📊</span> Recent Results</h2>
        <ul class="task-list" role="list">
            ${
                results
                    .slice(0, 10)
                    .map(
                        (result: ResultItem) => `
                <li class="task-item" role="listitem" aria-label="${this._esc(result.task_type || 'unknown')} ${this._esc(result.status)} id ${this._esc(result.task_id)} ${result.completed_at ? 'completed' : 'created'} ${this._esc(new Date(result.completed_at || result.created_at).toLocaleString())} ${result.error ? 'error ' + this._esc(result.error) : ''}">
                    <div>
                        <strong>${this._esc(result.task_type || 'unknown')}</strong>
                        <span class="task-type status-${this._esc(result.status)}">${this._esc(result.status?.toUpperCase())}</span>
                    </div>
                    <div class="task-id">ID: ${this._esc(result.task_id)}</div>
                    ${result.error ? `<div style="color: #FF5722; margin-top: 4px;">Error: ${this._esc(result.error)}</div>` : ''}
                    <div class="timestamp">Completed: ${this._esc(new Date(result.completed_at || result.created_at).toLocaleString())}</div>
                </li>
            `
                    )
                    .join('') || '<li class="task-item" role="listitem">No results yet</li>'
            }
        </ul>
    </section>
    </main>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        function refresh() { vscode.postMessage({ command: 'refresh' }); const sr = document.getElementById('sr-status'); if (sr) sr.textContent = 'Refreshed task data'; }
        function clearCompleted() { vscode.postMessage({ command: 'clearCompleted' }); const sr = document.getElementById('sr-status'); if (sr) sr.textContent = 'Cleared completed tasks'; }
    </script>
</body>
</html>`;
    }

    private _getErrorHtml(error: unknown): string {
        const cspSource = this._panel.webview.cspSource;
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} https: data:; style-src 'unsafe-inline' ${cspSource}; font-src ${cspSource}; script-src 'none';">
    <style>
        body { font-family: var(--vscode-font-family); padding: 20px; color: var(--vscode-foreground); background-color: var(--vscode-editor-background); }
        .error { background: var(--vscode-inputValidation-errorBackground); border: 1px solid var(--vscode-inputValidation-errorBorder); padding: 20px; border-radius: 8px; }
        h1 { margin-top: 0; }
        pre { background: var(--vscode-editor-background); padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="error">
        <h1>❌ Connection Error</h1>
        <p>Failed to connect to Task Queue Server at <code>${this._serverUrl}</code></p>
        <p>Please ensure:</p>
        <ul>
            <li>Task Queue Server is running on port 8091</li>
            <li>Run: <code>cd LLM_Unified\\ion-mentoring && .venv\\Scripts\\python.exe task_queue_server.py</code></li>
        </ul>
        <details>
            <summary>Error Details</summary>
            <pre>${error instanceof Error ? error.message : String(error)}</pre>
        </details>
    </div>
</body>
</html>`;
    }

    public dispose() {
        TaskQueueMonitor.currentPanel = undefined;
        if (this._updateInterval) clearInterval(this._updateInterval);
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) disposable.dispose();
        }
    }
}
