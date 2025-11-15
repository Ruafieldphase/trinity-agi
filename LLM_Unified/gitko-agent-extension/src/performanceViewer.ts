/**
 * Performance Monitor Viewer
 * Real-time visualization of performance metrics
 */

import * as vscode from 'vscode';
import { PerformanceMonitor } from './performanceMonitor';
import type { OperationSummaryEntry } from './types';
import { createLogger } from './logger';
import { createNonce } from './webviewUtil';

const logger = createLogger('PerfViewer');

export class PerformanceViewer {
    public static currentPanel: PerformanceViewer | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _updateInterval: NodeJS.Timeout | undefined;
    private _monitor: PerformanceMonitor;

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.ViewColumn.Two;

        if (PerformanceViewer.currentPanel) {
            PerformanceViewer.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel('performanceViewer', '📊 Performance Monitor', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [extensionUri],
        });

        PerformanceViewer.currentPanel = new PerformanceViewer(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._monitor = PerformanceMonitor.getInstance();

        this._update();

        this._updateInterval = setInterval(() => {
            this._update();
        }, 2000);

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            (message) => {
                switch (message.command) {
                    case 'refresh':
                        this._update();
                        return;
                    case 'clear':
                        this._monitor.clearMetrics();
                        this._update();
                        vscode.window.showInformationMessage('✅ Performance metrics cleared');
                        return;
                    case 'export':
                        this._exportMetrics();
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    /**
     * HTML-escape helper to prevent XSS.
     */
    private _esc(value: unknown): string {
        const str = value == null ? '' : String(value);
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    private _update() {
        const summary = this._monitor.getSummary();
        const operations = this._monitor.getAllOperations();

        this._panel.webview.html = this._getHtmlContent(summary, operations);
    }

    private async _exportMetrics() {
        const json = this._monitor.exportMetrics();
        const timestamp = new Date().toISOString().replace(/:/g, '-');
        const defaultName = `gitko-performance-${timestamp}.json`;
        try {
            const target = await vscode.window.showSaveDialog({
                saveLabel: 'Save metrics as...',
                filters: { JSON: ['json'] },
                defaultUri: vscode.Uri.file(defaultName),
            });
            if (!target) {
                return; // user cancelled
            }
            await vscode.workspace.fs.writeFile(target, Buffer.from(json, 'utf-8'));
            vscode.window.showInformationMessage('✅ Metrics exported successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`❌ Export failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    private _getHtmlContent(summary: Record<string, OperationSummaryEntry>, operations: string[]): string {
        const operationRows = operations
            .map((op) => {
                const stats = this._monitor.getOperationStats(op);
                const summaryData = summary[op] || { count: 0, successRate: 0, avgDuration: 0 };

                return `
                <tr>
                    <td>${this._esc(op)}</td>
                    <td>${this._esc(stats.totalCount)}</td>
                    <td>${this._esc(summaryData.successRate.toFixed(1))}%</td>
                    <td>${this._esc(summaryData.avgDuration.toFixed(0))}ms</td>
                    <td>${this._esc(stats.minDuration.toFixed(0))}ms</td>
                    <td>${this._esc(stats.maxDuration.toFixed(0))}ms</td>
                </tr>
            `;
            })
            .join('');

        const nonce = createNonce();
        const cspSource = this._panel.webview.cspSource;
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${cspSource} https: data:; style-src 'unsafe-inline' ${cspSource}; font-src ${cspSource}; script-src 'nonce-${nonce}';">
    <title>Performance Monitor</title>
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
        h1 {
            margin: 0;
            font-size: 24px;
        }
        .buttons {
            display: flex;
            gap: 10px;
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
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--vscode-widget-border);
        }
        th {
            background: var(--vscode-editor-inactiveSelectionBackground);
            font-weight: bold;
        }
        tr:hover {
            background: var(--vscode-list-hoverBackground);
        }
        .empty-state {
            text-align: center;
            padding: 40px;
            opacity: 0.6;
        }
    </style>
</head>
<body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <div id="sr-status" aria-live="polite" class="sr-only"></div>

    <div class="header" role="banner">
        <h1>📊 Performance Monitor</h1>
        <div class="buttons" role="group" aria-label="Actions">
            <button class="button" onclick="refresh()" aria-label="Refresh metrics">🔄 Refresh</button>
            <button class="button" onclick="exportMetrics()" aria-label="Export metrics">💾 Export</button>
            <button class="button" onclick="clearMetrics()" aria-label="Clear metrics">🗑️ Clear</button>
        </div>
    </div>

    <main id="main" role="main" tabindex="-1">
    ${
        operations.length === 0
            ? `
        <div class="empty-state">
            <h2>No performance data yet</h2>
            <p>Performance metrics will appear here once operations are tracked.</p>
        </div>
    `
            : `
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Operations</div>
                <div class="stat-value">${operations.length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Executions</div>
                <div class="stat-value">${Object.values(summary).reduce((sum: number, s) => sum + s.count, 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Success Rate</div>
                <div class="stat-value">${
                    operations.length > 0
                                                ? (
                                                            Object.values(summary).reduce((sum: number, s) => sum + s.successRate, 0) /
                                                            operations.length
                                                    ).toFixed(1)
                        : 0
                }%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Duration</div>
                <div class="stat-value">${
                    operations.length > 0
                                                ? (
                                                            Object.values(summary).reduce((sum: number, s) => sum + s.avgDuration, 0) /
                                                            operations.length
                                                    ).toFixed(0)
                        : 0
                }ms</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Operation</th>
                    <th>Count</th>
                    <th>Success Rate</th>
                    <th>Avg Duration</th>
                    <th>Min Duration</th>
                    <th>Max Duration</th>
                </tr>
            </thead>
            <tbody>
                ${operationRows}
            </tbody>
        </table>
    `
    }
    </main>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        function refresh() {
            vscode.postMessage({ command: 'refresh' });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = 'Refreshed metrics';
        }

        function exportMetrics() {
            vscode.postMessage({ command: 'export' });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = 'Exported metrics';
        }

        function clearMetrics() {
            if (confirm('Are you sure you want to clear all metrics?')) {
                vscode.postMessage({ command: 'clear' });
                const sr = document.getElementById('sr-status');
                if (sr) sr.textContent = 'Cleared metrics';
            }
        }
    </script>
</body>
</html>`;
    }

    public dispose() {
        PerformanceViewer.currentPanel = undefined;

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

        logger.debug('PerformanceViewer disposed');
    }
}
