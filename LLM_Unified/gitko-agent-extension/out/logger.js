"use strict";
/**
 * Unified Logging Utility for Gitko Extension
 * Provides consistent logging across all modules
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
const vscode = __importStar(require("vscode"));
var LogLevel;
(function (LogLevel) {
    LogLevel[LogLevel["DEBUG"] = 0] = "DEBUG";
    LogLevel[LogLevel["INFO"] = 1] = "INFO";
    LogLevel[LogLevel["WARN"] = 2] = "WARN";
    LogLevel[LogLevel["ERROR"] = 3] = "ERROR";
})(LogLevel || (exports.LogLevel = LogLevel = {}));
class Logger {
    constructor(channelName) {
        this.logLevel = LogLevel.INFO;
        this.outputChannel = vscode.window.createOutputChannel(channelName);
    }
    static getInstance(channelName = 'Gitko Extension') {
        if (!Logger.instance) {
            Logger.instance = new Logger(channelName);
        }
        return Logger.instance;
    }
    setLogLevel(level) {
        this.logLevel = level;
    }
    debug(message, source) {
        if (this.logLevel <= LogLevel.DEBUG) {
            this.write('DEBUG', message, source);
        }
    }
    info(message, source) {
        if (this.logLevel <= LogLevel.INFO) {
            this.write('INFO', message, source);
        }
    }
    warn(message, source) {
        if (this.logLevel <= LogLevel.WARN) {
            this.write('WARN', message, source);
        }
    }
    error(message, error, source) {
        if (this.logLevel <= LogLevel.ERROR) {
            const errorMsg = error instanceof Error ? error.message : String(error || '');
            const fullMessage = errorMsg ? `${message}: ${errorMsg}` : message;
            this.write('ERROR', fullMessage, source);
        }
    }
    write(level, message, source) {
        const timestamp = new Date().toISOString();
        const sourceTag = source ? `[${source}]` : '';
        const logMessage = `[${timestamp}] [${level}]${sourceTag} ${message}`;
        this.outputChannel.appendLine(logMessage);
    }
    show() {
        this.outputChannel.show();
    }
    dispose() {
        this.outputChannel.dispose();
    }
}
exports.Logger = Logger;
/**
 * Create a scoped logger for a specific module
 */
function createLogger(moduleName) {
    const logger = Logger.getInstance();
    return {
        debug: (msg) => logger.debug(msg, moduleName),
        info: (msg) => logger.info(msg, moduleName),
        warn: (msg) => logger.warn(msg, moduleName),
        error: (msg, err) => logger.error(msg, err, moduleName)
    };
}
//# sourceMappingURL=logger.js.map