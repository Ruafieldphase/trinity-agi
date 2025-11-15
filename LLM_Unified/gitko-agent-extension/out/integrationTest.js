"use strict";
/**
 * Integration Test Helper for Gitko Extension
 * Tests all major components programmatically
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
exports.runIntegrationTests = runIntegrationTests;
exports.registerIntegrationTestCommand = registerIntegrationTestCommand;
const vscode = __importStar(require("vscode"));
const performanceMonitor_1 = require("./performanceMonitor");
const configValidator_1 = require("./configValidator");
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('IntegrationTest');
async function runIntegrationTests() {
    const results = [];
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
    }
    catch (error) {
        results.push({
            test: 'Logger',
            passed: false,
            error: error instanceof Error ? error.message : String(error)
        });
        failed++;
    }
    // Test 2: Performance Monitor
    try {
        const monitor = performanceMonitor_1.PerformanceMonitor.getInstance();
        const opId = monitor.startOperation('test.operation');
        await new Promise(resolve => setTimeout(resolve, 10)); // Simulate work
        monitor.endOperation(opId, true);
        const stats = monitor.getOperationStats('test.operation');
        if (stats.totalCount === 1 && stats.successCount === 1) {
            results.push({ test: 'Performance Monitor', passed: true });
            passed++;
        }
        else {
            throw new Error('Performance stats mismatch');
        }
        monitor.clearMetrics('test.operation');
    }
    catch (error) {
        results.push({
            test: 'Performance Monitor',
            passed: false,
            error: error instanceof Error ? error.message : String(error)
        });
        failed++;
    }
    // Test 3: Config Validator
    try {
        const validation = configValidator_1.ConfigValidator.validateAll();
        results.push({
            test: 'Config Validator',
            passed: true,
            error: validation.isValid ? undefined : `${validation.errors.length} errors found`
        });
        passed++;
    }
    catch (error) {
        results.push({
            test: 'Config Validator',
            passed: false,
            error: error instanceof Error ? error.message : String(error)
        });
        failed++;
    }
    // Test 4: Extension Commands
    try {
        const commands = await vscode.commands.getCommands(true);
        const gitkoCommands = commands.filter(cmd => cmd.startsWith('gitko.'));
        const expectedCommands = [
            'gitko.enableHttpPoller',
            'gitko.disableHttpPoller',
            'gitko.showTaskQueueMonitor',
            'gitko.showResonanceLedger',
            'gitko.validateConfig',
            'gitko.showPerformanceViewer'
        ];
        const allFound = expectedCommands.every(cmd => gitkoCommands.includes(cmd));
        if (allFound) {
            results.push({
                test: 'Extension Commands',
                passed: true,
                error: `Found ${gitkoCommands.length} commands`
            });
            passed++;
        }
        else {
            throw new Error(`Missing commands. Found: ${gitkoCommands.length}, Expected: ${expectedCommands.length}`);
        }
    }
    catch (error) {
        results.push({
            test: 'Extension Commands',
            passed: false,
            error: error instanceof Error ? error.message : String(error)
        });
        failed++;
    }
    logger.info(`Integration tests completed: ${passed} passed, ${failed} failed`);
    return { passed, failed, results };
}
/**
 * Register integration test command
 */
function registerIntegrationTestCommand(context) {
    const testCmd = vscode.commands.registerCommand('gitko.runIntegrationTests', async () => {
        const result = await runIntegrationTests();
        const message = `Integration Tests: ${result.passed}/${result.passed + result.failed} passed`;
        if (result.failed === 0) {
            vscode.window.showInformationMessage(`✅ ${message}`);
        }
        else {
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
//# sourceMappingURL=integrationTest.js.map