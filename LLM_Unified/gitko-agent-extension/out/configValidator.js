"use strict";
/**
 * Configuration Validator for Gitko Extension
 * Validates user settings and provides helpful error messages
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
exports.ConfigValidator = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('ConfigValidator');
class ConfigValidator {
    /**
     * Validate all extension configurations
     */
    static validateAll() {
        const errors = [];
        const warnings = [];
        const cfg = vscode.workspace.getConfiguration('gitkoAgent');
        // Validate Python paths
        const pythonPath = cfg.get('pythonPath');
        if (pythonPath && pythonPath.trim()) {
            if (!fs.existsSync(pythonPath)) {
                errors.push(`Python executable not found: ${pythonPath}`);
            }
        }
        else {
            warnings.push('Python path not configured. Using default: D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe');
        }
        // Validate Computer Use Python path
        const cuPythonPath = cfg.get('computerUsePythonPath');
        if (cuPythonPath && cuPythonPath.trim()) {
            if (!fs.existsSync(cuPythonPath)) {
                errors.push(`Computer Use Python executable not found: ${cuPythonPath}`);
            }
        }
        // Validate script paths
        const scriptPath = cfg.get('scriptPath');
        if (scriptPath && scriptPath.trim()) {
            if (!fs.existsSync(scriptPath)) {
                errors.push(`Script not found: ${scriptPath}`);
            }
        }
        else {
            warnings.push('Script path not configured. Using auto-detection.');
        }
        // Validate Computer Use script path
        const cuScriptPath = cfg.get('computerUseScriptPath');
        if (cuScriptPath && cuScriptPath.trim()) {
            if (!fs.existsSync(cuScriptPath)) {
                errors.push(`Computer Use script not found: ${cuScriptPath}`);
            }
        }
        // Validate timeout
        const timeout = cfg.get('timeout');
        if (timeout !== undefined && timeout < 1000) {
            warnings.push(`Timeout is very low (${timeout}ms). Consider increasing to at least 30000ms.`);
        }
        // Validate Gitko settings
        const gitkoCfg = vscode.workspace.getConfiguration('gitko');
        const apiBase = gitkoCfg.get('httpApiBase');
        if (apiBase && !apiBase.startsWith('http')) {
            errors.push(`Invalid API base URL: ${apiBase}. Must start with http:// or https://`);
        }
        const pollingInterval = gitkoCfg.get('httpPollingInterval');
        if (pollingInterval !== undefined) {
            if (pollingInterval < 500) {
                errors.push(`Polling interval too low: ${pollingInterval}ms. Minimum is 500ms.`);
            }
            if (pollingInterval > 10000) {
                warnings.push(`Polling interval is high: ${pollingInterval}ms. Tasks may be delayed.`);
            }
        }
        const minUiInterval = gitkoCfg.get('minUiActionIntervalMs');
        if (minUiInterval !== undefined && minUiInterval < 0) {
            errors.push(`UI action interval cannot be negative: ${minUiInterval}ms`);
        }
        // Validate OCR backend
        const ocrBackend = cfg.get('ocrBackend');
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
    static showValidationResults(result) {
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
    static async validateAndFix() {
        const result = this.validateAll();
        if (!result.isValid) {
            const action = await vscode.window.showErrorMessage('Configuration validation failed. Would you like to open settings?', 'Open Settings', 'Ignore');
            if (action === 'Open Settings') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'gitkoAgent');
            }
        }
        else if (result.warnings.length > 0) {
            this.showValidationResults(result);
        }
        else {
            vscode.window.showInformationMessage('✅ Configuration is valid!');
        }
    }
    /**
     * Quick check for critical paths
     */
    static checkCriticalPaths() {
        const cfg = vscode.workspace.getConfiguration('gitkoAgent');
        // Check default Python path
        const defaultPython = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
        const pythonPath = cfg.get('pythonPath') || cfg.get('computerUsePythonPath') || defaultPython;
        if (!fs.existsSync(pythonPath)) {
            logger.error(`Critical: Python not found at ${pythonPath}`);
            return false;
        }
        logger.info(`Python found at: ${pythonPath}`);
        return true;
    }
}
exports.ConfigValidator = ConfigValidator;
//# sourceMappingURL=configValidator.js.map