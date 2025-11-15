import { describe, it, expect } from 'vitest';
import { PerformanceMonitor } from '../src/performanceMonitor';

describe('PerformanceMonitor', () => {
    it('tracks start/end and computes duration', async () => {
        const pm = PerformanceMonitor.getInstance();
        const opId = pm.startOperation('unit.test');
        await new Promise((r) => setTimeout(r, 10));
        pm.endOperation(opId, true);
        const stats = pm.getOperationStats('unit.test');
        expect(stats.totalCount).toBeGreaterThanOrEqual(1);
        expect(stats.successCount).toBeGreaterThanOrEqual(1);
        expect(stats.avgDuration).toBeGreaterThanOrEqual(0);
    });
});
