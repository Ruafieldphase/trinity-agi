import * as vscode from 'vscode';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import AdmZip from 'adm-zip';
import { PerformanceMonitor } from './performanceMonitor';
import { Logger } from './logger';
import { SecurityGuardrails } from './securityGuardrails';

function redactText(text: string): string {
  // similar to logger's redact
  try {
    text = text.replace(/([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[A-Za-z]{2,})/g, '[REDACTED:email]');
    text = text.replace(/Bearer\s+[A-Za-z0-9._-]+/gi, 'Bearer [REDACTED:token]');
    text = text.replace(/(api[-_ ]?key\s*[:=]\s*)["']?[A-Za-z0-9_-]{8,}["']?/gi, '$1[REDACTED:key]');
    text = text.replace(/(secret|password|token)\s*[:=]\s*["']?[A-Za-z0-9+/=]{8,}["']?/gi, '$1:[REDACTED]');
  } catch {
    // ignore redact errors
  }
  return text;
}

function redactConfig(obj: unknown): unknown {
  if (obj === null || typeof obj !== 'object') return obj;
  if (Array.isArray(obj)) return obj.map((x) => redactConfig(x));
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const key = k.toLowerCase();
    if (key.includes('secret') || key.includes('token') || key.includes('password')) {
      out[k] = '[REDACTED]';
    } else if (typeof v === 'string') {
      out[k] = redactText(v);
    } else {
      out[k] = redactConfig(v);
    }
  }
  return out;
}

export async function runPreflight(): Promise<{ ok: boolean; checks: Array<{ name: string; ok: boolean; message?: string }> }> {
  const cfg = vscode.workspace.getConfiguration('gitko');
  const apiBase = (cfg.get('httpApiBase', 'http://localhost:8091/api') as string).replace(/\/$/, '');
  const checks: Array<{ name: string; ok: boolean; message?: string }> = [];

  // HTTP reachability
  try {
    const res = await fetch(`${apiBase}/health`, { method: 'GET' });
    if (res.ok) {
      checks.push({ name: 'HTTP API /health reachable', ok: true });
    } else {
      checks.push({ name: 'HTTP API /health reachable', ok: false, message: `HTTP ${res.status}` });
    }
  } catch (e) {
    checks.push({ name: 'HTTP API /health reachable', ok: false, message: String((e as Error).message) });
  }

  // Tasks next endpoint
  try {
    const res = await fetch(`${apiBase}/tasks/next`, { method: 'GET', headers: { Accept: 'application/json' } });
    if (res.ok || res.status === 204) {
      checks.push({ name: 'HTTP API /tasks/next reachable', ok: true });
    } else {
      checks.push({ name: 'HTTP API /tasks/next reachable', ok: false, message: `HTTP ${res.status}` });
    }
  } catch (e) {
    checks.push({ name: 'HTTP API /tasks/next reachable', ok: false, message: String((e as Error).message) });
  }

  // SSE endpoint header check (Content-Type)
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 1500);
    const res = await fetch(`${apiBase}/tasks/stream?workerId=preflight`, {
      method: 'GET',
      headers: { Accept: 'text/event-stream' },
      signal: controller.signal,
    });
    clearTimeout(id);
    const ct = res.headers.get('content-type') || '';
    if (res.ok && ct.includes('text/event-stream')) {
      checks.push({ name: 'SSE endpoint provides event-stream', ok: true });
    } else {
      checks.push({ name: 'SSE endpoint provides event-stream', ok: false, message: `status=${res.status} ct=${ct}` });
    }
  } catch (e) {
    checks.push({ name: 'SSE endpoint provides event-stream', ok: false, message: String((e as Error).message) });
  }

  // File system write permission (temp dir)
  try {
    const tmp = path.join(os.tmpdir(), `gitko-diag-${Date.now()}.txt`);
    fs.writeFileSync(tmp, 'diag');
    fs.unlinkSync(tmp);
    checks.push({ name: 'Filesystem write (tmp)', ok: true });
  } catch (e) {
    checks.push({ name: 'Filesystem write (tmp)', ok: false, message: String((e as Error).message) });
  }

  const ok = checks.every((c) => c.ok);
  return { ok, checks };
}

export async function exportDiagnosticsBundle(): Promise<void> {
  const pm = PerformanceMonitor.getInstance();
  const sec = SecurityGuardrails.getInstance();

  const gitko = vscode.workspace.getConfiguration('gitko');
  const gitkoAgent = vscode.workspace.getConfiguration('gitkoAgent');

  const bundle: Record<string, string> = {};

  // Metadata
  const meta = {
    generatedAt: new Date().toISOString(),
    platform: `${process.platform} ${process.arch}`,
    node: process.version,
    vscode: vscode.version,
    extension: 'gitko-agent-extension',
  };
  bundle['meta.json'] = JSON.stringify(meta, null, 2);

  // Config (redacted)
  const cfg = { gitko: gitko, gitkoAgent: gitkoAgent } as unknown as Record<string, unknown>;
  bundle['config.redacted.json'] = JSON.stringify(redactConfig(cfg), null, 2);

  // Performance
  bundle['performance.summary.json'] = JSON.stringify(pm.getSummary(), null, 2);

  // Security audit stats
  bundle['security.stats.json'] = JSON.stringify(sec.getStats(), null, 2);

  // Preflight
  const preflight = await runPreflight();
  bundle['preflight.json'] = JSON.stringify(preflight, null, 2);

  // Optional log file
  try {
    const logToFile = (gitko.get('logToFile', false) as boolean) || false;
    const logPath = ((gitko.get('logFilePath', path.join(os.homedir(), 'gitko-agent.log')) as string) || '').trim();
    if (logToFile && logPath && fs.existsSync(logPath)) {
      const content = fs.readFileSync(logPath, 'utf-8');
      // Tail last 2MB to avoid huge zips
      const MAX = 2 * 1024 * 1024;
      const sliced = content.length > MAX ? content.slice(-MAX) : content;
      bundle['logs/gitko-agent.log'] = redactText(sliced);
    }
  } catch {
    // ignore optional log file read issues
  }

  // Offline queue dir listing (best-effort)
  try {
    const qDir = ((gitko.get('offlineQueue.dir', '') as string) || '').trim() ||
      path.join(process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'), 'gitko', 'queue');
    if (fs.existsSync(qDir)) {
      const files = fs.readdirSync(qDir);
      bundle['offlineQueue/listing.json'] = JSON.stringify({ dir: qDir, files }, null, 2);
    }
  } catch {
    // ignore offline queue listing issues
  }

  const zip = new AdmZip();
  for (const [name, content] of Object.entries(bundle)) {
    zip.addFile(name, Buffer.from(content, 'utf-8'));
  }

  const uri = await vscode.window.showSaveDialog({
    defaultUri: vscode.Uri.file(`gitko-diagnostics-${new Date().toISOString().replace(/:/g,'-').split('.')[0]}.zip`),
    filters: { 'Zip Archive': ['zip'] },
  });
  if (uri) {
    zip.writeZip(uri.fsPath);
    Logger.getInstance().info(`Diagnostics bundle saved to ${uri.fsPath}`, 'Diagnostics');
    vscode.window.showInformationMessage(`✅ Diagnostics bundle saved to ${uri.fsPath}`);
  }
}
