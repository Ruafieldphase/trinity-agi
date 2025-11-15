"use strict";
/**
 * Performance Monitor Viewer
 * Real-time visualization of performance metrics
 */
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
exports.PerformanceViewer = void 0;
const vscode = __importStar(require("vscode"));
const performanceMonitor_1 = require("./performanceMonitor");
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('PerfViewer');
class PerformanceViewer {
    static createOrShow(extensionUri) {
        const column = vscode.ViewColumn.Two;
        if (PerformanceViewer.currentPanel) {
            PerformanceViewer.currentPanel._panel.reveal(column);
            return;
        }
        const panel = vscode.window.createWebviewPanel('performanceViewer', '📊 Performance Monitor', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [extensionUri]
        });
        PerformanceViewer.currentPanel = new PerformanceViewer(panel, extensionUri);
    }
    constructor(panel, extensionUri) {
        this._disposables = [];
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._monitor = performanceMonitor_1.PerformanceMonitor.getInstance();
        this._update();
        this._updateInterval = setInterval(() => {
            this._update();
        }, 2000);
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(message => {
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
        }, null, this._disposables);
    }
    _update() {
        const summary = this._monitor.getSummary();
        const operations = this._monitor.getAllOperations();
        this._panel.webview.html = this._getHtmlContent(summary, operations);
    }
    _exportMetrics() {
        const json = this._monitor.exportMetrics();
        const timestamp = new Date().toISOString().replace(/:/g, '-');
        vscode.workspace.fs.writeFile(vscode.Uri.file(`gitko-performance-${timestamp}.json`), Buffer.from(json, 'utf-8')).then(() => {
            vscode.window.showInformationMessage('✅ Metrics exported successfully');
        }, (error) => {
            vscode.window.showErrorMessage(`❌ Export failed: ${error}`);
        });
    }
    _getHtmlContent(summary, operations) {
        const operationRows = operations.map(op => {
            const stats = this._monitor.getOperationStats(op);
            const summaryData = summary[op] || { count: 0, successRate: 0, avgDuration: 0 };
            return `
                <tr>
                    <td>${op}</td>
                    <td>${stats.totalCount}</td>
                    <td>${summaryData.successRate.toFixed(1)}%</td>
                    <td>${summaryData.avgDuration.toFixed(0)}ms</td>
                    <td>${stats.minDuration.toFixed(0)}ms</td>
                    <td>${stats.maxDuration.toFixed(0)}ms</td>
                </tr>
            `;
        }).join('');
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Monitor</title>
    <style>
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
    <div class="header">
        <h1>📊 Performance Monitor</h1>
        <div class="buttons">
            <button class="button" onclick="refresh()">🔄 Refresh</button>
            <button class="button" onclick="exportMetrics()">💾 Export</button>
            <button class="button" onclick="clearMetrics()">🗑️ Clear</button>
        </div>
    </div>

    ${operations.length === 0 ? `
        <div class="empty-state">
            <h2>No performance data yet</h2>
            <p>Performance metrics will appear here once operations are tracked.</p>
        </div>
    ` : `
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Operations</div>
                <div class="stat-value">${operations.length}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Executions</div>
                <div class="stat-value">${Object.values(summary).reduce((sum, s) => sum + s.count, 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Success Rate</div>
                <div class="stat-value">${operations.length > 0
            ? (Object.values(summary).reduce((sum, s) => sum + s.successRate, 0) / operations.length).toFixed(1)
            : 0}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Duration</div>
                <div class="stat-value">${operations.length > 0
            ? (Object.values(summary).reduce((sum, s) => sum + s.avgDuration, 0) / operations.length).toFixed(0)
            : 0}ms</div>
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
    `}

    <script>
        const vscode = acquireVsCodeApi();

        function refresh() {
            vscode.postMessage({ command: 'refresh' });
        }

        function exportMetrics() {
            vscode.postMessage({ command: 'export' });
        }

        function clearMetrics() {
            if (confirm('Are you sure you want to clear all metrics?')) {
                vscode.postMessage({ command: 'clear' });
            }
        }
    </script>
</body>
</html>`;
    }
    dispose() {
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
exports.PerformanceViewer = PerformanceViewer;
//# sourceMappingURL=performanceViewer.js.map