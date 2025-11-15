import { describe, it, expect } from 'vitest';
import { stableStringify, verifyHmacForObject } from '../src/security';

describe('HMAC verification', () => {
  it('verifies valid signature', () => {
    const obj = { task_id: 't1', type: 'ping', data: { a: 1 }, created_at: '2025-01-01T00:00:00Z' } as any;
    const secret = 's3cr3t';
    const clone = { ...obj };
    delete clone.signature;
    const data = stableStringify(clone);
    const expected = require('crypto').createHmac('sha256', secret).update(data).digest('hex');
    obj.signature = expected;

    const ok = verifyHmacForObject(obj, { enabled: true, secret, signatureField: 'signature', required: true });
    expect(ok).toBe(true);
  });

  it('rejects invalid signature', () => {
    const obj = { task_id: 't1', type: 'ping', data: { a: 1 }, signature: 'deadbeef' } as any;
    const ok = verifyHmacForObject(obj, { enabled: true, secret: 'secret', signatureField: 'signature', required: true });
    expect(ok).toBe(false);
  });

  it('passes when disabled', () => {
    const obj = { foo: 'bar' } as any;
    const ok = verifyHmacForObject(obj, { enabled: false, secret: '', signatureField: 'signature', required: false });
    expect(ok).toBe(true);
  });
});
