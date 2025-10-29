// 🤖 Computer Use 기능: 화면 인식 + 자동 클릭
import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';

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
        const defaultPy = 'D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe';
        const defaultScript = 'D:/nas_backup/LLM_Unified/ion-mentoring/computer_use.py';

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
        return new Promise((resolve, reject) => {
            const args = [
                this.scriptPath,
                'find',
                '--text', searchText
            ];

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
                        resolve(result);
                    } catch (error) {
                        reject(new Error(`Failed to parse result: ${error}`));
                    }
                } else {
                    reject(new Error(`Process exited with code ${code}: ${errorOutput}`));
                }
            });
        });
    }

    /**
     * 특정 위치 클릭
     */
    async clickAt(x: number, y: number): Promise<boolean> {
        return new Promise((resolve, reject) => {
            const args = [
                this.scriptPath,
                'click',
                '--x', x.toString(),
                '--y', y.toString()
            ];

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
                    resolve(true);
                } else {
                    reject(new Error(`Click failed: ${errorOutput}`));
                }
            });
        });
    }

    /**
     * 텍스트로 요소 찾아서 클릭
     */
    async clickElementByText(searchText: string): Promise<boolean> {
        try {
            const element = await this.findElementByText(searchText);
            if (!element) {
                throw new Error(`Element with text "${searchText}" not found`);
            }

            // 요소 중심 클릭
            const centerX = element.x + element.width / 2;
            const centerY = element.y + element.height / 2;

            return await this.clickAt(centerX, centerY);
        } catch (error) {
            throw error;
        }
    }

    /**
     * 키보드 입력
     */
    async type(text: string): Promise<boolean> {
        return new Promise((resolve, reject) => {
            const args = [
                this.scriptPath,
                'type',
                '--text', text
            ];

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
                    resolve(true);
                } else {
                    reject(new Error(`Type failed: ${errorOutput}`));
                }
            });
        });
    }

    /**
     * 화면 전체 스캔 (모든 텍스트 요소 찾기)
     */
    async scanScreen(): Promise<ScreenElement[]> {
        return new Promise((resolve, reject) => {
            const args = [
                this.scriptPath,
                'scan'
            ];

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
                        resolve(result);
                    } catch (error) {
                        reject(new Error(`Failed to parse result: ${error}`));
                    }
                } else {
                    reject(new Error(`Scan failed: ${errorOutput}`));
                }
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
    const clickByTextCmd = vscode.commands.registerCommand(
        'gitko.computerUse.clickByText',
        async () => {
            const searchText = await vscode.window.showInputBox({
                prompt: '찾을 텍스트를 입력하세요',
                placeHolder: 'Gitko'
            });

            if (!searchText) {
                return;
            }

            try {
                await vscode.window.withProgress(
                    {
                        location: vscode.ProgressLocation.Notification,
                        title: `"${searchText}" 요소 찾는 중...`,
                        cancellable: false
                    },
                    async (progress) => {
                        const success = await agent.clickElementByText(searchText);
                        if (success) {
                            vscode.window.showInformationMessage(`✅ "${searchText}" 클릭 완료`);
                        }
                    }
                );
            } catch (error) {
                vscode.window.showErrorMessage(
                    `❌ 클릭 실패: ${error instanceof Error ? error.message : String(error)}`
                );
            }
        }
    );

    // 2. 화면 스캔 (모든 요소 보기)
    const scanScreenCmd = vscode.commands.registerCommand(
        'gitko.computerUse.scanScreen',
        async () => {
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
                vscode.window.showErrorMessage(
                    `❌ 스캔 실패: ${error instanceof Error ? error.message : String(error)}`
                );
            }
        }
    );

    context.subscriptions.push(clickByTextCmd, scanScreenCmd);
}
