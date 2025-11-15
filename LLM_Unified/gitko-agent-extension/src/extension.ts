import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { registerComputerUseCommands } from './computerUse';
import { HttpTaskPoller } from './httpTaskPoller';
import { TaskQueueMonitor } from './taskQueueMonitor';
import { ResonanceLedgerViewer } from './resonanceLedgerViewer';
import { ConfigValidator } from './configValidator';
import { createLogger } from './logger';
import { PerformanceViewer } from './performanceViewer';
import { registerIntegrationTestCommand } from './integrationTest';
import { registerDevCommands } from './devUtils';
import { ActivityTracker, ActivityViewer } from './activityTracker';
import { StatusBarManager } from './statusBarManager';

const logger = createLogger('Extension');

interface AgentResult {
    agent: string;
    status: string;
    summary: string;
    output?: string;
    error?: string;
}

// HTTP Poller 상태 관리
let httpPollerInterval: NodeJS.Timeout | undefined; // legacy (unused after poller refactor)
let httpPollerOutputChannel: vscode.OutputChannel | undefined;
let taskPoller: HttpTaskPoller | undefined;
let agentOutputChannel: vscode.OutputChannel | undefined;
let statusBarManager: StatusBarManager | undefined;

interface AgentRuntimeConfig {
    pythonPath: string;
    scriptPath: string;
    workingDirectory: string;
    timeoutMs: number;
    enableLogging: boolean;
}

const MAX_TOOL_RESPONSE_CHARS = 3200; // Keep Copilot payloads below ~3.5k clipboard-safe limit
let cachedRuntimeConfig: AgentRuntimeConfig | null = null;
let runtimeConfigWarningShown = false;

