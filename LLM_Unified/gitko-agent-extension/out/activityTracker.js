"use strict";
/**
 * Activity Tracker for Gitko Extension
 * Tracks user actions and system events for analytics
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
exports.ActivityViewer = exports.ActivityTracker = void 0;
const vscode = __importStar(require("vscode"));
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('ActivityTracker');
class ActivityTracker {
    constructor() {
        this.events = [];
        this.MAX_EVENTS = 500;
        this.commandCounts = new Map();
        this.agentCalls = new Map();
        this.sessionStart = Date.now();
        logger.debug('ActivityTracker initialized');
    }
    static getInstance() {
        if (!ActivityTracker.instance) {
            ActivityTracker.instance = new ActivityTracker();
        }
        return ActivityTracker.instance;
    }
    /**
     * Track a command execution
     */
    trackCommand(commandId, duration) {
        this.addEvent({
            timestamp: Date.now(),
            type: 'command',
            action: commandId,
            duration
        });
        const count = this.commandCounts.get(commandId) || 0;
        this.commandCounts.set(commandId, count + 1);
    }
    /**
     * Track an agent call
     */
    trackAgentCall(agentName, success, duration) {
        this.addEvent({
            timestamp: Date.now(),
            type: 'agent',
            action: agentName,
            details: { success },
            duration
        });
        const count = this.agentCalls.get(agentName) || 0;
        this.agentCalls.set(agentName, count + 1);
    }
    /**
     * Track a task execution
     */
    trackTask(taskType, success, duration) {
        this.addEvent({
            timestamp: Date.now(),
            type: 'task',
            action: taskType,
            details: { success },
            duration
        });
    }
    /**
     * Track an error
     */
    trackError(source, error) {
        this.addEvent({
            timestamp: Date.now(),
            type: 'error',
            action: source,
            details: {
                error: error instanceof Error ? error.message : error
            }
        });
    }
    /**
     * Track a system event
     */
    trackSystemEvent(event, details) {
        this.addEvent({
            timestamp: Date.now(),
            type: 'system',
            action: event,
            details
        });
    }
    /**
     * Add event with automatic cleanup
     */
    addEvent(event) {
        this.events.push(event);
        // Auto cleanup if exceeds limit
        if (this.events.length > this.MAX_EVENTS) {
            this.events = this.events.slice(-this.MAX_EVENTS);
            logger.debug(`Activity events trimmed to ${this.MAX_EVENTS}`);
        }
    }
    /**
     * Get recent events
     */
    getRecentEvents(count = 50) {
        return this.events.slice(-count);
    }
    /**
     * Get events by type
     */
    getEventsByType(type) {
        return this.events.filter(e => e.type === type);
    }
    /**
     * Get session statistics
     */
    getSessionStats() {
        const now = Date.now();
        const sessionDuration = now - this.sessionStart;
        const topCommands = Array.from(this.commandCounts.entries())
            .map(([command, count]) => ({ command, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
        const topAgents = Array.from(this.agentCalls.entries())
            .map(([agent, count]) => ({ agent, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 5);
        return {
            sessionDuration,
            totalEvents: this.events.length,
            commandCount: this.events.filter(e => e.type === 'command').length,
            agentCallCount: this.events.filter(e => e.type === 'agent').length,
            taskCount: this.events.filter(e => e.type === 'task').length,
            errorCount: this.events.filter(e => e.type === 'error').length,
            topCommands,
            topAgents
        };
    }
    /**
     * Export activity log
     */
    exportLog() {
        const stats = this.getSessionStats();
        const sessionHours = (stats.sessionDuration / (1000 * 60 * 60)).toFixed(2);
        let report = `# Gitko Extension Activity Log\n\n`;
        report += `**Generated**: ${new Date().toISOString()}\n`;
        report += `**Session Duration**: ${sessionHours} hours\n\n`;
        report += `## Summary\n\n`;
        report += `- Total Events: ${stats.totalEvents}\n`;
        report += `- Commands Executed: ${stats.commandCount}\n`;
        report += `- Agent Calls: ${stats.agentCallCount}\n`;
        report += `- Tasks Processed: ${stats.taskCount}\n`;
        report += `- Errors: ${stats.errorCount}\n\n`;
        if (stats.topCommands.length > 0) {
            report += `## Top Commands\n\n`;
            stats.topCommands.forEach((cmd, i) => {
                report += `${i + 1}. \`${cmd.command}\` - ${cmd.count} times\n`;
            });
            report += `\n`;
        }
        if (stats.topAgents.length > 0) {
            report += `## Top Agents\n\n`;
            stats.topAgents.forEach((agent, i) => {
                report += `${i + 1}. **${agent.agent}** - ${agent.count} calls\n`;
            });
            report += `\n`;
        }
        report += `## Recent Events (Last 20)\n\n`;
        const recent = this.getRecentEvents(20);
        recent.forEach(event => {
            const time = new Date(event.timestamp).toLocaleTimeString();
            const duration = event.duration ? ` (${event.duration}ms)` : '';
            report += `- \`${time}\` [${event.type}] ${event.action}${duration}\n`;
        });
        return report;
    }
    /**
     * Clear all tracked data
     */
    clear() {
        this.events = [];
        this.commandCounts.clear();
        this.agentCalls.clear();
        this.sessionStart = Date.now();
        logger.info('Activity tracker cleared');
    }
    /**
     * Get activity summary for display
     */
    getSummary() {
        const stats = this.getSessionStats();
        const sessionMinutes = Math.floor(stats.sessionDuration / (1000 * 60));
        return `📊 Session: ${sessionMinutes}min | Commands: ${stats.commandCount} | Agents: ${stats.agentCallCount} | Errors: ${stats.errorCount}`;
    }
}
exports.ActivityTracker = ActivityTracker;
/**
 * Activity Viewer WebView
 */
class ActivityViewer {
    constructor() {
        this.tracker = ActivityTracker.getInstance();
    }
    show(context) {
        if (this.panel) {
            this.panel.reveal();
            return;
        }
        this.panel = vscode.window.createWebviewPanel('gitkoActivityViewer', 'Gitko Activity Tracker', vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true
        });
        this.panel.webview.html = this.getHtmlContent();
        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(message => {
            switch (message.command) {
                case 'refresh':
                    this.updateContent();
                    break;
                case 'export':
                    this.exportActivity();
                    break;
                case 'clear':
                    this.clearActivity();
                    break;
            }
        }, undefined, context.subscriptions);
        this.panel.onDidDispose(() => {
            this.panel = undefined;
        });
        // Auto-refresh every 5 seconds
        const interval = setInterval(() => {
            if (this.panel) {
                this.updateContent();
            }
            else {
                clearInterval(interval);
            }
        }, 5000);
    }
    updateContent() {
        if (!this.panel) {
            return;
        }
        const stats = this.tracker.getSessionStats();
        const recent = this.tracker.getRecentEvents(50);
        this.panel.webview.postMessage({
            command: 'update',
            stats,
            events: recent
        });
    }
    async exportActivity() {
        const log = this.tracker.exportLog();
        const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
        const fileName = `gitko-activity-${timestamp}.md`;
        const uri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file(fileName),
            filters: { 'Markdown': ['md'], 'All Files': ['*'] }
        });
        if (uri) {
            await vscode.workspace.fs.writeFile(uri, Buffer.from(log, 'utf-8'));
            vscode.window.showInformationMessage(`✅ Activity log saved to ${uri.fsPath}`);
        }
    }
    clearActivity() {
        vscode.window.showWarningMessage('Clear all activity data?', { modal: true }, 'Yes', 'No').then(answer => {
            if (answer === 'Yes') {
                this.tracker.clear();
                this.updateContent();
                vscode.window.showInformationMessage('Activity data cleared');
            }
        });
    }
    getHtmlContent() {
        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Tracker</title>
    <style>
        body { 
            font-family: var(--vscode-font-family); 
            padding: 20px; 
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
        }
        h1, h2 { color: var(--vscode-textLink-foreground); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { 
            background: var(--vscode-editor-background); 
            border: 1px solid var(--vscode-panel-border);
            padding: 15px; 
            border-radius: 5px; 
        }
        .stat-value { font-size: 2em; font-weight: bold; color: var(--vscode-textLink-foreground); }
        .stat-label { font-size: 0.9em; opacity: 0.8; margin-top: 5px; }
        .events { margin-top: 30px; }
        .event { 
            padding: 10px; 
            margin: 5px 0; 
            background: var(--vscode-editor-background);
            border-left: 3px solid var(--vscode-textLink-foreground);
            font-family: var(--vscode-editor-font-family);
            font-size: 0.9em;
        }
        .event-command { border-left-color: #4CAF50; }
        .event-agent { border-left-color: #2196F3; }
        .event-task { border-left-color: #FF9800; }
        .event-error { border-left-color: #f44336; }
        .event-system { border-left-color: #9C27B0; }
        .timestamp { opacity: 0.6; font-size: 0.85em; }
        .duration { color: var(--vscode-textLink-foreground); }
        .buttons { margin: 20px 0; }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 10px 20px;
            margin-right: 10px;
            cursor: pointer;
            border-radius: 3px;
        }
        button:hover { background: var(--vscode-button-hoverBackground); }
        .top-list { margin: 15px 0; }
        .top-item { padding: 8px; margin: 5px 0; background: var(--vscode-editor-background); border-radius: 3px; }
    </style>
</head>
<body>
    <h1>📊 Gitko Activity Tracker</h1>
    
    <div class="buttons">
        <button onclick="refresh()">🔄 Refresh</button>
        <button onclick="exportLog()">💾 Export</button>
        <button onclick="clearData()">🗑️ Clear</button>
    </div>

    <div class="stats" id="stats"></div>

    <h2>Top Commands</h2>
    <div class="top-list" id="topCommands"></div>

    <h2>Top Agents</h2>
    <div class="top-list" id="topAgents"></div>

    <h2>Recent Events</h2>
    <div class="events" id="events"></div>

    <script>
        const vscode = acquireVsCodeApi();

        function refresh() { vscode.postMessage({ command: 'refresh' }); }
        function exportLog() { vscode.postMessage({ command: 'export' }); }
        function clearData() { vscode.postMessage({ command: 'clear' }); }

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.command === 'update') {
                updateStats(message.stats);
                updateEvents(message.events);
            }
        });

        function updateStats(stats) {
            const sessionHours = (stats.sessionDuration / (1000 * 60 * 60)).toFixed(2);
            document.getElementById('stats').innerHTML = \`
                <div class="stat-card">
                    <div class="stat-value">\${sessionHours}h</div>
                    <div class="stat-label">Session Duration</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.totalEvents}</div>
                    <div class="stat-label">Total Events</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.commandCount}</div>
                    <div class="stat-label">Commands</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.agentCallCount}</div>
                    <div class="stat-label">Agent Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.taskCount}</div>
                    <div class="stat-label">Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.errorCount}</div>
                    <div class="stat-label">Errors</div>
                </div>
            \`;

            // Top commands
            const topCmds = stats.topCommands.map((cmd, i) => 
                \`<div class="top-item">\${i+1}. <code>\${cmd.command}</code> - \${cmd.count} times</div>\`
            ).join('');
            document.getElementById('topCommands').innerHTML = topCmds || '<div>No commands yet</div>';

            // Top agents
            const topAgts = stats.topAgents.map((agt, i) => 
                \`<div class="top-item">\${i+1}. <strong>\${agt.agent}</strong> - \${agt.count} calls</div>\`
            ).join('');
            document.getElementById('topAgents').innerHTML = topAgts || '<div>No agent calls yet</div>';
        }

        function updateEvents(events) {
            const html = events.reverse().map(event => {
                const time = new Date(event.timestamp).toLocaleTimeString();
                const duration = event.duration ? \` <span class="duration">(\${event.duration}ms)</span>\` : '';
                return \`
                    <div class="event event-\${event.type}">
                        <span class="timestamp">\${time}</span> 
                        [\${event.type}] <strong>\${event.action}</strong>\${duration}
                    </div>
                \`;
            }).join('');
            document.getElementById('events').innerHTML = html || '<div>No events yet</div>';
        }

        // Initial load
        refresh();
    </script>
</body>
</html>`;
    }
}
exports.ActivityViewer = ActivityViewer;
//# sourceMappingURL=activityTracker.js.map