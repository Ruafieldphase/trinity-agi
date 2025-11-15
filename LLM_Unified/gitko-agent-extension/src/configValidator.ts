/**
 * Configuration Validator for Gitko Extension
 * Validates user settings and provides helpful error messages
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import { createLogger } from './logger';

const logger = createLogger('ConfigValidator');

export interface ValidationResult {
    isValid: boolean;
    errors: string[];
    warnings: string[];
}

export class ConfigValidator {
    /**
     * Validate all extension configurations
     */
    static validateAll(): ValidationResult {
        const errors: string[] = [];
        const warnings: string[] = [];

        const cfg = vscode.workspace.getConfiguration('gitkoAgent');

        // Validate Python paths
        const pythonPath = cfg.get<string>('pythonPath');
        if (pythonPath && pythonPath.trim()) {
            if (!fs.existsSync(pythonPath)) {
                errors.push(`Python executable not found: ${pythonPath}`);
            }
        } else {
            warnings.push(
                'Python path not configured. It will be auto-detected from workspace.'
            );
        }

        // Validate Computer Use Python path
        const cuPythonPath = cfg.get<string>('computerUsePythonPath');
        if (cuPythonPath && cuPythonPath.trim()) {
            if (!fs.existsSync(cuPythonPath)) {
                errors.push(`Computer Use Python executable not found: ${cuPythonPath}`);
            }
        }

        // Validate script paths
        const scriptPath = cfg.get<string>('scriptPath');
        if (scriptPath && scriptPath.trim()) {
            if (!fs.existsSync(scriptPath)) {
                errors.push(`Script not found: ${scriptPath}`);
            }
        } else {
            warnings.push('Script path not configured. Using auto-detection.');
        }

        // Validate Computer Use script path
        const cuScriptPath = cfg.get<string>('computerUseScriptPath');
        if (cuScriptPath && cuScriptPath.trim()) {
            if (!fs.existsSync(cuScriptPath)) {
                errors.push(`Computer Use script not found: ${cuScriptPath}`);
            }
        }

        // Validate timeout
        const timeout = cfg.get<number>('timeout');
        if (timeout !== undefined && timeout < 1000) {
            warnings.push(`Timeout is very low (${timeout}ms). Consider increasing to at least 30000ms.`);
        }

        // Validate Gitko settings
        const gitkoCfg = vscode.workspace.getConfiguration('gitko');
        const apiBase = gitkoCfg.get<string>('httpApiBase');
        if (apiBase && !apiBase.startsWith('http')) {
            errors.push(`Invalid API base URL: ${apiBase}. Must start with http:// or https://`);
        }

        const pollingInterval = gitkoCfg.get<number>('httpPollingInterval');
        if (pollingInterval !== undefined) {
            if (pollingInterval < 500) {
                errors.push(`Polling interval too low: ${pollingInterval}ms. Minimum is 500ms.`);
            }
            if (pollingInterval > 10000) {
                warnings.push(`Polling interval is high: ${pollingInterval}ms. Tasks may be delayed.`);
            }
        }

        const minUiInterval = gitkoCfg.get<number>('minUiActionIntervalMs');
        if (minUiInterval !== undefined && minUiInterval < 0) {
            errors.push(`UI action interval cannot be negative: ${minUiInterval}ms`);
        }

        // Validate OCR backend
        const ocrBackend = cfg.get<string>('ocrBackend');
        const validBackends = ['auto', 'tesseract', 'rapidocr'];
        if (ocrBackend && !validBackends.includes(ocrBackend)) {
            errors.push(`Invalid OCR backend: ${ocrBackend}. Must be one of: ${validBackends.join(', ')}`);
        }

        return {
            isValid: errors.length === 0,
            errors,
            warnings,
        };
    }

    /**
     * Show validation results to user
     */
    static showValidationResults(result: ValidationResult) {
        if (result.isValid && result.warnings.length === 0) {
            vscode.window.showInformationMessage('✅ All configurations are valid!');
            logger.info('Configuration validation passed');
            return;
        }

        if (result.errors.length > 0) {
            const errorMsg = `Configuration errors:\n${result.errors.join('\n')}`;
            vscode.window.showErrorMessage(errorMsg);
            logger.error('Configuration validation failed', new Error(errorMsg));
        }

        if (result.warnings.length > 0) {
            const warnMsg = `Configuration warnings:\n${result.warnings.join('\n')}`;
            vscode.window.showWarningMessage(warnMsg);
            logger.warn(`Configuration warnings: ${result.warnings.length} issues found`);
        }
    }

    /**
     * Validate and fix common issues
     */
    static async validateAndFix(): Promise<void> {
        const result = this.validateAll();

        if (!result.isValid) {
            const action = await vscode.window.showErrorMessage(
                'Configuration validation failed. Would you like to open settings?',
                'Open Settings',
                'Ignore'
            );

            if (action === 'Open Settings') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'gitkoAgent');
            }
        } else if (result.warnings.length > 0) {
            this.showValidationResults(result);
        } else {
            vscode.window.showInformationMessage('✅ Configuration is valid!');
        }
    }

    /**
     * Quick check for critical paths
     */
    static checkCriticalPaths(): boolean {
        const cfg = vscode.workspace.getConfiguration('gitkoAgent');

        // Check default Python path
        const defaultPython = ''; // Auto-detect from workspace
        const pythonPath = cfg.get<string>('pythonPath') || cfg.get<string>('computerUsePythonPath') || defaultPython;

        if (!fs.existsSync(pythonPath)) {
            logger.error(`Critical: Python not found at ${pythonPath}`);
            return false;
        }

        logger.info(`Python found at: ${pythonPath}`);
        return true;
    }
}