export function activate(context: vscode.ExtensionContext) {
    logger.info('Gitko Agent Extension is now active!');

    // Activity Tracker 초기화
    const activityTracker = ActivityTracker.getInstance();
    activityTracker.trackSystemEvent('extension_activated', {
        version: context.extension.packageJSON.version,
        mode: context.extensionMode,
    });

    // Status Bar Manager 생성
    statusBarManager = new StatusBarManager(vscode.StatusBarAlignment.Right, 100);
    statusBarManager.setState('stopped');
    statusBarManager.setToggleCallback(() => {
        if (taskPoller?.isActive()) {
            disableHttpPoller();
        } else {
            enableHttpPoller();
        }
    });
    context.subscriptions.push(statusBarManager);

    // 설정 검증
    const validationResult = ConfigValidator.validateAll();
    if (!validationResult.isValid) {
        ConfigValidator.showValidationResults(validationResult);
    } else if (validationResult.warnings.length > 0) {
        logger.warn(`Configuration has ${validationResult.warnings.length} warnings`);
    }

    // 설정 검증 명령어 등록
    const validateConfigCmd = vscode.commands.registerCommand('gitko.validateConfig', () => {
        ConfigValidator.validateAndFix();
    });
    context.subscriptions.push(validateConfigCmd);

    // Integration Test 명령어 등록
    registerIntegrationTestCommand(context);

    // Development Utilities 명령어 등록 (개발 모드에서만)
    if (process.env.VSCODE_DEBUG_MODE || context.extensionMode === vscode.ExtensionMode.Development) {
        registerDevCommands(context);
        logger.debug('Dev utilities enabled');
    }

    // 🤖 Computer Use 기능 등록
    registerComputerUseCommands(context);

    // HTTP Poller Output Channel 생성
    httpPollerOutputChannel = vscode.window.createOutputChannel('Gitko HTTP Poller');
    context.subscriptions.push(httpPollerOutputChannel);
    agentOutputChannel = vscode.window.createOutputChannel('Gitko Agent Runtime');
    context.subscriptions.push(agentOutputChannel);

    // HTTP Poller 명령어 등록
    const toggleHttpPollerCmd = vscode.commands.registerCommand('gitko.toggleHttpPoller', () => {
        statusBarManager?.handleToggle();
    });

    const enableHttpPollerCmd = vscode.commands.registerCommand('gitko.enableHttpPoller', () => {
        enableHttpPoller();
    });

    const disableHttpPollerCmd = vscode.commands.registerCommand('gitko.disableHttpPoller', () => {
        disableHttpPoller();
    });

    const showPollerOutputCmd = vscode.commands.registerCommand('gitko.showPollerOutput', () => {
        httpPollerOutputChannel?.show();
    });

    // 🎯 Task Queue Monitor 명령어 등록
    const showTaskQueueMonitorCmd = vscode.commands.registerCommand('gitko.showTaskQueueMonitor', () => {
        const serverUrl = vscode.workspace
            .getConfiguration('gitko')
            .get<string>('taskQueueUrl', 'http://127.0.0.1:8091');
        TaskQueueMonitor.createOrShow(context.extensionUri, serverUrl);
    });

    // 🌊 Resonance Ledger Viewer 명령어 등록
    const showResonanceLedgerCmd = vscode.commands.registerCommand('gitko.showResonanceLedger', () => {
        ResonanceLedgerViewer.createOrShow(context.extensionUri);
    });

    // 📊 Performance Viewer 명령어 등록
    const showPerformanceViewerCmd = vscode.commands.registerCommand('gitko.showPerformanceViewer', () => {
        ActivityTracker.getInstance().trackCommand('gitko.showPerformanceViewer');
        PerformanceViewer.createOrShow(context.extensionUri);
    });

    // 📈 Activity Viewer 명령어 등록
    const activityViewer = new ActivityViewer();
    const showActivityViewerCmd = vscode.commands.registerCommand('gitko.showActivityViewer', () => {
        ActivityTracker.getInstance().trackCommand('gitko.showActivityViewer');
        activityViewer.show(context);
    });

    context.subscriptions.push(
        toggleHttpPollerCmd,
        enableHttpPollerCmd,
        disableHttpPollerCmd,
        showPollerOutputCmd,
        showTaskQueueMonitorCmd,
        showResonanceLedgerCmd,
        showPerformanceViewerCmd,
        showActivityViewerCmd
    );

    const configWatcher = vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('gitkoAgent')) {
            resetRuntimeConfigCache();
            logGitko('gitkoAgent 설정 변경 감지: 런타임 구성을 초기화했습니다.', undefined, true);
        }
    });
    context.subscriptions.push(configWatcher);

    // 🚀 HTTP Poller 자동 시작 (설정 기반)
    // gitko.enableHttpPoller=true일 때만 자동 시작 (기본값 true)
    const gitkoCfg = vscode.workspace.getConfiguration('gitko');
    const shouldAutostart = gitkoCfg.get<boolean>('enableHttpPoller', true);
    if (shouldAutostart) {
        enableHttpPoller();
        logger.info('HTTP Poller auto-started');
    } else {
        httpPollerOutputChannel?.appendLine(
            `[${new Date().toISOString()}] HTTP Task Poller autostart is disabled by settings (gitko.enableHttpPoller=false)`
        );
    }

    // Language Model Tools 등록 (Copilot이 자동으로 호출)
    const sianTool = vscode.lm.registerTool('sian_refactor', {
        invoke: async (
            options: vscode.LanguageModelToolInvocationOptions<{ message: string }>,
            token: vscode.CancellationToken
        ) => {
            const result = await executeAgent('sian', options.input.message, token);
            return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(result)]);
        },
    });

    const lubitTool = vscode.lm.registerTool('lubit_review', {
        invoke: async (
            options: vscode.LanguageModelToolInvocationOptions<{ message: string }>,
            token: vscode.CancellationToken
        ) => {
            const result = await executeAgent('lubit', options.input.message, token);
            return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(result)]);
        },
    });

    const gitkoTool = vscode.lm.registerTool('gitko_orchestrate', {
        invoke: async (
            options: vscode.LanguageModelToolInvocationOptions<{ message: string }>,
            token: vscode.CancellationToken
        ) => {
            const result = await executeAgent('gitko', options.input.message, token);
            return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(result)]);
        },
    });

    // Chat Participant도 유지 (명시적 호출용)
    const gitko = vscode.chat.createChatParticipant(
        'gitko-agent',
        async (
            request: vscode.ChatRequest,
            context: vscode.ChatContext,
            stream: vscode.ChatResponseStream,
            token: vscode.CancellationToken
        ) => {
            // 슬래시 커맨드 처리
            if (request.command === 'help') {
                stream.markdown(`# 🎯 Gitko AI Agent 도움말\n\n`);
                stream.markdown(`## 사용 가능한 명령어\n\n`);
                stream.markdown(`- \`/review\` - 코드 리뷰 (Lubit Agent)\n`);
                stream.markdown(`- \`/improve\` - 코드 개선 (Sian Agent)\n`);
                stream.markdown(`- \`/parallel\` - 병렬 실행 (모든 에이전트)\n`);
                stream.markdown(`- \`/check\` - 환경 설정 확인\n\n`);

                stream.markdown(`## Python 환경\n\n`);
                const pythonPath = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
                stream.markdown(`- **Python 경로**: \`${pythonPath}\`\n`);
                stream.markdown(`- **스크립트**: \`D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py\`\n\n`);

                stream.markdown(`## 사용 방법\n\n`);
                stream.markdown(`1. \`@gitko /review\` - 현재 코드를 리뷰합니다\n`);
                stream.markdown(`2. \`@gitko /improve 함수명 개선\` - 특정 함수를 개선합니다\n`);
                stream.markdown(`3. \`@gitko 코드 리팩토링 해줘\` - 일반 대화로 요청합니다\n\n`);

                return { metadata: { command: 'help' } };
            }

            if (request.command === 'check') {
                stream.markdown(`# 🔍 환경 설정 확인\n\n`);
                const pythonPath = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
                const scriptPath = 'D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py';

                const pythonExists = fs.existsSync(pythonPath);
                const scriptExists = fs.existsSync(scriptPath);

                stream.markdown(`## Python 환경\n\n`);
                stream.markdown(`- Python: ${pythonExists ? '✅' : '❌'} \`${pythonPath}\`\n`);
                stream.markdown(`- Script: ${scriptExists ? '✅' : '❌'} \`${scriptPath}\`\n\n`);

                if (!pythonExists || !scriptExists) {
                    stream.markdown(`⚠️ **설정 필요**: Settings에서 경로를 확인하세요.\n\n`);
                }

                return { metadata: { command: 'check' } };
            }

            if (request.command === 'review') {
                stream.markdown(`# 🛡️ Lubit 코드 리뷰\n\n`);
                stream.markdown(`📝 요청: "${request.prompt || '현재 코드 리뷰'}"\n\n`);
                stream.markdown(`🔍 Lubit이 코드를 분석 중입니다...\n\n`);

                try {
                    const result = await executeGitkoAgent(request.prompt || 'review', stream, token);

                    if (result.status === 'success') {
                        stream.markdown(`\n---\n\n## ✅ 리뷰 완료\n\n`);
                        if (result.output) {
                            stream.markdown(`\`\`\`\n${result.output}\n\`\`\`\n\n`);
                        }
                        if (result.summary) {
                            stream.markdown(`**요약**: ${result.summary}\n\n`);
                        }
                    } else {
                        stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                    }
                } catch (error) {
                    stream.markdown(`\n❌ 실행 오류: ${error instanceof Error ? error.message : String(error)}\n\n`);
                }

                return { metadata: { command: 'review' } };
            }

            if (request.command === 'improve') {
                stream.markdown(`# 🔧 Sian 코드 개선\n\n`);
                stream.markdown(`📝 요청: "${request.prompt || '코드 개선'}"\n\n`);
                stream.markdown(`🔍 Sian이 개선 방안을 분석 중입니다...\n\n`);

                try {
                    const result = await executeGitkoAgent(request.prompt || 'improve', stream, token);

                    if (result.status === 'success') {
                        stream.markdown(`\n---\n\n## ✅ 개선 완료\n\n`);
                        if (result.output) {
                            stream.markdown(`\`\`\`\n${result.output}\n\`\`\`\n\n`);
                        }
                        if (result.summary) {
                            stream.markdown(`**요약**: ${result.summary}\n\n`);
                        }
                    } else {
                        stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                    }
                } catch (error) {
                    stream.markdown(`\n❌ 실행 오류: ${error instanceof Error ? error.message : String(error)}\n\n`);
                }

                return { metadata: { command: 'improve' } };
            }

            if (request.command === 'parallel') {
                stream.markdown(`# 🎭 병렬 실행 (모든 에이전트)\n\n`);
                stream.markdown(`📝 요청: "${request.prompt || '병렬 분석'}"\n\n`);
                stream.markdown(`🔍 Sian, Lubit, Gitko가 동시에 분석 중입니다...\n\n`);

                try {
                    const result = await executeGitkoAgent(request.prompt || 'parallel', stream, token);

                    if (result.status === 'success') {
                        stream.markdown(`\n---\n\n## ✅ 병렬 실행 완료\n\n`);
                        if (result.output) {
                            stream.markdown(`\`\`\`\n${result.output}\n\`\`\`\n\n`);
                        }
                        if (result.summary) {
                            stream.markdown(`**요약**: ${result.summary}\n\n`);
                        }
                    } else {
                        stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                    }
                } catch (error) {
                    stream.markdown(`\n❌ 실행 오류: ${error instanceof Error ? error.message : String(error)}\n\n`);
                }

                return { metadata: { command: 'parallel' } };
            }

            const userMessage = request.prompt;

            // 메시지가 비어있으면 안내 출력
            if (!userMessage || userMessage.trim() === '') {
                stream.markdown(`🤖 **Gitko AI Agent**\n\n`);
                stream.markdown(`💡 메시지를 입력해주세요. 예:\n\n`);
                stream.markdown(`- \`@gitko /help\` - 도움말 보기\n`);
                stream.markdown(`- \`@gitko /review\` - 코드 리뷰\n`);
                stream.markdown(`- \`@gitko 이 함수를 개선해줘\` - 일반 요청\n\n`);
                return { metadata: { command: 'empty' } };
            }

            stream.markdown(`🤖 **Gitko AI Agent**\n\n`);
            stream.markdown(`📝 요청: "${userMessage}"\n\n`);
            stream.markdown(`🔍 작업 분석 중...\n\n`);

            try {
                const result = await executeGitkoAgent(userMessage, stream, token);

                if (result.status === 'success') {
                    stream.markdown(`\n---\n\n`);
                    stream.markdown(`## ✅ 작업 완료\n\n`);
                    stream.markdown(`**에이전트**: ${result.agent}\n\n`);

                    if (result.output) {
                        stream.markdown(`**결과**:\n\`\`\`\n${result.output}\n\`\`\`\n\n`);
                    }

                    if (result.summary) {
                        stream.markdown(`**요약**: ${result.summary}\n\n`);
                    }
                } else {
                    stream.markdown(`\n---\n\n`);
                    stream.markdown(`## ⚠️ 작업 중 오류 발생\n\n`);
                    stream.markdown(`${result.error || '알 수 없는 오류'}\n\n`);
                }
            } catch (error) {
                stream.markdown(`\n---\n\n`);
                stream.markdown(`## ❌ 실행 오류\n\n`);
                stream.markdown(`${error instanceof Error ? error.message : String(error)}\n\n`);
            }

            return { metadata: { command: 'gitko' } };
        }
    );

    gitko.iconPath = vscode.Uri.file(path.join(context.extensionPath, 'resources', 'gitko-icon.png'));

    context.subscriptions.push(gitko, sianTool, lubitTool, gitkoTool);
}

