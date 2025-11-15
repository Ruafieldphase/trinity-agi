import * as vscode from 'vscode';

export type PollerState = 'stopped' | 'polling' | 'busy' | 'error' | 'paused';

export interface QueueStats {
    pending: number;
    inFlight: number;
    successRate: number;
    lastUpdate: Date;
}

/**
 * Manages the Gitko status bar item with real-time poller state and queue stats
 */
export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private currentState: PollerState = 'stopped';
    private stats: QueueStats | null = null;
    private toggleCallback?: () => void;

    constructor(alignment: vscode.StatusBarAlignment = vscode.StatusBarAlignment.Right, priority: number = 100) {
        this.statusBarItem = vscode.window.createStatusBarItem(alignment, priority);
        this.statusBarItem.command = 'gitko.toggleHttpPoller'; // Default toggle command
        this.updateDisplay();
        this.statusBarItem.show();
    }

    /**
     * Set the toggle callback (e.g., enable/disable poller)
     */
    setToggleCallback(callback: () => void) {
        this.toggleCallback = callback;
    }

    /**
     * Update poller state
     */
    setState(state: PollerState) {
        if (this.currentState !== state) {
            this.currentState = state;
            this.updateDisplay();
        }
    }

    /**
     * Update queue statistics
     */
    setStats(stats: Partial<QueueStats>) {
        this.stats = {
            pending: stats.pending ?? this.stats?.pending ?? 0,
            inFlight: stats.inFlight ?? this.stats?.inFlight ?? 0,
            successRate: stats.successRate ?? this.stats?.successRate ?? 0,
            lastUpdate: stats.lastUpdate ?? new Date(),
        };
        this.updateDisplay();
    }

    /**
     * Get current state
     */
    getState(): PollerState {
        return this.currentState;
    }

    /**
     * Show the status bar item
     */
    show() {
        this.statusBarItem.show();
    }

    /**
     * Hide the status bar item
     */
    hide() {
        this.statusBarItem.hide();
    }

    /**
     * Dispose the status bar item
     */
    dispose() {
        this.statusBarItem.dispose();
    }

    /**
     * Handle toggle command
     */
    handleToggle() {
        if (this.toggleCallback) {
            this.toggleCallback();
        }
    }

    /**
     * Update visual display based on current state and stats
     */
    private updateDisplay() {
        const { icon, color, text } = this.getDisplayInfo();

        this.statusBarItem.text = `${icon} ${text}`;
        this.statusBarItem.backgroundColor = color;
        this.statusBarItem.tooltip = this.buildTooltip();
    }

    /**
     * Get display information (icon, color, text) based on state
     */
    private getDisplayInfo(): { icon: string; color: vscode.ThemeColor | undefined; text: string } {
        switch (this.currentState) {
            case 'stopped':
                return {
                    icon: '$(circle-slash)',
                    color: undefined,
                    text: 'Gitko: Off',
                };
            case 'polling':
                return {
                    icon: '$(sync~spin)',
                    color: undefined,
                    text: this.stats ? `Gitko: ${this.stats.pending}/${this.stats.inFlight}` : 'Gitko: Polling',
                };
            case 'busy':
                return {
                    icon: '$(gear~spin)',
                    color: new vscode.ThemeColor('statusBarItem.warningBackground'),
                    text: 'Gitko: Working',
                };
            case 'error':
                return {
                    icon: '$(warning)',
                    color: new vscode.ThemeColor('statusBarItem.errorBackground'),
                    text: 'Gitko: Error',
                };
            case 'paused':
                return {
                    icon: '$(debug-pause)',
                    color: new vscode.ThemeColor('statusBarItem.warningBackground'),
                    text: 'Gitko: Paused',
                };
            default:
                return {
                    icon: '$(circle-outline)',
                    color: undefined,
                    text: 'Gitko',
                };
        }
    }

    /**
     * Build detailed tooltip
     */
    private buildTooltip(): string {
        const lines: string[] = [];

        lines.push('🤖 Gitko Agent Extension');
        lines.push('');

        // State
        lines.push(`State: ${this.getStateLabel()}`);

        // Stats (if available)
        if (this.stats) {
            lines.push('');
            lines.push('Queue Statistics:');
            lines.push(`  • Pending: ${this.stats.pending}`);
            lines.push(`  • In-Flight: ${this.stats.inFlight}`);
            lines.push(`  • Success Rate: ${this.stats.successRate.toFixed(1)}%`);

            const timeSinceUpdate = Date.now() - this.stats.lastUpdate.getTime();
            if (timeSinceUpdate < 60000) {
                lines.push(`  • Updated: ${Math.round(timeSinceUpdate / 1000)}s ago`);
            } else {
                lines.push(`  • Updated: ${Math.round(timeSinceUpdate / 60000)}m ago`);
            }
        }

        lines.push('');
        lines.push('Click to toggle HTTP Poller');

        return lines.join('\n');
    }

    /**
     * Get human-readable state label
     */
    private getStateLabel(): string {
        switch (this.currentState) {
            case 'stopped':
                return '⚫ Stopped';
            case 'polling':
                return '🟢 Polling';
            case 'busy':
                return '🟡 Processing Task';
            case 'error':
                return '🔴 Error';
            case 'paused':
                return '🟠 Paused';
            default:
                return 'Unknown';
        }
    }
}
