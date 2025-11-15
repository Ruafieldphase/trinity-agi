/**
 * Development Utilities for Gitko Extension
 * Helper functions for debugging and development
 */

import * as vscode from 'vscode';
import { createLogger } from './logger';
import { PerformanceMonitor } from './performanceMonitor';
import { exportDiagnosticsBundle, runPreflight } from './diagnostics';
import { runI18nCheck, runI18nSync } from './i18nGuard';

const logger = createLogger('DevUtils');

export class DevUtils {
    /**
     * Get memory usage statistics
     */
    static getMemoryStats(): {
        rss: string;
        heapTotal: string;
        heapUsed: string;
        external: string;
    } {
        const usage = process.memoryUsage();
        return {
            rss: `${(usage.rss / 1024 / 1024).toFixed(2)} MB`,
            heapTotal: `${(usage.heapTotal / 1024 / 1024).toFixed(2)} MB`,
            heapUsed: `${(usage.heapUsed / 1024 / 1024).toFixed(2)} MB`,
            external: `${(usage.external / 1024 / 1024).toFixed(2)} MB`,
        };
    }

    /**
     * Log system information
     */
    static logSystemInfo(): void {
        const memory = this.getMemoryStats();
        logger.info('=== System Information ===');
        logger.info(`Platform: ${process.platform} ${process.arch}`);
        logger.info(`Node: ${process.version}`);
        logger.info(`VS Code: ${vscode.version}`);
        logger.info('=== Memory Usage ===');
        logger.info(`RSS: ${memory.rss}`);
        logger.info(`Heap Total: ${memory.heapTotal}`);
        logger.info(`Heap Used: ${memory.heapUsed}`);
        logger.info(`External: ${memory.external}`);
    }

    /**
     * Create memory usage monitor
     */
    static startMemoryMonitor(intervalMs: number = 60000): NodeJS.Timeout {
        logger.info(`Starting memory monitor (interval: ${intervalMs}ms)`);

        return setInterval(() => {
            const memory = this.getMemoryStats();
            logger.debug(`Memory: RSS=${memory.rss}, Heap=${memory.heapUsed}/${memory.heapTotal}`);

            // Warning if heap usage > 80%
            const heapUsed = parseFloat(memory.heapUsed);
            const heapTotal = parseFloat(memory.heapTotal);
            if (heapUsed / heapTotal > 0.8) {
                logger.warn(`High memory usage: ${((heapUsed / heapTotal) * 100).toFixed(1)}%`);
            }
        }, intervalMs);
    }

    /**
     * Generate diagnostic report
     */
    static async generateDiagnostics(): Promise<string> {
        const memory = this.getMemoryStats();
        const perfMonitor = PerformanceMonitor.getInstance();
        const summary = perfMonitor.getSummary();

        const report = `
# Gitko Extension Diagnostics

**Generated**: ${new Date().toISOString()}

## System Information
- Platform: ${process.platform} ${process.arch}
- Node: ${process.version}
- VS Code: ${vscode.version}

## Memory Usage
- RSS: ${memory.rss}
- Heap Total: ${memory.heapTotal}
- Heap Used: ${memory.heapUsed}
- External: ${memory.external}

## Performance Summary
${Object.entries(summary)
    .map(
        ([op, stats]) => `
### ${op}
- Executions: ${stats.count}
- Success Rate: ${stats.successRate.toFixed(1)}%
- Avg Duration: ${stats.avgDuration.toFixed(0)}ms
`
    )
    .join('\n')}

## Configuration
${JSON.stringify(vscode.workspace.getConfiguration('gitkoAgent'), null, 2)}
${JSON.stringify(vscode.workspace.getConfiguration('gitko'), null, 2)}
`;

        return report;
    }