// Tool에서 사용할 에이전트 실행 함수
async function executeAgent(agent: string, message: string, token: vscode.CancellationToken): Promise<string> {
    const runtime = getAgentRuntimeConfig();
    if (!runtime) {
        return 'Gitko Agent 실행 구성이 완료되지 않았습니다. VS Code 설정의 gitkoAgent.pythonPath/scriptPath를 확인하세요.';
    }

    return new Promise((resolve, reject) => {
        const args = [runtime.scriptPath, `--agent=${agent}`, message];
        logGitko(`Launching gitko_cli.py (tool:${agent})`, runtime);
        const proc = spawn(runtime.pythonPath, args, {
            cwd: runtime.workingDirectory,
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
            },
            windowsHide: true,
        });

        let stdout = '';
        let stderr = '';
        let cancelled = false;
        let timedOut = false;

        const timeoutHandle = setTimeout(() => {
            timedOut = true;
            proc.kill();
        }, runtime.timeoutMs);

        proc.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        proc.on('error', (error) => {
            clearTimeout(timeoutHandle);
            reject(error);
        });

        proc.on('close', (code) => {
            clearTimeout(timeoutHandle);
            if (cancelled || token.isCancellationRequested) {
                reject(new Error('작업이 취소되었습니다.'));
                return;
            }
            if (timedOut) {
                reject(new Error(`Gitko Agent 실행이 ${Math.round(runtime.timeoutMs / 1000)}초 제한을 초과했습니다.`));
                return;
            }

            if (code === 0) {
                const safeOutput = sanitizeToolOutput(stdout, agent);
                logGitko(`[tool:${agent}] stdout ${stdout.length}자 → ${safeOutput.length}자 반환`, runtime);
                if (stderr.trim()) {
                    logGitko(`[tool:${agent}] stderr: ${stderr.trim()}`, runtime);
                }
                resolve(safeOutput);
            } else {
                reject(new Error((stderr || stdout || 'Gitko Agent 실행 실패').trim()));
            }
        });

        token.onCancellationRequested(() => {
            cancelled = true;
            proc.kill();
        });
    });
}

