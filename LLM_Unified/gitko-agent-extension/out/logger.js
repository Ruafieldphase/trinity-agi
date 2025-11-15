"use strict";
/**
 * Unified Logging Utility for Gitko Extension
 * - Structured logging (JSON/plain)
 * - Log levels
 * - Optional per-module output channels
 * - Optional file sink
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
exports.Logger = exports.LogLevel = void 0;
exports.createLogger = createLogger;
// Avoid hard dependency on VS Code API during unit tests.
// Try to require 'vscode' at runtime; fall back to console-based channel if unavailable.
let vscodeApi = undefined;
try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    vscodeApi = require('vscode');
}
catch {
    vscodeApi = undefined;
}
const fs = __importStar(require("fs"));
const os = __importStar(require("os"));
const path = __importStar(require("path"));
var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["DEBUG"] = 0] = "DEBUG";
    LogLevel[LogLevel["INFO"] = 1] = "INFO";
    LogLevel[LogLevel["WARN"] = 2] = "WARN";
    LogLevel[LogLevel["ERROR"] = 3] = "ERROR";
})(LogLevel || (exports.LogLevel = LogLevel = {}));
function createOutputChannel(name) {
    if (vscodeApi && vscodeApi.window && typeof vscodeApi.window.createOutputChannel === 'function') {
        return vscodeApi.window.createOutputChannel(name);
    }
    // Fallback: console-backed output channel for tests
    return {
        appendLine: (v) => console.log(`[${name}] ${v}`),
        show: () => { },
        dispose: () => { },
    };
}
class Logger {
    constructor() {
        this.channels = new Map();
        this.defaultChannelName = 'Gitko Extension';
        this.options = this.loadOptionsFromConfig();
        // Create default channel
        this.getChannel(this.defaultChannelName);
    }
    static getInstance() {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }
    /** Reload options from settings */
    reloadConfig() {
        this.options = this.loadOptionsFromConfig();
    }
    loadOptionsFromConfig() {
        if (vscodeApi?.workspace?.getConfiguration) {
            const cfg = vscodeApi.workspace.getConfiguration('gitko');
            const levelStr = (cfg.get('logLevel', 'info') || 'info').toLowerCase();
            const levelMap = {
                debug: LogLevel.DEBUG,
                info: LogLevel.INFO,
                warn: LogLevel.WARN,
                error: LogLevel.ERROR,
            };
            const level = levelMap[levelStr] ?? LogLevel.INFO;
            const format = cfg.get('logFormat', 'plain') || 'plain';
            const separateChannels = cfg.get('separateOutputChannels', false) ?? false;
            const logToFile = cfg.get('logToFile', false) ?? false;
            const logFilePath = cfg.get('logFilePath', path.join(os.homedir(), 'gitko-agent.log')) ||
                path.join(os.homedir(), 'gitko-agent.log');
            return { level, format, separateChannels, logToFile, logFilePath };
        }
        // Defaults for test environment
        return {
            level: LogLevel.INFO,
            format: 'plain',
            separateChannels: false,
            logToFile: false,
            logFilePath: path.join(os.homedir(), 'gitko-agent.log'),
        };
    }
    setLogLevel(level) {
        this.options.level = level;
    }
    debug(message, source, metadata) {
        if (this.options.level <= LogLevel.DEBUG) {
            this.write('DEBUG', message, source, metadata);
        }
    }
    info(message, source, metadata) {
        if (this.options.level <= LogLevel.INFO) {
            this.write('INFO', message, source, metadata);
        }
    }
    warn(message, source, metadata) {
        if (this.options.level <= LogLevel.WARN) {
            this.write('WARN', message, source, metadata);
        }
    }
    error(message, error, source, metadata) {
        if (this.options.level <= LogLevel.ERROR) {
            const errorMsg = error instanceof Error ? error.message : error ? String(error) : undefined;
            const meta = { ...(metadata || {}), error: errorMsg };
            this.write('ERROR', message, source, meta);
        }
    }
    getChannel(name) {
        if (!this.channels.has(name)) {
            this.channels.set(name, createOutputChannel(name));
        }
        return this.channels.get(name);
    }
    getTargetChannel(module) {
        if (this.options.separateChannels && module) {
            return this.getChannel(`Gitko: ${module}`);
        }
        return this.getChannel(this.defaultChannelName);
    }
    write(level, message, source, metadata) {
        const timestamp = new Date().toISOString();
        let line;
        if (this.options.format === 'json') {
            const payload = {
                ts: timestamp,
                level,
                module: source || 'core',
                msg: message,
            };
            if (metadata && Object.keys(metadata).length > 0) {
                payload.meta = metadata;
            }
            try {
                line = JSON.stringify(payload);
            }
            catch {
                line = JSON.stringify({ ts: timestamp, level, module: source || 'core', msg: String(message) });
            }
        }
        else {
            const sourceTag = source ? `[${source}]` : '';
            line = `[${timestamp}] [${level}]${sourceTag} ${message}`;
        }
        // Output channel
        const channel = this.getTargetChannel(source);
        channel.appendLine(line);
        // Optional file sink
        if (this.options.logToFile && this.options.logFilePath) {
            try {
                fs.appendFile(this.options.logFilePath, line + os.EOL, () => { });
            }
            catch {
                // ignore file errors to avoid crashing logging
            }
        }
    }
    show(module) {
        this.getTargetChannel(module).show();
    }
    dispose() {
        for (const ch of this.channels.values()) {
            ch.dispose();
        }
        this.channels.clear();
    }
}
exports.Logger = Logger;
/**
 * Create a scoped logger for a specific module
 */
function createLogger(moduleName) {
    const logger = Logger.getInstance();
    return {
        debug: (msg, meta) => logger.debug(msg, moduleName, meta),
        info: (msg, meta) => logger.info(msg, moduleName, meta),
        warn: (msg, meta) => logger.warn(msg, moduleName, meta),
        error: (msg, err, meta) => logger.error(msg, err, moduleName, meta),
    };
}
//# sourceMappingURL=logger.js.map