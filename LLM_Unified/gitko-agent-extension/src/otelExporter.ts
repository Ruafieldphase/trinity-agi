// Avoid hard dependency on VS Code API during unit tests
let vscodeApi: unknown = undefined;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  vscodeApi = require('vscode');
} catch {
  vscodeApi = undefined;
}
import * as nodeCrypto from 'crypto';
import { PerformanceMonitor, PerformanceMetrics } from './performanceMonitor';
import { createLogger } from './logger';

const logger = createLogger('OtelExporter');

// Simple histogram buckets in milliseconds
const DURATION_BUCKETS = [10, 50, 100, 500, 1000, 2000, 5000, 10000];

interface ExportState {
  lastExportedAt: number; // export only metrics whose endTime > lastExportedAt
}

let intervalHandle: NodeJS.Timeout | undefined;
const state: ExportState = { lastExportedAt: 0 };

export function startOtelExporter() {
  const cfg = (vscodeApi as { workspace?: { getConfiguration?: (section: string) => unknown } } | undefined)
    ?.workspace?.getConfiguration?.('gitko') as { get: (key: string, defaultValue?: unknown) => unknown };
  const enabled = (cfg.get('otel.enabled', false) as boolean) ?? false;
  if (!enabled) return;

  const endpoint = ((cfg.get('otel.endpoint', 'http://localhost:4318') as string) || 'http://localhost:4318').replace(/\/$/, '');
  const headerName = (cfg.get('otel.headerName', 'Authorization') as string) || 'Authorization';
  const token = (cfg.get('otel.token', '') as string) || '';
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers[headerName] = token;

  const flush = async () => {
    try {
      const pm = PerformanceMonitor.getInstance();
      const operations = pm.getAllOperations();
      const spans: OtelSpan[] = [];
      const durations: number[] = [];
      const latencies: number[] = [];

      for (const op of operations) {
        const recents = pm.getRecentMetrics(op, 100);
        for (const m of recents) {
          if (!m.endTime || m.endTime <= state.lastExportedAt) continue;
          spans.push(metricToSpan(m));
          if (typeof m.duration === 'number') durations.push(m.duration);
          const q = (m.metadata && (m.metadata['queueLatencyMs'] as number)) || undefined;
          if (typeof q === 'number') latencies.push(q);
        }
      }

      if (spans.length > 0) {
        const body = buildTraces(spans);
        await fetch(`${endpoint}/v1/traces`, { method: 'POST', headers, body: JSON.stringify(body) });
        logger.info(`Exported ${spans.length} spans to OTLP`);
        // Update last exported at to max endTime
        const maxEnd = Math.max(...spans.map((s) => Number(s.endTimeUnixNano) / 1e6));
        state.lastExportedAt = Math.max(state.lastExportedAt, maxEnd);
      }

      if (durations.length > 0 || latencies.length > 0) {
        const body = buildMetrics(durations, latencies);
        await fetch(`${endpoint}/v1/metrics`, { method: 'POST', headers, body: JSON.stringify(body) });
        logger.info(`Exported metrics to OTLP`);
      }
    } catch (err) {
      logger.warn(`OTLP export failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  // Export every 10s
  intervalHandle = setInterval(flush, 10000);
  logger.info('OTLP exporter started');
}

export function stopOtelExporter() {
  if (intervalHandle) clearInterval(intervalHandle);
  intervalHandle = undefined;
}

function metricToSpan(m: PerformanceMetrics) {
  const startN = BigInt(m.startTime) * 1_000_000n;
  const endN = BigInt(m.endTime || Date.now()) * 1_000_000n;
  // random 16-byte traceId and 8-byte spanId (hex)
  const traceId = cryptoRandomHex(16);
  const spanId = cryptoRandomHex(8);
  return {
    traceId,
    spanId,
    name: m.operationName,
    kind: 1, // INTERNAL
    startTimeUnixNano: startN.toString(),
    endTimeUnixNano: endN.toString(),
    attributes: attributesFromMeta(m),
    status: { code: m.success ? 1 : 2 },
  };
}

function attributesFromMeta(m: PerformanceMetrics): OtelKeyValue[] {
  const attrs: OtelKeyValue[] = [];
  if (m.metadata) {
    for (const [k, v] of Object.entries(m.metadata)) {
      if (typeof v === 'string') attrs.push({ key: k, value: { stringValue: v } });
      else if (typeof v === 'number') attrs.push({ key: k, value: { doubleValue: v } });
      else if (typeof v === 'boolean') attrs.push({ key: k, value: { boolValue: v } });
    }
  }
  return attrs;
}

function buildTraces(spans: OtelSpan[]): OtelTraces {
  return {
    resourceSpans: [
      {
        resource: { attributes: [{ key: 'service.name', value: { stringValue: 'gitko-extension' } }] },
        scopeSpans: [
          {
            scope: { name: 'gitko.perf' },
            spans,
          },
        ],
      },
    ],
  };
}

function buildMetrics(durations: number[], latencies: number[]): OtelMetrics {
  const nowN = BigInt(Date.now()) * 1_000_000n;
  const points: OtelMetric[] = [];
  if (durations.length > 0) {
    points.push(histogramPoint('gitko_task_duration_ms', durations, nowN));
  }
  if (latencies.length > 0) {
    points.push(histogramPoint('gitko_queue_latency_ms', latencies, nowN));
  }
  return {
    resourceMetrics: [
      {
        resource: { attributes: [{ key: 'service.name', value: { stringValue: 'gitko-extension' } }] },
        scopeMetrics: [
          {
            scope: { name: 'gitko.perf' },
            metrics: points,
          },
        ],
      },
    ],
  };
}

function histogramPoint(name: string, values: number[], nowN: bigint): OtelMetric {
  const counts = new Array(DURATION_BUCKETS.length + 1).fill(0);
  for (const v of values) {
    let idx = DURATION_BUCKETS.findIndex((b) => v <= b);
    if (idx === -1) idx = DURATION_BUCKETS.length;
    counts[idx] += 1;
  }
  const sum = values.reduce((a, b) => a + b, 0);
  return {
    name,
    histogram: {
      dataPoints: [
        {
          timeUnixNano: nowN.toString(),
          startTimeUnixNano: nowN.toString(),
          count: values.length,
          sum,
          bucketCounts: counts,
          explicitBounds: DURATION_BUCKETS,
        },
      ],
      aggregationTemporality: 2, // CUMULATIVE
    },
  };
}

function cryptoRandomHex(bytes: number): string {
  const arr = new Uint8Array(bytes);
  const buf: Buffer = nodeCrypto.randomBytes(bytes);
  for (let i = 0; i < bytes; i++) arr[i] = buf[i];
  return Buffer.from(arr).toString('hex');
}

// --- Minimal OTLP JSON types ---
interface OtelKeyValue {
  key: string;
  value: { stringValue?: string; doubleValue?: number; boolValue?: boolean };
}

interface OtelSpan {
  traceId: string;
  spanId: string;
  name: string;
  kind: number;
  startTimeUnixNano: string;
  endTimeUnixNano: string;
  attributes?: OtelKeyValue[];
  status?: { code: number };
}

interface OtelTraces {
  resourceSpans: Array<{
    resource: { attributes?: OtelKeyValue[] };
    scopeSpans: Array<{
      scope: { name: string };
      spans: OtelSpan[];
    }>;
  }>;
}

interface OtelMetric {
  name: string;
  histogram?: {
    dataPoints: Array<{
      timeUnixNano: string;
      startTimeUnixNano: string;
      count: number;
      sum: number;
      bucketCounts: number[];
      explicitBounds: number[];
    }>;
    aggregationTemporality: number;
  };
}

interface OtelMetrics {
  resourceMetrics: Array<{
    resource: { attributes?: OtelKeyValue[] };
    scopeMetrics: Array<{
      scope: { name: string };
      metrics: OtelMetric[];
    }>;
  }>;
}