// Chat Participant용 실행 함수 (기존 유지)

async function executeGitkoAgent(
    message: string,
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken
): Promise<AgentResult> {
    const runtime = getAgentRuntimeConfig();
    if (!runtime) {
        throw new Error('Gitko Agent 실행 구성이 완료되지 않았습니다. VS Code 설정을 확인하세요.');
    }

    return new Promise((resolve, reject) => {
        const proc = spawn(runtime.pythonPath, [runtime.scriptPath, message], {
            cwd: runtime.workingDirectory,
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8',
            },
            windowsHide: true,
        });

        let stdout = '';
        let stderr = '';
        let cancelled = false;
        let timedOut = false;

        const timeoutHandle = setTimeout(() => {
            timedOut = true;
            proc.kill();
        }, runtime.timeoutMs);

        proc.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;

            // 실시간 진행상황 표시
            const lines = text.split('\n').filter((l: string) => l.trim());
            for (const line of lines) {
                if (line.includes('분석 완료') || line.includes('실행 중') || line.includes('대기')) {
                    stream.markdown(`${line}\n\n`);
                }
            }
        });

        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        proc.on('error', (error) => {
            clearTimeout(timeoutHandle);
            reject(error);
        });

        proc.on('close', (code) => {
            clearTimeout(timeoutHandle);
            if (token.isCancellationRequested) {
                reject(new Error('작업이 취소되었습니다.'));
                return;
            }
            if (cancelled) {
                reject(new Error('작업이 취소되었습니다.'));
                return;
            }
            if (timedOut) {
                reject(new Error(`Gitko Agent 실행이 ${Math.round(runtime.timeoutMs / 1000)}초 제한을 초과했습니다.`));
                return;
            }

            if (code === 0) {
                // 출력 파싱
                const result = parseAgentOutput(stdout);
                if (result.output) {
                    const safeOutput = sanitizeToolOutput(result.output, result.agent || 'gitko');
                    if (safeOutput !== result.output) {
                        result.output = safeOutput;
                        if (result.summary) {
                            result.summary += ' (출력 일부만 표시됨)';
                        } else {
                            result.summary = '출력 일부만 표시됨';
                        }
                    }
                }
                logGitko(`[chat] stdout ${stdout.length}자`, runtime);
                if (stderr.trim()) {
                    logGitko(`[chat] stderr: ${stderr.trim()}`, runtime);
                }
                resolve(result);
            } else {
                resolve({
                    agent: 'gitko',
                    status: 'error',
                    summary: '에이전트 실행 실패',
                    error: (stderr || stdout || 'Gitko Agent 실행 실패').trim(),
                });
            }
        });

        proc.on('error', (error) => {
            reject(new Error(`프로세스 실행 오류: ${error.message}`));
        });

        // 취소 처리
        token.onCancellationRequested(() => {
            cancelled = true;
            proc.kill();
        });
    });
}

