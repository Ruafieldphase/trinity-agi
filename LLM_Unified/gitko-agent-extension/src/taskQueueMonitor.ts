import * as vscode from 'vscode';
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { createLogger } from './logger';

const logger = createLogger('TaskQueueMonitor');

// Axios retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

interface TaskQueueStatus {
    pending: number;
    inflight: number;
    completed: number;
    failed: number;
}

interface TaskQueueHealth {
    status: string;
    queue_size: number;
    success_rate: number;
    avg_duration_ms: number;
}

/**
 * Axios request with retry logic
 */
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
    // Retry on network errors or 5xx server errors
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

/**
 * Task Queue Monitor Panel
 * Port 8091의 Task Queue Server를 실시간 모니터링
 */
export class TaskQueueMonitor {
    public static currentPanel: TaskQueueMonitor | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _updateInterval: NodeJS.Timeout | undefined;
    private _serverUrl: string;

    public static createOrShow(extensionUri: vscode.Uri, serverUrl: string = 'http://127.0.0.1:8091') {
        const column = vscode.ViewColumn.Two;

        // 이미 패널이 있으면 표시
        if (TaskQueueMonitor.currentPanel) {
            TaskQueueMonitor.currentPanel._panel.reveal(column);
            return;
        }

        // 새 패널 생성
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

        // 초기 컨텐츠 설정
        this._update();

        // 2초마다 업데이트
        this._updateInterval = setInterval(() => {
            this._update();
        }, 2000);

        // 패널이 닫힐 때 정리
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // 웹뷰 메시지 처리
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
        logger.debug('Fetching health status');
        return axiosWithRetry<TaskQueueHealth>({
            method: 'GET',
            url: `${this._serverUrl}/api/health`,
        });
    }

    private async _fetchTasks(): Promise<any[]> {
        logger.debug('Fetching tasks');
        return axiosWithRetry<any[]>({
            method: 'GET',
            url: `${this._serverUrl}/api/tasks`,
        });
    }

    private async _fetchInflight(): Promise<any> {
        logger.debug('Fetching inflight tasks');
        return axiosWithRetry<any>({
            method: 'GET',
            url: `${this._serverUrl}/api/inflight`,
        });
    }

    private async _fetchResults(): Promise<any[]> {
        logger.debug('Fetching results');
        return axiosWithRetry<any[]>({
            method: 'GET',
            url: `${this._serverUrl}/api/results`,
        });
    }

    private async _clearCompleted(): Promise<void> {
        try {
            logger.info('Clearing completed tasks');
            await axiosWithRetry<void>({
                method: 'POST',
                url: `${this._serverUrl}/api/clear-completed`,
            });
            vscode.window.showInformationMessage('✅ Completed tasks cleared');
            logger.info('Completed tasks cleared successfully');
            this._update();
        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : String(error);
            logger.error('Failed to clear completed tasks', error as Error);
            vscode.window.showErrorMessage(`❌ Failed to clear tasks: ${errorMsg}`);
        }
    }

