/**
 * Integration Test Helper for Gitko Extension
 * Tests all major components programmatically
 */

import * as vscode from 'vscode';
import { PerformanceMonitor } from './performanceMonitor';
import { ConfigValidator } from './configValidator';
import { createLogger } from './logger';

const logger = createLogger('IntegrationTest');

export async function runIntegrationTests(): Promise<{
    passed: number;
    failed: number;
    results: Array<{ test: string; passed: boolean; error?: string }>;
}> {
    const results: Array<{ test: string; passed: boolean; error?: string }> = [];
    let passed = 0;
    let failed = 0;

    logger.info('Starting integration tests...');

    // Test 1: Logger
    try {
        logger.debug('Test debug message');
        logger.info('Test info message');
        logger.warn('Test warning message');
        results.push({ test: 'Logger', passed: true });
        passed++;
    } catch (error) {
        results.push({
            test: 'Logger',
            passed: false,
            error: error instanceof Error ? error.message : String(error),
        });
        failed++;
    }

    // Test 2: Performance Monitor
    try {
        const monitor = PerformanceMonitor.getInstance();
        const opId = monitor.startOperation('test.operation');
        await new Promise((resolve) => setTimeout(resolve, 10)); // Simulate work
        monitor.endOperation(opId, true);

        const stats = monitor.getOperationStats('test.operation');
        if (stats.totalCount === 1 && stats.successCount === 1) {
            results.push({ test: 'Performance Monitor', passed: true });
            passed++;
        } else {
            throw new Error('Performance stats mismatch');
        }

        monitor.clearMetrics('test.operation');
    } catch (error) {
        results.push({
            test: 'Performance Monitor',
            passed: false,
            error: error instanceof Error ? error.message : String(error),
        });
        failed++;
    }

    // Test 3: Config Validator
    try {
        const validation = ConfigValidator.validateAll();
        results.push({
            test: 'Config Validator',
            passed: true,
            error: validation.isValid ? undefined : `${validation.errors.length} errors found`,
        });
        passed++;
    } catch (error) {
        results.push({
            test: 'Config Validator',
            passed: false,
            error: error instanceof Error ? error.message : String(error),
        });
        failed++;
    }

    // Test 4: Extension Commands
    try {
        const commands = await vscode.commands.getCommands(true);
        const gitkoCommands = commands.filter((cmd) => cmd.startsWith('gitko.'));

        const expectedCommands = [
            'gitko.enableHttpPoller',
            'gitko.disableHttpPoller',
            'gitko.showTaskQueueMonitor',
            'gitko.showResonanceLedger',
            'gitko.validateConfig',
            'gitko.showPerformanceViewer',
        ];

        const allFound = expectedCommands.every((cmd) => gitkoCommands.includes(cmd));

        if (allFound) {
            results.push({
                test: 'Extension Commands',
                passed: true,
                error: `Found ${gitkoCommands.length} commands`,
            });
            passed++;
        } else {
            throw new Error(`Missing commands. Found: ${gitkoCommands.length}, Expected: ${expectedCommands.length}`);
        }
    } catch (error) {
        results.push({
            test: 'Extension Commands',
            passed: false,
            error: error instanceof Error ? error.message : String(error),
        });
        failed++;
    }

    logger.info(`Integration tests completed: ${passed} passed, ${failed} failed`);

    return { passed, failed, results };
}

/**
 * Register integration test command
 */
export function registerIntegrationTestCommand(context: vscode.ExtensionContext) {
    const testCmd = vscode.commands.registerCommand('gitko.runIntegrationTests', async () => {
        const result = await runIntegrationTests();

        const message = `Integration Tests: ${result.passed}/${result.passed + result.failed} passed`;

        if (result.failed === 0) {
            vscode.window.showInformationMessage(`✅ ${message}`);
        } else {
            vscode.window.showWarningMessage(`⚠️ ${message}`);
        }

        // Show detailed results in Output Channel
        const outputChannel = vscode.window.createOutputChannel('Gitko Integration Tests');
        outputChannel.clear();
        outputChannel.appendLine('=== Integration Test Results ===\n');

        result.results.forEach((r, i) => {
            const status = r.passed ? '✅' : '❌';
            outputChannel.appendLine(`${i + 1}. ${status} ${r.test}`);
            if (r.error) {
                outputChannel.appendLine(`   ${r.error}`);
            }
        });

        outputChannel.appendLine(`\n=== Summary ===`);
        outputChannel.appendLine(`Passed: ${result.passed}`);
        outputChannel.appendLine(`Failed: ${result.failed}`);
        outputChannel.appendLine(`Total: ${result.passed + result.failed}`);

        outputChannel.show();
    });

    context.subscriptions.push(testCmd);
}