function parseAgentOutput(output: string): AgentResult {
    try {
        // gitko_cli.py 출력 파싱
        const lines = output.split('\n');

        let agent = 'gitko';
        let summary = '';
        let status = 'success';
        let outputText = '';

        for (const line of lines) {
            if (line.includes('에이전트:')) {
                const match = line.match(/에이전트:\s*(\w+)/);
                if (match) {
                    agent = match[1].toLowerCase();
                }
            }

            if (line.includes('요약:')) {
                summary = line.split('요약:')[1]?.trim() || '';
            }

            if (line.includes('작업 완료') || line.includes('✅')) {
                status = 'success';
            }

            if (line.includes('오류') || line.includes('❌') || line.includes('실패')) {
                status = 'error';
            }
        }

        // 전체 출력을 저장 (디버깅용)
        outputText = output.trim();

        return {
            agent,
            status,
            summary: summary || `${agent} 에이전트 작업 완료`,
            output: outputText,
        };
    } catch (error) {
        return {
            agent: 'gitko',
            status: 'error',
            summary: '출력 파싱 실패',
            error: error instanceof Error ? error.message : String(error),
            output: output,
        };
    }
}

function sanitizeToolOutput(output: string, agent: string): string {
    const trimmed = (output || '').trim();
    if (trimmed.length <= MAX_TOOL_RESPONSE_CHARS) {
        return trimmed;
    }
    const safeText = trimmed.slice(0, MAX_TOOL_RESPONSE_CHARS);
    return `${safeText}\n\n... (${agent} 출력이 ${trimmed.length}자를 초과해 앞부분 ${MAX_TOOL_RESPONSE_CHARS}자만 Copilot에 전달했습니다.)`;
}

