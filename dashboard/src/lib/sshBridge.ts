/**
 * SSH Bridge to Linux VM (via Python Proxy)
 * 
 * Uses ledger_proxy.py script to access Linux VM's Resonance Ledger
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// Path to Python proxy script
const PROXY_SCRIPT = path.resolve(process.cwd(), '..', 'scripts', 'ledger_proxy.py');
const PYTHON_CMD = process.platform === 'win32' ? 'python' : 'python3';

interface LedgerMessage {
    [key: string]: unknown;
}

interface ProxyResult {
    error?: string;
    success?: boolean;
    [key: string]: unknown;
}

/**
 * Read Resonance Ledger from Linux VM
 */
export async function readResonanceLedger(limit: number = 50, source?: string): Promise<string> {
    try {
        const args = ['read', limit.toString()];
        if (source) {
            args.push(source);
        }

        const command = `${PYTHON_CMD} "${PROXY_SCRIPT}" ${args.join(' ')}`;

        const { stdout, stderr } = await execAsync(command, {
            maxBuffer: 10 * 1024 * 1024, // 10MB buffer
            timeout: 10000 // 10 second timeout
        });

        if (stderr) {
            console.warn('Proxy stderr:', stderr);
        }

        const result = JSON.parse(stdout) as ProxyResult & LedgerMessage[];

        if (result.error) {
            throw new Error(result.error);
        }

        // Convert messages array back to JSONL format
        return (result as LedgerMessage[]).map((msg) => JSON.stringify(msg)).join('\n');

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Failed to read ledger via proxy:', error);
        throw new Error(`Proxy read failed: ${errorMessage}`);
    }
}

/**
 * Append to Resonance Ledger on Linux VM
 */
export async function appendToResonanceLedger(jsonLine: string): Promise<void> {
    try {
        // Parse the JSON line to convert it to entry object
        const entry = JSON.parse(jsonLine.trim());

        // Escape entry JSON for shell
        const entryJson = JSON.stringify(entry).replace(/"/g, '\\"');

        const command = `${PYTHON_CMD} "${PROXY_SCRIPT}" append "${entryJson}"`;

        const { stdout, stderr } = await execAsync(command, {
            timeout: 5000 // 5 second timeout
        });

        if (stderr) {
            console.warn('Proxy stderr:', stderr);
        }

        const result = JSON.parse(stdout);

        if (!result.success) {
            throw new Error('Proxy append failed');
        }

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Failed to append ledger via proxy:', error);
        throw new Error(`Proxy append failed: ${errorMessage}`);
    }
}
