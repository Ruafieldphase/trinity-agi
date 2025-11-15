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
exports.ResonanceLedgerViewer = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('ResonanceLedger');
/**
 * Resonance Ledger Viewer
 * fdo_agi_repo/memory/resonance_ledger.jsonl 실시간 시각화
 */
class ResonanceLedgerViewer {
    static createOrShow(extensionUri) {
        const column = vscode.ViewColumn.Two;
        // 이미 패널이 있으면 표시
        if (ResonanceLedgerViewer.currentPanel) {
            ResonanceLedgerViewer.currentPanel._panel.reveal(column);
            return;
        }
        // 새 패널 생성
        const panel = vscode.window.createWebviewPanel('resonanceLedgerViewer', '🌊 Resonance Ledger', column, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [extensionUri],
        });
        ResonanceLedgerViewer.currentPanel = new ResonanceLedgerViewer(panel, extensionUri);
    }
    constructor(panel, extensionUri) {
        this._disposables = [];
        this._panel = panel;
        this._extensionUri = extensionUri;
        // Ledger 경로 설정
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            this._ledgerPath = path.join(workspaceFolder.uri.fsPath, 'fdo_agi_repo', 'memory', 'resonance_ledger.jsonl');
        }
        else {
            this._ledgerPath = 'c:\\workspace\\agi\\fdo_agi_repo\\memory\\resonance_ledger.jsonl';
        }
        // 초기 컨텐츠 설정
        this._update();
        // 파일 변경 감지
        this._watchLedgerFile();
        // 5초마다 업데이트 (백업)
        this._updateInterval = setInterval(() => {
            this._update();
        }, 5000);
        // 패널이 닫힐 때 정리
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // 웹뷰 메시지 처리
        this._panel.webview.onDidReceiveMessage((message) => {
            switch (message.command) {
                case 'refresh':
                    this._update();
                    return;
                case 'filterByAgent':
                    this._update(message.agent);
                    return;
            }
        }, null, this._disposables);
    }
    _watchLedgerFile() {
        try {
            if (fs.existsSync(this._ledgerPath)) {
                this._fileWatcher = fs.watch(this._ledgerPath, (eventType) => {
                    if (eventType === 'change') {
                        this._update();
                    }
                });
                logger.debug(`Watching ledger file: ${this._ledgerPath}`);
            }
            else {
                logger.warn(`Ledger file not found: ${this._ledgerPath}`);
            }
        }
        catch (error) {
            logger.error('Failed to watch ledger file', error);
        }
    }
    _update(filterAgent) {
        try {
            const events = this._readLedger(filterAgent);
            this._panel.webview.html = this._getHtmlContent(events);
        }
        catch (error) {
            this._panel.webview.html = this._getErrorHtml(error);
        }
    }
    _readLedger(filterAgent) {
        if (!fs.existsSync(this._ledgerPath)) {
            return [];
        }
        const content = fs.readFileSync(this._ledgerPath, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const events = lines
            .map((line) => {
            try {
                return JSON.parse(line);
            }
            catch {
                return null;
            }
        })
            .filter((e) => e !== null)
            .reverse(); // 최신순
        if (filterAgent) {
            return events.filter((e) => e.agent === filterAgent);
        }
        return events.slice(0, 100); // 최근 100개
    }
    _getHtmlContent(events) {
        const eventsByType = this._groupByType(events);
        const agents = [...new Set(events.map((e) => e.agent).filter(Boolean))];
        const avgScore = events
            .filter((e) => e.resonance_score !== undefined)
            .reduce((sum, e) => sum + (e.resonance_score || 0), 0) / Math.max(events.length, 1);
        return `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resonance Ledger</title>
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
            padding-bottom: 15px;
            border-bottom: 2px solid var(--vscode-panel-border);
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .wave {
            display: inline-block;
            animation: wave 2s ease-in-out infinite;
        }
        @keyframes wave {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }
        .controls {
            display: flex;
            gap: 8px;
        }
        .button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 13px;
        }
        .button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .button.secondary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid var(--vscode-charts-blue);
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            margin: 8px 0;
        }
        .stat-label {
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }
        .timeline {
            position: relative;
            padding-left: 40px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(to bottom, 
                var(--vscode-charts-blue), 
                var(--vscode-charts-purple));
        }
        .event {
            position: relative;
            margin-bottom: 20px;
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 16px;
            border-radius: 8px;
            border-left: 3px solid var(--vscode-charts-blue);
        }
        .event::before {
            content: '';
            position: absolute;
            left: -29px;
            top: 20px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: var(--vscode-charts-blue);
            border: 3px solid var(--vscode-editor-background);
            z-index: 1;
        }
        .event-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .event-type {
            font-weight: bold;
            font-size: 14px;
        }
        .event-time {
            font-size: 11px;
            opacity: 0.6;
            font-family: monospace;
        }
        .event-meta {
            display: flex;
            gap: 8px;
            margin-top: 8px;
            flex-wrap: wrap;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }
        .badge-agent {
            background: var(--vscode-charts-purple);
            color: white;
        }
        .badge-action {
            background: var(--vscode-charts-blue);
            color: white;
        }
        .badge-score {
            background: var(--vscode-charts-green);
            color: white;
        }
        .event-context {
            margin-top: 12px;
            padding: 8px;
            background: var(--vscode-editor-background);
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
        }
        .filter-bar {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            padding: 12px;
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 8px;
        }
        .filter-label {
            font-size: 12px;
            font-weight: bold;
            margin-right: 8px;
            align-self: center;
        }
    </style>
</head>
<body>
    <a class="skip-link" href="#main">Skip to main content</a>
    <div id="sr-status" aria-live="polite" class="sr-only"></div>
    <header class="header" role="banner">
        <h1 aria-label="Resonance Ledger">
            <span class="wave" aria-hidden="true">🌊</span>
            Resonance Ledger
        </h1>
        <div class="controls" role="group" aria-label="Actions">
            <button class="button" onclick="refresh()" aria-label="Refresh ledger"><span aria-hidden="true">🔄</span> Refresh</button>
        </div>
    </header>

    <main id="main" role="main" tabindex="-1">
    <div class="stats" role="region" aria-label="Ledger statistics">
        <div class="stat-card">
            <div class="stat-label">Total Events</div>
            <div class="stat-value">${events.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Resonance Score</div>
            <div class="stat-value">${avgScore.toFixed(2)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Active Agents</div>
            <div class="stat-value">${agents.length}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Event Types</div>
            <div class="stat-value">${Object.keys(eventsByType).length}</div>
        </div>
    </div>

    <div class="filter-bar" role="region" aria-label="Filter controls">
        <span class="filter-label" id="filter-label">Filter by Agent:</span>
        <button class="button secondary" onclick="filterByAgent('')" aria-labelledby="filter-label">All</button>
        ${agents
            .map((agent) => `
            <button class="button secondary" onclick="filterByAgent('${agent}')" aria-label="Filter by agent ${agent}">${agent}</button>
        `)
            .join('')}
    </div>

    <div class="timeline" role="list" aria-label="Events timeline">
        ${events
            .map((event) => `
            <div class="event" role="listitem" aria-label="${event.event_type || 'Unknown Event'} at ${new Date(event.timestamp).toLocaleString()} ${event.agent ? 'by ' + event.agent : ''}">
                <div class="event-header">
                    <span class="event-type">${event.event_type || 'Unknown Event'}</span>
                    <span class="event-time">${new Date(event.timestamp).toLocaleString()}</span>
                </div>
                <div class="event-meta">
                    ${event.agent ? `<span class="badge badge-agent">👤 ${event.agent}</span>` : ''}
                    ${event.action ? `<span class="badge badge-action">⚡ ${event.action}</span>` : ''}
                    ${event.resonance_score !== undefined ? `<span class="badge badge-score">🎯 ${event.resonance_score.toFixed(2)}</span>` : ''}
                </div>
                ${event.result ? `<div style="margin-top: 8px; font-size: 13px;">${event.result}</div>` : ''}
                ${event.context
            ? `
                    <details style="margin-top: 8px;">
                        <summary style="cursor: pointer; font-size: 12px; opacity: 0.8;">Context (toggle)</summary>
                        <div class="event-context">${JSON.stringify(event.context, null, 2)}</div>
                    </details>
                `
            : ''}
                ${event.evidence_link
            ? `
                    <div style="margin-top: 8px; font-size: 11px;">
                        <span aria-hidden="true">🔗</span> <a href="${event.evidence_link}" style="color: var(--vscode-textLink-foreground);">Evidence Link</a>
                    </div>
                `
            : ''}
            </div>
        `)
            .join('')}
    </div>

    ${events.length === 0
            ? `
        <div style="text-align: center; padding: 40px; opacity: 0.6;">
            <p>No events found in Resonance Ledger</p>
            <p style="font-size: 12px;">Path: ${this._ledgerPath}</p>
        </div>
    `
            : ''}

    <script>
        const vscode = acquireVsCodeApi();
        
        function refresh() {
            vscode.postMessage({ command: 'refresh' });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = 'Ledger refreshed';
        }
        
        function filterByAgent(agent) {
            vscode.postMessage({ command: 'filterByAgent', agent: agent });
            const sr = document.getElementById('sr-status');
            if (sr) sr.textContent = agent ? ('Filtered by agent ' + agent) : 'Filter cleared';
        }
    </script>
</main>
</body>
</html>`;
    }
    _groupByType(events) {
        return events.reduce((acc, event) => {
            const type = event.event_type || 'unknown';
            acc[type] = (acc[type] || 0) + 1;
            return acc;
        }, {});
    }
    _getErrorHtml(error) {
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
        <h1>❌ Error Loading Resonance Ledger</h1>
        <p>Failed to read ledger file at <code>${this._ledgerPath}</code></p>
        <details>
            <summary>Error Details</summary>
            <pre>${error instanceof Error ? error.message : String(error)}</pre>
        </details>
    </div>
</body>
</html>`;
    }
    dispose() {
        ResonanceLedgerViewer.currentPanel = undefined;
        if (this._updateInterval) {
            clearInterval(this._updateInterval);
        }
        if (this._fileWatcher) {
            this._fileWatcher.close();
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
exports.ResonanceLedgerViewer = ResonanceLedgerViewer;
//# sourceMappingURL=resonanceLedgerViewer.js.map