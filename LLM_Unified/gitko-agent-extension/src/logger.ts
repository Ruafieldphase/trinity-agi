/**
 * Unified Logging Utility for Gitko Extension
 * - Structured logging (JSON/plain)
 * - Log levels
 * - Optional per-module output channels
 * - Optional file sink
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3,
}

type LogFormat = 'plain' | 'json';

interface LoggerOptions {
    level: LogLevel;
    format: LogFormat;
    separateChannels: boolean;
    logToFile: boolean;
    logFilePath: string;
}

export class Logger {
    private static instance: Logger;
    private channels: Map<string, vscode.OutputChannel> = new Map();
    private defaultChannelName = 'Gitko Extension';
    private options: LoggerOptions;

    private constructor() {
        this.options = this.loadOptionsFromConfig();
        // Create default channel
        this.getChannel(this.defaultChannelName);
    }

    static getInstance(): Logger {
        if (!Logger.instance) {
            Logger.instance = new Logger();
        }
        return Logger.instance;
    }

    /** Reload options from settings */
    public reloadConfig(): void {
        this.options = this.loadOptionsFromConfig();
    }

    private loadOptionsFromConfig(): LoggerOptions {
        const cfg = vscode.workspace.getConfiguration('gitko');
        const levelStr = (cfg.get<string>('logLevel', 'info') || 'info').toLowerCase();
        const levelMap: Record<string, LogLevel> = { debug: LogLevel.DEBUG, info: LogLevel.INFO, warn: LogLevel.WARN, error: LogLevel.ERROR };
        const level = levelMap[levelStr] ?? LogLevel.INFO;
        const format = (cfg.get<string>('logFormat', 'plain') as LogFormat) || 'plain';
        const separateChannels = cfg.get<boolean>('separateOutputChannels', false) ?? false;
        const logToFile = cfg.get<boolean>('logToFile', false) ?? false;
        const logFilePath = cfg.get<string>('logFilePath', path.join(os.homedir(), 'gitko-agent.log')) || path.join(os.homedir(), 'gitko-agent.log');
        return { level, format, separateChannels, logToFile, logFilePath };
    }

    public setLogLevel(level: LogLevel) {
        this.options.level = level;
    }

    public debug(message: string, source?: string, metadata?: Record<string, unknown>) {
        if (this.options.level <= LogLevel.DEBUG) {
            this.write('DEBUG', message, source, metadata);
        }
    }

    public info(message: string, source?: string, metadata?: Record<string, unknown>) {
        if (this.options.level <= LogLevel.INFO) {
            this.write('INFO', message, source, metadata);
        }
    }

    public warn(message: string, source?: string, metadata?: Record<string, unknown>) {
        if (this.options.level <= LogLevel.WARN) {
            this.write('WARN', message, source, metadata);
        }
    }

    public error(message: string, error?: Error | unknown, source?: string, metadata?: Record<string, unknown>) {
        if (this.options.level <= LogLevel.ERROR) {
            const errorMsg = error instanceof Error ? error.message : error ? String(error) : undefined;
            const meta = { ...(metadata || {}), error: errorMsg };
            this.write('ERROR', message, source, meta);
        }
    }

    private getChannel(name: string): vscode.OutputChannel {
        if (!this.channels.has(name)) {
            this.channels.set(name, vscode.window.createOutputChannel(name));
        }
        return this.channels.get(name)!;
    }

    private getTargetChannel(module?: string): vscode.OutputChannel {
        if (this.options.separateChannels && module) {
            return this.getChannel(`Gitko: ${module}`);
        }
        return this.getChannel(this.defaultChannelName);
    }

    private write(level: string, message: string, source?: string, metadata?: Record<string, unknown>) {
        const timestamp = new Date().toISOString();

        let line: string;
        if (this.options.format === 'json') {
            const payload: Record<string, unknown> = {
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
            } catch {
                line = JSON.stringify({ ts: timestamp, level, module: source || 'core', msg: String(message) });
            }
        } else {
            const sourceTag = source ? `[${source}]` : '';
            line = `[${timestamp}] [${level}]${sourceTag} ${message}`;
        }

        // Output channel
        const channel = this.getTargetChannel(source);
        channel.appendLine(line);

        // Optional file sink
        if (this.options.logToFile && this.options.logFilePath) {
            try {
                fs.appendFile(this.options.logFilePath, line + os.EOL, () => {});
            } catch {
                // ignore file errors to avoid crashing logging
            }
        }
    }

    public show(module?: string) {
        this.getTargetChannel(module).show();
    }

    public dispose() {
        for (const ch of this.channels.values()) {
            ch.dispose();
        }
        this.channels.clear();
    }
}

/**
 * Create a scoped logger for a specific module
 */
export function createLogger(moduleName: string): {
    debug: (msg: string, meta?: Record<string, unknown>) => void;
    info: (msg: string, meta?: Record<string, unknown>) => void;
    warn: (msg: string, meta?: Record<string, unknown>) => void;
    error: (msg: string, err?: Error | unknown, meta?: Record<string, unknown>) => void;
} {
    const logger = Logger.getInstance();
    return {
        debug: (msg: string, meta?: Record<string, unknown>) => logger.debug(msg, moduleName, meta),
        info: (msg: string, meta?: Record<string, unknown>) => logger.info(msg, moduleName, meta),
        warn: (msg: string, meta?: Record<string, unknown>) => logger.warn(msg, moduleName, meta),
        error: (msg: string, err?: Error | unknown, meta?: Record<string, unknown>) =>
            logger.error(msg, err, moduleName, meta),
    };
}