function getAgentRuntimeConfig(): AgentRuntimeConfig | undefined {
    if (cachedRuntimeConfig) {
        return cachedRuntimeConfig;
    }
    const resolved = resolveAgentRuntimeConfig();
    if (resolved) {
        cachedRuntimeConfig = resolved;
        logGitko(`Runtime resolved (python: ${resolved.pythonPath}, script: ${resolved.scriptPath})`, resolved);
        return resolved;
    }

    if (!runtimeConfigWarningShown) {
        vscode.window.showWarningMessage(
            'Gitko Agent 실행 파일을 찾지 못했습니다. VS Code 설정 (gitkoAgent.pythonPath/scriptPath)을 확인하세요.'
        );
        runtimeConfigWarningShown = true;
    }
    return undefined;
}

function resetRuntimeConfigCache() {
    cachedRuntimeConfig = null;
    runtimeConfigWarningShown = false;
}

function resolveAgentRuntimeConfig(): AgentRuntimeConfig | undefined {
    const cfg = vscode.workspace.getConfiguration('gitkoAgent');
    const workspaceRoot = getWorkspaceRoot();

    const scriptCandidates: Array<string | undefined> = [
        resolveScriptCandidate(cfg.get<string>('scriptPath'), workspaceRoot),
        resolveScriptCandidate(process.env.GITKO_SCRIPT_PATH, workspaceRoot),
    ];
    if (workspaceRoot) {
        scriptCandidates.push(
            path.join(workspaceRoot, 'LLM_Unified', 'ion-mentoring', 'gitko_cli.py'),
            path.join(workspaceRoot, 'ion-mentoring', 'gitko_cli.py'),
            path.join(workspaceRoot, 'gitko_cli.py')
        );
    }

    const scriptPath = findExistingFile(scriptCandidates);
    if (!scriptPath) {
        return undefined;
    }

    const pythonCandidates: Array<string | undefined> = [
        resolveExecutableCandidate(cfg.get<string>('pythonPath'), workspaceRoot),
        resolveExecutableCandidate(process.env.GITKO_PYTHON_PATH, workspaceRoot),
    ];
    if (workspaceRoot) {
        const win = process.platform === 'win32';
        pythonCandidates.push(
            win
                ? path.join(workspaceRoot, '.venv', 'Scripts', 'python.exe')
                : path.join(workspaceRoot, '.venv', 'bin', 'python'),
            win
                ? path.join(workspaceRoot, 'LLM_Unified', '.venv', 'Scripts', 'python.exe')
                : path.join(workspaceRoot, 'LLM_Unified', '.venv', 'bin', 'python')
        );
    }
    pythonCandidates.push(process.platform === 'win32' ? 'python.exe' : 'python');

    const pythonPath =
        findExistingExecutable(pythonCandidates) ?? (process.platform === 'win32' ? 'python.exe' : 'python');

    const workingDirectory =
        resolveDirectoryCandidate(cfg.get<string>('workingDirectory'), workspaceRoot) || path.dirname(scriptPath);

    const timeout = cfg.get<number>('timeout', 300000) ?? 300000;
    const enableLogging = cfg.get<boolean>('enableLogging', true) ?? true;

    return {
        pythonPath,
        scriptPath,
        workingDirectory,
        timeoutMs: timeout > 0 ? timeout : 300000,
        enableLogging,
    };
}

function resolveScriptCandidate(value: string | undefined, workspaceRoot?: string): string | undefined {
    const expanded = expandPathValue(value, workspaceRoot);
    if (!expanded) {
        return undefined;
    }
    if (path.isAbsolute(expanded)) {
        return expanded;
    }
    if (workspaceRoot) {
        return path.join(workspaceRoot, expanded);
    }
    return path.resolve(expanded);
}