    private _getHtmlContent(health: TaskQueueHealth, tasks: any[], inflight: any, results: any[]): string {
        const pendingCount = tasks.length;
        const inflightCount = inflight?.count || 0;
        const completedCount = results.filter((r: any) => r.status === 'completed').length;
        const failedCount = results.filter((r: any) => r.status === 'failed').length;

        const healthColor = health.status === 'healthy' ? '#4CAF50' : '#FF5722';
        const successRate = (health.success_rate * 100).toFixed(1);

        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Queue Monitor</title>
    <style>
        .skip-link {
            position: absolute;
            left: -9999px;
            top: auto;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }
        .skip-link:focus {
            position: static;
            width: auto;
            height: auto;
            padding: 8px 12px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
        }
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 14px;
        }
        .button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid var(--vscode-button-background);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin: 8px 0;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.8;
        }
        .health-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: ${healthColor};
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            font-size: 18px;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 8px;
        }
        .task-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .task-item {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 13px;
        }
        .task-id {
            font-family: monospace;
            opacity: 0.7;
            font-size: 11px;
        }
        .task-type {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 8px;
            background: var(--vscode-button-secondaryBackground);
        }
        .status-pending { color: #FFC107; }
        .status-inflight { color: #2196F3; }
        .status-completed { color: #4CAF50; }
        .status-failed { color: #FF5722; }
        .timestamp {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <div id="sr-status" aria-live="polite" class="sr-only"></div>
    <header class="header" role="banner">
        <h1 aria-label="Task Queue Monitor"><span aria-hidden="true">🎯</span> Task Queue Monitor</h1>
        <div role="group" aria-label="Actions">
            <button class="button" onclick="refresh()" aria-label="Refresh task data"><span aria-hidden="true">🔄</span> Refresh</button>
            <button class="button" onclick="clearCompleted()" aria-label="Clear completed tasks"><span aria-hidden="true">🗑️</span> Clear Completed</button>
        </div>
    </header>

    <main id="main" role="main" tabindex="-1">
      <section class="stats" role="region" aria-label="Queue statistics">
        <div class="stat-card" role="group" aria-label="Health status ${health.status} with success rate ${successRate} percent">
            <div class="stat-label">
                <span class="health-indicator" aria-hidden="true"></span>
                <span>Health Status</span>
            </div>
            <div class="stat-value" aria-label="${health.status.toUpperCase()}">${health.status.toUpperCase()}</div>
            <div class="stat-label" aria-label="Success rate ${successRate} percent">Success Rate: ${successRate}%</div>
        </div>
        <div class="stat-card" role="group" aria-label="Pending tasks ${pendingCount}">
            <div class="stat-label"><span aria-hidden="true">⏳</span> Pending</div>
            <div class="stat-value status-pending">${pendingCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="In flight tasks ${inflightCount}">
            <div class="stat-label"><span aria-hidden="true">🔄</span> In Flight</div>
            <div class="stat-value status-inflight">${inflightCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Completed tasks ${completedCount}">
            <div class="stat-label"><span aria-hidden="true">✅</span> Completed</div>
            <div class="stat-value status-completed">${completedCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Failed tasks ${failedCount}">
            <div class="stat-label"><span aria-hidden="true">❌</span> Failed</div>
            <div class="stat-value status-failed">${failedCount}</div>
        </div>
        <div class="stat-card" role="group" aria-label="Average duration ${health.avg_duration_ms.toFixed(0)} milliseconds">
            <div class="stat-label"><span aria-hidden="true">⏱️</span> Avg Duration</div>
            <div class="stat-value">${health.avg_duration_ms.toFixed(0)}ms</div>
        </div>
      </section>

    <section class="section" role="region" aria-label="Pending tasks list with ${pendingCount} items">
        <h2><span aria-hidden="true">📋</span> Pending Tasks (${pendingCount})</h2>
        <ul class="task-list" role="list">
            ${
                tasks
                    .slice(0, 10)
                    .map(
                        (task: any) => `
                <li class="task-item" role="listitem" aria-label="${task.task_type || 'unknown'} priority ${task.priority || 'normal'} id ${task.task_id} created ${new Date(task.created_at).toLocaleString()}">
                    <div>
                        <strong>${task.task_type || 'unknown'}</strong>
                        <span class="task-type">${task.priority || 'normal'}</span>
                    </div>
                    <div class="task-id">ID: ${task.task_id}</div>
                    <div class="timestamp">Created: ${new Date(task.created_at).toLocaleString()}</div>
                </li>
            `
                    )
                    .join('') || '<li class="task-item" role="listitem">No pending tasks</li>'
            }
        </ul>
    </section>

    <section class="section" role="region" aria-label="In flight tasks list with ${inflightCount} items">
        <h2><span aria-hidden="true">🔄</span> In Flight Tasks (${inflightCount})</h2>
        <ul class="task-list" role="list">
            ${
                inflight?.tasks
                    ?.slice(0, 5)
                    .map(
                        (task: any) => `
                <li class="task-item" role="listitem" aria-label="${task.task_type || 'unknown'} running id ${task.task_id} started ${new Date(task.leased_at).toLocaleString()}">
                    <div>
                        <strong>${task.task_type || 'unknown'}</strong>
                        <span class="task-type status-inflight">RUNNING</span>
                    </div>
                    <div class="task-id">ID: ${task.task_id}</div>
                    <div class="timestamp">Started: ${new Date(task.leased_at).toLocaleString()}</div>
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
                        (result: any) => `
                <li class="task-item" role="listitem" aria-label="${result.task_type || 'unknown'} ${result.status} id ${result.task_id} ${result.completed_at ? 'completed' : 'created'} ${new Date(result.completed_at || result.created_at).toLocaleString()} ${result.error ? 'error ' + result.error : ''}">
                    <div>
                        <strong>${result.task_type || 'unknown'}</strong>
                        <span class="task-type status-${result.status}">${result.status?.toUpperCase()}</span>
                    </div>
                    <div class="task-id">ID: ${result.task_id}</div>
                    ${result.error ? `<div style="color: #FF5722; margin-top: 4px;">Error: ${result.error}</div>` : ''}
                    <div class="timestamp">Completed: ${new Date(result.completed_at || result.created_at).toLocaleString()}</div>
                </li>
            `
                    )
                    .join('') || '<li class="task-item" role="listitem">No results yet</li>'
            }
        </ul>
    </section>
    </main>

    <script>
        const vscode = acquireVsCodeApi();
        
        function refresh() {
            vscode.postMessage({ command: 'refresh' });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = 'Refreshed task data';
        }
        
        function clearCompleted() {
            vscode.postMessage({ command: 'clearCompleted' });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = 'Cleared completed tasks';
        }
    </script>
</body>
</html>`;
    }

    private _getErrorHtml(error: any): string {
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .error {
            background: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            padding: 20px;
            border-radius: 8px;
        }
        h1 { margin-top: 0; }
        pre {
            background: var(--vscode-editor-background);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
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

        if (this._updateInterval) {
            clearInterval(this._updateInterval);
        }

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
