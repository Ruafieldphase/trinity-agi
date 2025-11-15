/**
 * Unified Logging Utility for Gitko Extension
 * - Structured logging (JSON/plain)
 * - Log levels
 * - Optional per-module output channels
 * - Optional file sink
 */

// Avoid hard dependency on VS Code API during unit tests.
// Try to require 'vscode' at runtime; fall back to console-based channel if unavailable.
let vscodeApi: any = undefined;
try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    vscodeApi = require('vscode');
} catch {
    vscodeApi = undefined;
}
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
    redactSensitive: boolean;
}

interface OutputChannelLike {
    appendLine(value: string): void;
    show(): void;
    dispose(): void;
}

function createOutputChannel(name: string): OutputChannelLike {
    if (vscodeApi && vscodeApi.window && typeof vscodeApi.window.createOutputChannel === 'function') {
        return vscodeApi.window.createOutputChannel(name);
    }
    // Fallback: console-backed output channel for tests
    return {
        appendLine: (v: string) => console.log(`[${name}] ${v}`),
        show: () => {},
        dispose: () => {},
    } as OutputChannelLike;
}

export class Logger {
    private static instance: Logger;
    private channels: Map<string, OutputChannelLike> = new Map();
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
        if (vscodeApi?.workspace?.getConfiguration) {
            const cfg = vscodeApi.workspace.getConfiguration('gitko');
            const levelStr = (cfg.get('logLevel', 'info') || 'info').toLowerCase();
            const levelMap: Record<string, LogLevel> = {
                debug: LogLevel.DEBUG,
                info: LogLevel.INFO,
                warn: LogLevel.WARN,
                error: LogLevel.ERROR,
            };
            const level = levelMap[levelStr] ?? LogLevel.INFO;
            const format = ((cfg.get('logFormat', 'plain') as string) as LogFormat) || 'plain';
            const separateChannels = (cfg.get('separateOutputChannels', false) as boolean) ?? false;
            const logToFile = (cfg.get('logToFile', false) as boolean) ?? false;
            const logFilePath =
                (cfg.get('logFilePath', path.join(os.homedir(), 'gitko-agent.log')) as string) ||
                path.join(os.homedir(), 'gitko-agent.log');
            const redactSensitive = (cfg.get('security.redact.enabled', true) as boolean) ?? true;
            return { level, format, separateChannels, logToFile, logFilePath, redactSensitive };
        }
        // Defaults for test environment
        return {
            level: LogLevel.INFO,
            format: 'plain',
            separateChannels: false,
            logToFile: false,
            logFilePath: path.join(os.homedir(), 'gitko-agent.log'),
            redactSensitive: true,
        };
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

    private getChannel(name: string): OutputChannelLike {
        if (!this.channels.has(name)) {
            this.channels.set(name, createOutputChannel(name));
        }
        return this.channels.get(name)!;
    }

    private getTargetChannel(module?: string): OutputChannelLike {
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

        // Redact sensitive content if enabled
        if (this.options.redactSensitive) {
            line = this.redact(line);
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

    private redact(text: string): string {
        try {
            // Email addresses
            text = text.replace(/([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[A-Za-z]{2,})/g, '[REDACTED:email]');
            // Bearer tokens
            text = text.replace(/Bearer\s+[A-Za-z0-9._\-]+/gi, 'Bearer [REDACTED:token]');
            // API keys common patterns
            text = text.replace(/(api[-_ ]?key\s*[:=]\s*)["']?[A-Za-z0-9_\-]{8,}["']?/gi, '$1[REDACTED:key]');
            // Secret-like hex/base64 strings following key/secret/password labels
            text = text.replace(/(secret|password|token)\s*[:=]\s*["']?[A-Za-z0-9+/=]{8,}["']?/gi, '$1:[REDACTED]');
        } catch {
            // best-effort
        }
        return text;
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
