import * as crypto from 'crypto';

export interface HmacConfig {
  enabled: boolean;
  secret: string;
  signatureField: string;
  required: boolean;
}

/** Stable stringify: sort object keys recursively to get deterministic JSON */
export function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return '[' + value.map((v) => stableStringify(v)).join(',') + ']';
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const parts: string[] = [];
  for (const k of keys) {
    parts.push(JSON.stringify(k) + ':' + stableStringify(obj[k]));
  }
  return '{' + parts.join(',') + '}';
}

/** Verify HMAC using SHA-256 over the payload with signature field removed */
export function verifyHmacForObject(payload: Record<string, unknown>, cfg: HmacConfig): boolean {
  if (!cfg.enabled || !cfg.secret) {
    return true; // disabled
  }
  const sigField = cfg.signatureField || 'signature';
  const provided = (payload as Record<string, unknown>)[sigField] as string | undefined;
  if (!provided || typeof provided !== 'string') {
    return !cfg.required ? true : false;
  }
  // clone without signature field
  const clone: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(payload)) {
    if (k === sigField) continue;
    clone[k] = v;
  }
  const data = stableStringify(clone);
  const expected = crypto.createHmac('sha256', cfg.secret).update(data).digest('hex');
  const ok = timingSafeEqualHex(expected, provided);
  return ok;
}

function timingSafeEqualHex(a: string, b: string): boolean {
  try {
    const aBuf = Buffer.from(a, 'hex');
    const bBuf = Buffer.from(b, 'hex');
    if (aBuf.length !== bBuf.length) return false;
    return crypto.timingSafeEqual(aBuf, bBuf);
  } catch {
    return false;
  }
}
