/**
 * Unified Logging Utility for Gitko Extension
 * Provides consistent logging across all modules
 */

import * as vscode from 'vscode';

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}

export class Logger {
    private static instance: Logger;
    private outputChannel: vscode.OutputChannel;
    private logLevel: LogLevel = LogLevel.INFO;

    private constructor(channelName: string) {
        this.outputChannel = vscode.window.createOutputChannel(channelName);
    }

    static getInstance(channelName: string = 'Gitko Extension'): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger(channelName);
        }
        return Logger.instance;
    }

    setLogLevel(level: LogLevel) {
        this.logLevel = level;
    }

    debug(message: string, source?: string) {
        if (this.logLevel <= LogLevel.DEBUG) {
            this.write('DEBUG', message, source);
        }
    }

    info(message: string, source?: string) {
        if (this.logLevel <= LogLevel.INFO) {
            this.write('INFO', message, source);
        }
    }

    warn(message: string, source?: string) {
        if (this.logLevel <= LogLevel.WARN) {
            this.write('WARN', message, source);
        }
    }

    error(message: string, error?: Error | unknown, source?: string) {
        if (this.logLevel <= LogLevel.ERROR) {
            const errorMsg = error instanceof Error ? error.message : String(error || '');
            const fullMessage = errorMsg ? `${message}: ${errorMsg}` : message;
            this.write('ERROR', fullMessage, source);
        }
    }

    private write(level: string, message: string, source?: string) {
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

/**
 * Create a scoped logger for a specific module
 */
export function createLogger(moduleName: string): {
    debug: (msg: string) => void;
    info: (msg: string) => void;
    warn: (msg: string) => void;
    error: (msg: string, err?: Error | unknown) => void;
} {
    const logger = Logger.getInstance();
    return {
        debug: (msg: string) => logger.debug(msg, moduleName),
        info: (msg: string) => logger.info(msg, moduleName),
        warn: (msg: string) => logger.warn(msg, moduleName),
        error: (msg: string, err?: Error | unknown) => logger.error(msg, err, moduleName)
    };
}
