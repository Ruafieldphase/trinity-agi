import { describe, it, expect } from 'vitest';
import { validateTaskSafe } from '../src/schemas';

describe('schemas.validateTaskSafe', () => {
    it('accepts a minimal valid task', () => {
        const raw = { task_id: 't1', type: 'ping', data: {} };
        const res = validateTaskSafe(raw);
        expect(res.success).toBe(true);
        if (res.success) {
            expect(res.data.task_id).toBe('t1');
            expect(res.data.type).toBe('ping');
        }
    });

    it('rejects invalid task missing fields', () => {
        const raw = { type: 'ping' } as any;
        const res = validateTaskSafe(raw);
        expect(res.success).toBe(false);
        if (!res.success) {
            expect(res.error).toContain('task_id');
        }
    });
});
