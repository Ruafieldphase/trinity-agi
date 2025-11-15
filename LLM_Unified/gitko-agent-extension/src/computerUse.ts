// 🤖 Computer Use 기능: 화면 인식 + 자동 클릭
import * as vscode from 'vscode';
import { spawn } from 'child_process';
import { createLogger } from './logger';
import { PerformanceMonitor } from './performanceMonitor';
import { SecurityGuardrails } from './securityGuardrails';

const logger = createLogger('ComputerUse');
const perfMonitor = PerformanceMonitor.getInstance();
const security = SecurityGuardrails.getInstance();

/**
 * Computer Use 기능 구현
 * - 화면 캡처 (screenshot)
 * - OCR로 텍스트 인식
 * - 위치 기반 클릭/타이핑
 */

export interface ScreenElement {
    text: string;
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
}

export class ComputerUseAgent {
    private pythonPath: string;
    private scriptPath: string;
    private ocrBackend: 'auto' | 'tesseract' | 'rapidocr';

    constructor() {
        // Python 환경 설정 (설정값 우선, 없으면 기본값 사용)
        const cfg = vscode.workspace.getConfiguration('gitkoAgent');
        const defaultPy = ''; // Auto-detect from workspace
        const defaultScript = ''; // Auto-detect from workspace

        // Computer Use 전용 설정 우선
        const configuredCuPy = (cfg.get<string>('computerUsePythonPath') || '').trim();
        const configuredCuScript = (cfg.get<string>('computerUseScriptPath') || '').trim();

        // 기존 pythonPath는 백업 폴백으로만 사용 (scriptPath는 혼동 방지를 위해 사용하지 않음)
        const fallbackPy = (cfg.get<string>('pythonPath') || '').trim();

        this.pythonPath = configuredCuPy || fallbackPy || defaultPy;
        this.scriptPath = configuredCuScript || defaultScript;

        // OCR backend selection
        const backend = (cfg.get<string>('ocrBackend') || 'auto').toLowerCase();
        if (backend === 'tesseract' || backend === 'rapidocr') {
            this.ocrBackend = backend as 'tesseract' | 'rapidocr';
        } else {
            this.ocrBackend = 'auto';
        }
    }

    /**
     * 화면 캡처 + OCR로 요소 찾기
     */
    async findElementByText(searchText: string): Promise<ScreenElement | null> {
        const opId = perfMonitor.startOperation('computerUse.findElement', { searchText });

        return new Promise((resolve, reject) => {
            const args = [this.scriptPath, 'find', '--text', searchText];

            const envVars: NodeJS.ProcessEnv = { ...process.env, PYTHONIOENCODING: 'utf-8' };
            if (this.ocrBackend !== 'auto') {
                envVars.COMPUTER_USE_OCR_BACKEND = this.ocrBackend;
            }
            const child = spawn(this.pythonPath, args, { env: envVars });
            let output = '';
            let errorOutput = '';

            child.stdout?.on('data', (data: Buffer) => {
                output += data.toString();
            });

            child.stderr?.on('data', (data: Buffer) => {
                errorOutput += data.toString();
            });

            child.on('close', (code: number | null) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(output);
                        logger.debug(`Found element: ${searchText}`);
                        perfMonitor.endOperation(opId, true);
                        resolve(result);
                    } catch (error) {
                        const errMsg = `Failed to parse JSON result: ${error instanceof Error ? error.message : String(error)}`;
                        logger.error(errMsg, error as Error);
                        perfMonitor.endOperation(opId, false);
                        reject(new Error(errMsg));
                    }
                } else {
                    const errMsg = `Process exited with code ${code}: ${errorOutput}`;
                    logger.error(`Find element failed: ${searchText}`, new Error(errMsg));
                    perfMonitor.endOperation(opId, false);
                    reject(new Error(errMsg));
                }
            });

