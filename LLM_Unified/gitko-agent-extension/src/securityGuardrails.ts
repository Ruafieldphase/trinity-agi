import * as vscode from 'vscode';
import { createLogger } from './logger';
import { t } from './i18n';

const logger = createLogger('SecurityGuardrails');

/**
 * Security Guardrails for Computer Use (RPA)
 *
 * Implements:
 * - Rate limiting (daily action limits)
 * - Confirmation prompts for destructive actions
 * - Audit logging
 * - Global killswitch
 */

interface ActionLog {
    timestamp: number;
    action: string;
    allowed: boolean;
    reason?: string;
}

export class SecurityGuardrails {
    private static instance: SecurityGuardrails;
    private actionLog: ActionLog[] = [];
    private dailyActionCount: number = 0;
    private lastResetDate: string = '';
    private isKillswitchActive: boolean = false;

    // Rate limits
    private readonly maxDailyActions: number = 100;
    private readonly maxActionsPerMinute: number = 10;
    private recentActions: number[] = []; // timestamps

    // Destructive action patterns
    private readonly destructivePatterns = [
        /rm\s+-rf/i,
        /del\s+\/s/i,
        /format\s+[a-z]:/i,
        /shutdown/i,
        /restart/i,
        /delete.*database/i,
        /drop\s+table/i,
        /truncate/i,
    ];

    private constructor() {
        this.resetIfNewDay();
    }

    public static getInstance(): SecurityGuardrails {
        if (!SecurityGuardrails.instance) {
            SecurityGuardrails.instance = new SecurityGuardrails();
        }
        return SecurityGuardrails.instance;
    }

    /**
     * Check if action is allowed
     */
    public async checkAction(action: string, data: unknown): Promise<{ allowed: boolean; reason?: string }> {
        // Reset counters if new day
        this.resetIfNewDay();

        // Check killswitch
        if (this.isKillswitchActive) {
            this.logAction(action, false, 'Killswitch active');
            return { allowed: false, reason: t('security.killswitchEnabled') };
        }

        // Check daily limit
        if (this.dailyActionCount >= this.maxDailyActions) {
            this.logAction(action, false, 'Daily limit exceeded');
            return { allowed: false, reason: t('security.dailyLimitExceeded', this.maxDailyActions) };
        }

        // Check per-minute rate limit
        const now = Date.now();
        this.recentActions = this.recentActions.filter((ts) => now - ts < 60000);
        if (this.recentActions.length >= this.maxActionsPerMinute) {
            this.logAction(action, false, 'Rate limit exceeded');
            return {
                allowed: false,
                reason: t('security.rateLimitExceeded', this.maxActionsPerMinute),
            };
        }

        // Check for destructive patterns
        const isDestructive = this.isDestructiveAction(action, data);
        if (isDestructive) {
            const confirmed = await this.confirmDestructiveAction(action);
            if (!confirmed) {
                this.logAction(action, false, 'User declined destructive action');
                return { allowed: false, reason: 'Destructive action declined by user' };
            }
        }

        // Action allowed
        this.recentActions.push(now);
        this.dailyActionCount++;
        this.logAction(action, true);
        return { allowed: true };
    }

    /**
     * Check if action is destructive
     */
    private isDestructiveAction(action: string, data: unknown): boolean {
        // Check action type
        if (action === 'computer_use.type') {
            const text = (data as { text?: string })?.text || '';
            return this.destructivePatterns.some((pattern) => pattern.test(text));
        }

        // Specific destructive actions
        const destructiveActions = ['computer_use.delete', 'computer_use.shutdown'];
        if (destructiveActions.includes(action)) {
            return true;
        }

        return false;
    }

    /**
     * Confirm destructive action with user
     */
    private async confirmDestructiveAction(action: string): Promise<boolean> {
        const result = await vscode.window.showWarningMessage(
            t('security.destructiveActionConfirm', action),
            { modal: true },
            t('common.allow'),
            t('common.deny')
        );
        return result === t('common.allow');
    }

    /**
     * Log action
     */
    private logAction(action: string, allowed: boolean, reason?: string): void {
        const entry: ActionLog = {
            timestamp: Date.now(),
            action,
            allowed,
            reason,
        };
        this.actionLog.push(entry);

        // Keep only last 1000 entries
        if (this.actionLog.length > 1000) {
            this.actionLog = this.actionLog.slice(-1000);
        }

        logger.info(`[Security] ${allowed ? '✅' : '❌'} ${action}${reason ? ` (${reason})` : ''}`);
    }

    /**
     * Reset counters if new day
     */
    private resetIfNewDay(): void {
        const today = new Date().toISOString().split('T')[0];
        if (this.lastResetDate !== today) {
            this.dailyActionCount = 0;
            this.lastResetDate = today;
            logger.info(`[Security] Daily counters reset (${today})`);
        }
    }

    /**
     * Toggle killswitch
     */
    public toggleKillswitch(): void {
        this.isKillswitchActive = !this.isKillswitchActive;
        const state = this.isKillswitchActive ? 'ENABLED' : 'DISABLED';
        logger.info(`[Security] 🔴 Killswitch ${state}`);
        const message = this.isKillswitchActive ? t('security.killswitchEnabled') : t('security.killswitchDisabled');
        vscode.window.showInformationMessage(message);
    }

    /**
     * Get killswitch state
     */
    public isKillswitchEnabled(): boolean {
        return this.isKillswitchActive;
    }

    /**
     * Get statistics
     */
    public getStats(): {
        dailyActions: number;
        maxDailyActions: number;
        recentActionsPerMin: number;
        totalLogged: number;
        killswitchActive: boolean;
    } {
        return {
            dailyActions: this.dailyActionCount,
            maxDailyActions: this.maxDailyActions,
            recentActionsPerMin: this.recentActions.length,
            totalLogged: this.actionLog.length,
            killswitchActive: this.isKillswitchActive,
        };
    }

    /**
     * Get audit log
     */
    public getAuditLog(limit: number = 100): ActionLog[] {
        return this.actionLog.slice(-limit);
    }

    /**
     * Export audit log as JSON
     */
    public async exportAuditLog(): Promise<void> {
        try {
            const uri = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.file(`computer-use-audit-${Date.now()}.json`),
                filters: {
                    JSON: ['json'],
                },
            });

            if (uri) {
                const content = JSON.stringify(
                    {
                        exportedAt: new Date().toISOString(),
                        stats: this.getStats(),
                        log: this.actionLog,
                    },
                    null,
                    2
                );
                await vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf-8'));
                vscode.window.showInformationMessage(t('security.auditLogExported', uri.fsPath));
            }
        } catch (error) {
            logger.error('[Security] Failed to export audit log:', error);
            vscode.window.showErrorMessage(t('security.auditLogExportFailed'));
        }
    }
}