    /**
     * Export diagnostics to file
     */
    static async exportDiagnostics(): Promise<void> {
        const report = await this.generateDiagnostics();
        const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
        const fileName = `gitko-diagnostics-${timestamp}.md`;

        const uri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file(fileName),
            filters: { Markdown: ['md'], 'All Files': ['*'] },
        });

        if (uri) {
            await vscode.workspace.fs.writeFile(uri, Buffer.from(report, 'utf-8'));
            vscode.window.showInformationMessage(`✅ Diagnostics saved to ${uri.fsPath}`);

            const open = await vscode.window.showInformationMessage('Open diagnostics file?', 'Yes', 'No');

            if (open === 'Yes') {
                await vscode.window.showTextDocument(uri);
            }
        }
    }

    /**
     * Clear all caches and restart
     */
    static async clearAndRestart(): Promise<void> {
        const confirm = await vscode.window.showWarningMessage(
            'Clear all caches and restart extension?',
            { modal: true },
            'Yes',
            'No'
        );

        if (confirm === 'Yes') {
            logger.info('Clearing caches...');

            // Clear performance metrics
            PerformanceMonitor.getInstance().clearMetrics();

            vscode.window
                .showInformationMessage('✅ Caches cleared. Please reload the window.', 'Reload')
                .then((action) => {
                    if (action === 'Reload') {
                        vscode.commands.executeCommand('workbench.action.reloadWindow');
                    }
                });
        }
    }

    /**
     * Run health check
     */
    static async healthCheck(): Promise<{
        healthy: boolean;
        issues: string[];
        warnings: string[];
    }> {
        const issues: string[] = [];
        const warnings: string[] = [];

        // Memory check
        const memory = this.getMemoryStats();
        const heapUsed = parseFloat(memory.heapUsed);
        const heapTotal = parseFloat(memory.heapTotal);

        if (heapUsed / heapTotal > 0.9) {
            issues.push('Critical memory usage (>90%)');
        } else if (heapUsed / heapTotal > 0.8) {
            warnings.push('High memory usage (>80%)');
        }

        // Performance check
        const perfMonitor = PerformanceMonitor.getInstance();
        const summary = perfMonitor.getSummary();

        for (const [op, stats] of Object.entries(summary)) {
            if (stats.successRate < 50) {
                issues.push(`Low success rate for ${op}: ${stats.successRate.toFixed(1)}%`);
            } else if (stats.successRate < 80) {
                warnings.push(`Moderate success rate for ${op}: ${stats.successRate.toFixed(1)}%`);
            }

            if (stats.avgDuration > 10000) {
                warnings.push(`Slow operation ${op}: ${stats.avgDuration.toFixed(0)}ms avg`);
            }
        }

        return {
            healthy: issues.length === 0,
            issues,
            warnings,
        };
    }

    /**
     * Show health check results
     */
    static async showHealthCheck(): Promise<void> {
        const health = await this.healthCheck();
        const outputChannel = vscode.window.createOutputChannel('Gitko Health Check');

        outputChannel.clear();
        outputChannel.appendLine('=== Gitko Extension Health Check ===\n');
        outputChannel.appendLine(`Status: ${health.healthy ? '✅ Healthy' : '❌ Issues Detected'}\n`);

        if (health.issues.length > 0) {
            outputChannel.appendLine('🔴 Issues:');
            health.issues.forEach((issue) => outputChannel.appendLine(`  - ${issue}`));
            outputChannel.appendLine('');
        }

        if (health.warnings.length > 0) {
            outputChannel.appendLine('⚠️ Warnings:');
            health.warnings.forEach((warning) => outputChannel.appendLine(`  - ${warning}`));
            outputChannel.appendLine('');
        }

        if (health.healthy && health.warnings.length === 0) {
            outputChannel.appendLine('✅ All systems operational!');
        }

        outputChannel.show();

        if (!health.healthy) {
            vscode.window
                .showWarningMessage(`Health check failed: ${health.issues.length} issue(s) found`, 'View Details')
                .then((action) => {
                    if (action === 'View Details') {
                        outputChannel.show();
                    }
                });
        }
    }
}

/**
 * Register dev utility commands
 */
export function registerDevCommands(context: vscode.ExtensionContext): void {
    // System info command
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.showSystemInfo', () => {
            DevUtils.logSystemInfo();
            vscode.window.showInformationMessage('System info logged to Output Channel');
        })
    );

    // Memory stats command
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.showMemoryStats', () => {
            const stats = DevUtils.getMemoryStats();
            vscode.window.showInformationMessage(`Memory: RSS=${stats.rss}, Heap=${stats.heapUsed}/${stats.heapTotal}`);
        })
    );

    // Export diagnostics command
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.exportDiagnostics', () => {
            DevUtils.exportDiagnostics();
        })
    );

    // Export diagnostics bundle (ZIP)
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.exportDiagnosticsBundle', () => {
            exportDiagnosticsBundle();
        })
    );

    // Run preflight checks
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.preflight', async () => {
            const result = await runPreflight();
            const ch = vscode.window.createOutputChannel('Gitko Preflight');
            ch.clear();
            ch.appendLine('=== Gitko Preflight Checks ===\n');
            for (const c of result.checks) {
                ch.appendLine(`${c.ok ? '✅' : '❌'} ${c.name}${c.message ? ` - ${c.message}` : ''}`);
            }
            ch.show();
            if (!result.ok) {
                vscode.window.showWarningMessage('Preflight checks found issues. See Output for details.');
            } else {
                vscode.window.showInformationMessage('Preflight checks passed.');
            }
        })
    );

    // i18n coverage check
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.i18nCheck', async () => {
            const r = await runI18nCheck();
            if (r.missingInEn.length || r.missingInKo.length) {
                vscode.window.showWarningMessage('i18n: Missing keys detected. See Output for details.');
            } else {
                vscode.window.showInformationMessage('i18n: No missing keys.');
            }
        })
    );

    // i18n sync
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.i18nSync', async () => {
            await runI18nSync();
        })
    );

    // Health check command
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.healthCheck', () => {
            DevUtils.showHealthCheck();
        })
    );

    // Clear and restart command
    context.subscriptions.push(
        vscode.commands.registerCommand('gitko.dev.clearAndRestart', () => {
            DevUtils.clearAndRestart();
        })
    );

    logger.debug('Dev utility commands registered');
}