            child.on('error', (err) => {
                logger.error('Failed to spawn Python process', err);
                perfMonitor.endOperation(opId, false);
                reject(new Error(`Failed to start process: ${err.message}`));
            });
        });
    }

    /**
     * 특정 위치 클릭
     */
    async clickAt(x: number, y: number): Promise<boolean> {
        // Security check
        const check = await security.checkAction('computer_use.click', { x, y });
        if (!check.allowed) {
            throw new Error(`Action blocked: ${check.reason}`);
        }

        return new Promise((resolve, reject) => {
            const args = [this.scriptPath, 'click', '--x', x.toString(), '--y', y.toString()];

            const envVars: NodeJS.ProcessEnv = { ...process.env, PYTHONIOENCODING: 'utf-8' };
            if (this.ocrBackend !== 'auto') {
                envVars.COMPUTER_USE_OCR_BACKEND = this.ocrBackend;
            }
            const child = spawn(this.pythonPath, args, { env: envVars });
            let errorOutput = '';

            child.stderr?.on('data', (data: Buffer) => {
                errorOutput += data.toString();
            });

            child.on('close', (code: number | null) => {
                if (code === 0) {
                    logger.debug(`Clicked at (${x}, ${y})`);
                    resolve(true);
                } else {
                    const errMsg = `Click failed at (${x}, ${y}): ${errorOutput}`;
                    logger.error(errMsg);
                    reject(new Error(errMsg));
                }
            });

            child.on('error', (err) => {
                logger.error('Failed to spawn Python process for click', err);
                reject(new Error(`Failed to start process: ${err.message}`));
            });
        });
    }

    /**
     * 텍스트로 요소 찾아서 클릭
     */
    async clickElementByText(searchText: string): Promise<boolean> {
        // Security check
        const check = await security.checkAction('computer_use.click', { text: searchText });
        if (!check.allowed) {
            throw new Error(`Action blocked: ${check.reason}`);
        }

        try {
            const element = await this.findElementByText(searchText);
            if (!element) {
                const errMsg = `Element with text "${searchText}" not found`;
                logger.warn(errMsg);
                throw new Error(errMsg);
            }

            // 요소 중심 클릭
            const centerX = Math.round(element.x + element.width / 2);
            const centerY = Math.round(element.y + element.height / 2);

            logger.info(`Clicking element "${searchText}" at (${centerX}, ${centerY})`);
            return await this.clickAt(centerX, centerY);
        } catch (error) {
            logger.error(`Failed to click element by text: ${searchText}`, error as Error);
            throw error;
        }
    }

    /**
     * 키보드 입력
     */
    async type(text: string): Promise<boolean> {
        // Security check
        const check = await security.checkAction('computer_use.type', { text });
        if (!check.allowed) {
            throw new Error(`Action blocked: ${check.reason}`);
        }

        return new Promise((resolve, reject) => {
            const args = [this.scriptPath, 'type', '--text', text];

            const envVars: NodeJS.ProcessEnv = { ...process.env, PYTHONIOENCODING: 'utf-8' };
            if (this.ocrBackend !== 'auto') {
                envVars.COMPUTER_USE_OCR_BACKEND = this.ocrBackend;
            }
            const child = spawn(this.pythonPath, args, { env: envVars });
            let errorOutput = '';

            child.stderr?.on('data', (data: Buffer) => {
                errorOutput += data.toString();
            });

            child.on('close', (code: number | null) => {
                if (code === 0) {
                    logger.debug(`Typed text: ${text.substring(0, 20)}...`);
                    resolve(true);
                } else {
                    const errMsg = `Type failed: ${errorOutput}`;
                    logger.error(errMsg);
                    reject(new Error(errMsg));
                }
            });

            child.on('error', (err) => {
                logger.error('Failed to spawn Python process for type', err);
                reject(new Error(`Failed to start process: ${err.message}`));
            });
        });
    }

    /**
     * 화면 전체 스캔 (모든 텍스트 요소 찾기)
     */
    async scanScreen(): Promise<ScreenElement[]> {
        return new Promise((resolve, reject) => {
            const args = [this.scriptPath, 'scan'];

            const envVars: NodeJS.ProcessEnv = { ...process.env, PYTHONIOENCODING: 'utf-8' };
            if (this.ocrBackend !== 'auto') {
                envVars.COMPUTER_USE_OCR_BACKEND = this.ocrBackend;
            }
            const child = spawn(this.pythonPath, args, { env: envVars });
            let output = '';
            let errorOutput = '';

            child.stdout?.on('data', (data: Buffer) => {
                output += data.toString();
            });

            child.stderr?.on('data', (data: Buffer) => {
                errorOutput += data.toString();
            });

            child.on('close', (code: number | null) => {
                if (code === 0) {
                    try {
                        const result = JSON.parse(output);
                        logger.debug(`Screen scan found ${result.length} elements`);
                        resolve(result);
                    } catch (error) {
                        const errMsg = `Failed to parse scan result: ${error instanceof Error ? error.message : String(error)}`;
                        logger.error(errMsg, error as Error);
                        reject(new Error(errMsg));
                    }
                } else {
                    const errMsg = `Scan failed with code ${code}: ${errorOutput}`;
                    logger.error(errMsg);
                    reject(new Error(errMsg));
                }
            });

            child.on('error', (err) => {
                logger.error('Failed to spawn Python process for scan', err);
                reject(new Error(`Failed to start process: ${err.message}`));
            });
        });
    }
}

/**
 * VS Code 명령으로 등록
 */
export function registerComputerUseCommands(context: vscode.ExtensionContext) {
    const agent = new ComputerUseAgent();

    // 1. 텍스트로 요소 찾아 클릭
    const clickByTextCmd = vscode.commands.registerCommand('gitko.computerUse.clickByText', async () => {
        const searchText = await vscode.window.showInputBox({
            prompt: '찾을 텍스트를 입력하세요',
            placeHolder: 'Gitko',
        });

        if (!searchText) {
            return;
        }

        try {
            await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: `"${searchText}" 요소 찾는 중...`,
                    cancellable: false,
                },
                async (_progress) => {
                    const success = await agent.clickElementByText(searchText);
                    if (success) {
                        vscode.window.showInformationMessage(`✅ "${searchText}" 클릭 완료`);
                    }
                }
            );
        } catch (error) {
            vscode.window.showErrorMessage(`❌ 클릭 실패: ${error instanceof Error ? error.message : String(error)}`);
        }
    });

    // 2. 화면 스캔 (모든 요소 보기)
    const scanScreenCmd = vscode.commands.registerCommand('gitko.computerUse.scanScreen', async () => {
        try {
            const elements = await agent.scanScreen();
            const outputChannel = vscode.window.createOutputChannel('Computer Use - Screen Scan');
            outputChannel.clear();
            outputChannel.appendLine(`🔍 총 ${elements.length}개 요소 발견:\n`);

            elements.forEach((el, index) => {
                outputChannel.appendLine(`${index + 1}. "${el.text}"`);
                outputChannel.appendLine(`   위치: (${el.x}, ${el.y})`);
                outputChannel.appendLine(`   크기: ${el.width}x${el.height}`);
                outputChannel.appendLine(`   신뢰도: ${(el.confidence * 100).toFixed(1)}%\n`);
            });

            outputChannel.show();
            vscode.window.showInformationMessage(`✅ 화면 스캔 완료: ${elements.length}개 요소 발견`);
        } catch (error) {
            vscode.window.showErrorMessage(`❌ 스캔 실패: ${error instanceof Error ? error.message : String(error)}`);
        }
    });

    context.subscriptions.push(clickByTextCmd, scanScreenCmd);
}
