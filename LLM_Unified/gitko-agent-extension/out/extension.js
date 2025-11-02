"use strict";
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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const computerUse_1 = require("./computerUse");
const httpTaskPoller_1 = require("./httpTaskPoller");
const taskQueueMonitor_1 = require("./taskQueueMonitor");
const resonanceLedgerViewer_1 = require("./resonanceLedgerViewer");
// HTTP Poller 상태 관리
let httpPollerInterval; // legacy (unused after poller refactor)
let httpPollerOutputChannel;
let taskPoller;
function activate(context) {
    console.log('Gitko Agent Extension is now active!');
    // 🤖 Computer Use 기능 등록
    (0, computerUse_1.registerComputerUseCommands)(context);
    // HTTP Poller Output Channel 생성
    httpPollerOutputChannel = vscode.window.createOutputChannel('Gitko HTTP Poller');
    context.subscriptions.push(httpPollerOutputChannel);
    // HTTP Poller 명령어 등록
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
        const serverUrl = vscode.workspace.getConfiguration('gitko').get('taskQueueUrl', 'http://127.0.0.1:8091');
        taskQueueMonitor_1.TaskQueueMonitor.createOrShow(context.extensionUri, serverUrl);
    });
    // 🌊 Resonance Ledger Viewer 명령어 등록
    const showResonanceLedgerCmd = vscode.commands.registerCommand('gitko.showResonanceLedger', () => {
        resonanceLedgerViewer_1.ResonanceLedgerViewer.createOrShow(context.extensionUri);
    });
    context.subscriptions.push(enableHttpPollerCmd, disableHttpPollerCmd, showPollerOutputCmd, showTaskQueueMonitorCmd, showResonanceLedgerCmd);
    // 🚀 HTTP Poller 자동 시작 (설정 기반)
    // gitko.enableHttpPoller=true일 때만 자동 시작 (기본값 true)
    const gitkoCfg = vscode.workspace.getConfiguration('gitko');
    const shouldAutostart = gitkoCfg.get('enableHttpPoller', true);
    if (shouldAutostart) {
        enableHttpPoller();
        vscode.window.showInformationMessage('🤖 Gitko Agent Extension 활성화! HTTP Poller 자동 시작됨');
    }
    else {
        httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller autostart is disabled by settings (gitko.enableHttpPoller=false)`);
    }
    // Language Model Tools 등록 (Copilot이 자동으로 호출)
    const sianTool = vscode.lm.registerTool('sian_refactor', {
        invoke: async (options, token) => {
            const result = await executeAgent('sian', options.input.message, token);
            return new vscode.LanguageModelToolResult([
                new vscode.LanguageModelTextPart(result)
            ]);
        }
    });
    const lubitTool = vscode.lm.registerTool('lubit_review', {
        invoke: async (options, token) => {
            const result = await executeAgent('lubit', options.input.message, token);
            return new vscode.LanguageModelToolResult([
                new vscode.LanguageModelTextPart(result)
            ]);
        }
    });
    const gitkoTool = vscode.lm.registerTool('gitko_orchestrate', {
        invoke: async (options, token) => {
            const result = await executeAgent('gitko', options.input.message, token);
            return new vscode.LanguageModelToolResult([
                new vscode.LanguageModelTextPart(result)
            ]);
        }
    });
    // Chat Participant도 유지 (명시적 호출용)
    const gitko = vscode.chat.createChatParticipant('gitko-agent', async (request, context, stream, token) => {
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
            const fs = require('fs');
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
                }
                else {
                    stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                }
            }
            catch (error) {
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
                }
                else {
                    stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                }
            }
            catch (error) {
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
                }
                else {
                    stream.markdown(`\n⚠️ 오류: ${result.error}\n\n`);
                }
            }
            catch (error) {
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
            }
            else {
                stream.markdown(`\n---\n\n`);
                stream.markdown(`## ⚠️ 작업 중 오류 발생\n\n`);
                stream.markdown(`${result.error || '알 수 없는 오류'}\n\n`);
            }
        }
        catch (error) {
            stream.markdown(`\n---\n\n`);
            stream.markdown(`## ❌ 실행 오류\n\n`);
            stream.markdown(`${error instanceof Error ? error.message : String(error)}\n\n`);
        }
        return { metadata: { command: 'gitko' } };
    });
    gitko.iconPath = vscode.Uri.file(path.join(context.extensionPath, 'resources', 'gitko-icon.png'));
    context.subscriptions.push(gitko, sianTool, lubitTool, gitkoTool);
}
// Tool에서 사용할 에이전트 실행 함수
async function executeAgent(agent, message, token) {
    return new Promise((resolve, reject) => {
        const pythonPath = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
        const scriptPath = 'D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py';
        const proc = (0, child_process_1.spawn)(pythonPath, [scriptPath, `--agent=${agent}`, message], {
            cwd: 'D:/nas_backup/LLM_Unified/ion-mentoring',
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8'
            }
        });
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        proc.on('close', (code) => {
            if (token.isCancellationRequested) {
                reject('작업이 취소되었습니다.');
                return;
            }
            if (code === 0) {
                resolve(stdout);
            }
            else {
                reject(stderr || stdout);
            }
        });
        token.onCancellationRequested(() => {
            proc.kill();
        });
    });
}
// Chat Participant용 실행 함수 (기존 유지)
async function executeGitkoAgent(message, stream, token) {
    return new Promise((resolve, reject) => {
        // Python 실행 파일 경로
        const pythonPath = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
        const scriptPath = 'D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py';
        // Python 스크립트 실행
        const proc = (0, child_process_1.spawn)(pythonPath, [scriptPath, message], {
            cwd: 'D:/nas_backup/LLM_Unified/ion-mentoring',
            env: {
                ...process.env,
                PYTHONIOENCODING: 'utf-8'
            }
        });
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', (data) => {
            const text = data.toString();
            stdout += text;
            // 실시간 진행상황 표시
            const lines = text.split('\n').filter((l) => l.trim());
            for (const line of lines) {
                if (line.includes('분석 완료') || line.includes('실행 중') || line.includes('대기')) {
                    stream.markdown(`${line}\n\n`);
                }
            }
        });
        proc.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        proc.on('close', (code) => {
            if (token.isCancellationRequested) {
                reject(new Error('작업이 취소되었습니다.'));
                return;
            }
            if (code === 0) {
                // 출력 파싱
                const result = parseAgentOutput(stdout);
                resolve(result);
            }
            else {
                resolve({
                    agent: 'gitko',
                    status: 'error',
                    summary: '에이전트 실행 실패',
                    error: stderr || stdout
                });
            }
        });
        proc.on('error', (error) => {
            reject(new Error(`프로세스 실행 오류: ${error.message}`));
        });
        // 취소 처리
        token.onCancellationRequested(() => {
            proc.kill();
        });
    });
}
function parseAgentOutput(output) {
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
            output: outputText
        };
    }
    catch (error) {
        return {
            agent: 'gitko',
            status: 'error',
            summary: '출력 파싱 실패',
            error: error instanceof Error ? error.message : String(error),
            output: output
        };
    }
}
// HTTP Poller 함수들
function enableHttpPoller() {
    if (taskPoller && taskPoller.isActive()) {
        vscode.window.showInformationMessage('HTTP Task Poller is already running');
        return;
    }
    // HTTP Poller 설정은 contributes.configuration의 "gitko" 섹션을 따름
    const config = vscode.workspace.getConfiguration('gitko');
    const apiBase = config.get('httpApiBase', 'http://localhost:8091/api');
    const interval = config.get('httpPollingInterval', 2000);
    httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller enabled`);
    httpPollerOutputChannel?.appendLine(`API Base: ${apiBase}`);
    httpPollerOutputChannel?.appendLine(`Polling Interval: ${interval}ms`);
    httpPollerOutputChannel?.show();
    vscode.window.showInformationMessage(`✅ Gitko HTTP Task Poller enabled (${interval}ms interval)`);
    taskPoller = new httpTaskPoller_1.HttpTaskPoller(apiBase, 'gitko-extension', interval);
    taskPoller.setOutputCallback((msg) => httpPollerOutputChannel?.appendLine(msg));
    taskPoller.start();
}
function disableHttpPoller() {
    if (taskPoller && taskPoller.isActive()) {
        taskPoller.stop();
        httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller disabled`);
        vscode.window.showInformationMessage('❌ Gitko HTTP Task Poller disabled');
        return;
    }
    if (httpPollerInterval) {
        clearInterval(httpPollerInterval);
        httpPollerInterval = undefined;
    }
    httpPollerOutputChannel?.appendLine(`[${new Date().toISOString()}] HTTP Task Poller disabled`);
    vscode.window.showInformationMessage('❌ Gitko HTTP Task Poller disabled');
}
function deactivate() {
    if (httpPollerInterval) {
        clearInterval(httpPollerInterval);
        httpPollerInterval = undefined;
    }
    console.log('Gitko Agent Extension is deactivated');
}
//# sourceMappingURL=extension.js.map