function resolveExecutableCandidate(value: string | undefined, workspaceRoot?: string): string | undefined {
    const expanded = expandPathValue(value, workspaceRoot);
    if (!expanded) {
        return undefined;
    }
    if (expanded.includes('\\') || expanded.includes('/')) {
        if (path.isAbsolute(expanded)) {
            return expanded;
        }
        if (workspaceRoot) {
            return path.join(workspaceRoot, expanded);
        }
        return path.resolve(expanded);
    }
    return expanded;
}

function resolveDirectoryCandidate(value: string | undefined, workspaceRoot?: string): string | undefined {
    const expanded = expandPathValue(value, workspaceRoot);
    if (!expanded) {
        return undefined;
    }
    const absolutePath = path.isAbsolute(expanded)
        ? expanded
        : workspaceRoot
          ? path.join(workspaceRoot, expanded)
          : path.resolve(expanded);
    try {
        if (fs.existsSync(absolutePath) && fs.statSync(absolutePath).isDirectory()) {
            return absolutePath;
        }
    } catch (error) {
        // ignore invalid paths
    }
    return undefined;
}

function expandPathValue(value: string | undefined, workspaceRoot?: string): string | undefined {
    if (!value) {
        return undefined;
    }
    let expanded = value.trim();
    if (!expanded) {
        return undefined;
    }
    if (workspaceRoot) {
        expanded = expanded.replace(/\${workspaceFolder}/gi, workspaceRoot);
    }
    if (expanded.startsWith('~')) {
        expanded = path.join(os.homedir(), expanded.slice(1));
    }
    return expanded;
}

function findExistingFile(candidates: Array<string | undefined>): string | undefined {
    for (const candidate of candidates) {
        if (candidate && fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
            return candidate;
        }
    }
    return undefined;
}

function findExistingExecutable(candidates: Array<string | undefined>): string | undefined {
    for (const candidate of candidates) {
        if (!candidate) {
            continue;
        }
        if (!candidate.includes('\\') && !candidate.includes('/')) {
            return candidate;
        }
        if (fs.existsSync(candidate)) {
            return candidate;
        }
    }
    return undefined;
}

function getWorkspaceRoot(): string | undefined {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function logGitko(message: string, runtime?: AgentRuntimeConfig, force = false) {
    if (!agentOutputChannel) {
        return;
    }
    if (!force && runtime && !runtime.enableLogging) {
        return;
    }
    agentOutputChannel.appendLine(`[${new Date().toISOString()}] ${message}`);
}

// HTTP Poller 함수들
function enableHttpPoller() {
    if (taskPoller && taskPoller.isActive()) {
        vscode.window.showInformationMessage('HTTP Task Poller is already running');
        return;
    }

    // HTTP Poller 설정은 contributes.configuration의 "gitko" 섹션을 따름
    const config = vscode.workspace.getConfiguration('gitko');
    const apiBase = config.get<string>('httpApiBase', 'http://localhost:8091/api');
    const interval = config.get<number>('httpPollingInterval', 2000);

    httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller enabled`);
    httpPollerOutputChannel?.appendLine(`API Base: ${apiBase}`);
    httpPollerOutputChannel?.appendLine(`Polling Interval: ${interval}ms`);
    httpPollerOutputChannel?.show();

    vscode.window.showInformationMessage(`✅ Gitko HTTP Task Poller enabled (${interval}ms interval)`);

    taskPoller = new HttpTaskPoller(apiBase, 'gitko-extension', interval);
    taskPoller.setOutputCallback((msg) => httpPollerOutputChannel?.appendLine(msg));
    taskPoller.start();
    statusBarManager?.setState('polling');
}

function disableHttpPoller() {
    if (taskPoller && taskPoller.isActive()) {
        taskPoller.stop();
        httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller disabled`);
        vscode.window.showInformationMessage('❌ Gitko HTTP Task Poller disabled');
        statusBarManager?.setState('stopped');
        return;
    }

    if (httpPollerInterval) {
        clearInterval(httpPollerInterval);
        httpPollerInterval = undefined;
    }
    httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller disabled`);
    vscode.window.showInformationMessage('❌ Gitko HTTP Task Poller disabled');
    statusBarManager?.setState('stopped');
}

export function deactivate() {
    if (httpPollerInterval) {
        clearInterval(httpPollerInterval);
        httpPollerInterval = undefined;
    }
    logger.info('Gitko Agent Extension is deactivated');
}
