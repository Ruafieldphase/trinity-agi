"use strict";
/**
 * Performance Monitor for Gitko Extension
 * Tracks execution times, memory usage, and operation statistics
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PerformanceMonitor = void 0;
exports.trackPerformance = trackPerformance;
const logger_1 = require("./logger");
const logger = (0, logger_1.createLogger)('PerformanceMonitor');
class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.activeOperations = new Map();
        this.MAX_METRICS_PER_OPERATION = 100; // 작업당 최대 100개 메트릭
        this.MAX_TOTAL_METRICS = 1000; // 전체 최대 1000개 메트릭
        logger.debug('PerformanceMonitor initialized');
        this.startAutoCleanup();
    }
    static getInstance() {
        if (!PerformanceMonitor.instance) {
            PerformanceMonitor.instance = new PerformanceMonitor();
        }
        return PerformanceMonitor.instance;
    }
    /**
     * Start tracking an operation
     */
    startOperation(operationName, metadata) {
        const operationId = `${operationName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const startTime = Date.now();
        this.activeOperations.set(operationId, startTime);
        const metric = {
            operationName,
            startTime,
            success: false,
            metadata
        };
        if (!this.metrics.has(operationName)) {
            this.metrics.set(operationName, []);
        }
        this.metrics.get(operationName).push(metric);
        logger.debug(`Operation started: ${operationName} (${operationId})`);
        return operationId;
    }
    /**
     * End tracking an operation
     */
    endOperation(operationId, success = true, metadata) {
        const startTime = this.activeOperations.get(operationId);
        if (!startTime) {
            logger.warn(`Operation ID not found: ${operationId}`);
            return;
        }
        const endTime = Date.now();
        const duration = endTime - startTime;
        this.activeOperations.delete(operationId);
        // Find and update the metric
        const operationName = operationId.split('_')[0];
        const metrics = this.metrics.get(operationName);
        if (metrics) {
            const metric = metrics.find(m => m.startTime === startTime && !m.endTime);
            if (metric) {
                metric.endTime = endTime;
                metric.duration = duration;
                metric.success = success;
                if (metadata) {
                    metric.metadata = { ...metric.metadata, ...metadata };
                }
            }
        }
        // 자동 정리: 작업별 메트릭 수 제한
        this.trimMetricsIfNeeded(operationName);
        logger.debug(`Operation ended: ${operationName} (${duration}ms, success: ${success})`);
    }
    /**
     * Get statistics for an operation
     */
    getOperationStats(operationName) {
        const metrics = this.metrics.get(operationName) || [];
        const completedMetrics = metrics.filter(m => m.duration !== undefined);
        if (completedMetrics.length === 0) {
            return {
                totalCount: 0,
                successCount: 0,
                failureCount: 0,
                avgDuration: 0,
                minDuration: 0,
                maxDuration: 0
            };
        }
        const durations = completedMetrics.map(m => m.duration);
        const successCount = completedMetrics.filter(m => m.success).length;
        return {
            totalCount: completedMetrics.length,
            successCount,
            failureCount: completedMetrics.length - successCount,
            avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
            minDuration: Math.min(...durations),
            maxDuration: Math.max(...durations)
        };
    }
    /**
     * Get all operation names
     */
    getAllOperations() {
        return Array.from(this.metrics.keys());
    }
    /**
     * Get recent metrics for an operation
     */
    getRecentMetrics(operationName, count = 10) {
        const metrics = this.metrics.get(operationName) || [];
        return metrics.slice(-count);
    }
    /**
     * Clear metrics for an operation
     */
    clearMetrics(operationName) {
        if (operationName) {
            this.metrics.delete(operationName);
            logger.info(`Cleared metrics for: ${operationName}`);
        }
        else {
            this.metrics.clear();
            logger.info('Cleared all metrics');
        }
    }
    /**
     * Get summary of all operations
     */
    getSummary() {
        const summary = {};
        for (const operationName of this.getAllOperations()) {
            const stats = this.getOperationStats(operationName);
            summary[operationName] = {
                count: stats.totalCount,
                successRate: stats.totalCount > 0 ? (stats.successCount / stats.totalCount) * 100 : 0,
                avgDuration: stats.avgDuration
            };
        }
        return summary;
    }
    /**
     * Export metrics to JSON
     */
    exportMetrics() {
        const data = {
            timestamp: new Date().toISOString(),
            summary: this.getSummary(),
            activeOperations: this.activeOperations.size,
            operations: Object.fromEntries(this.metrics)
        };
        return JSON.stringify(data, null, 2);
    }
    /**
     * Trim metrics if exceeding limits
     */
    trimMetricsIfNeeded(operationName) {
        const metrics = this.metrics.get(operationName);
        if (metrics && metrics.length > this.MAX_METRICS_PER_OPERATION) {
            // Keep only the most recent metrics
            const trimmed = metrics.slice(-this.MAX_METRICS_PER_OPERATION);
            this.metrics.set(operationName, trimmed);
            logger.debug(`Trimmed metrics for ${operationName}: ${metrics.length} -> ${trimmed.length}`);
        }
        // Check total metrics count
        const totalMetrics = Array.from(this.metrics.values()).reduce((sum, m) => sum + m.length, 0);
        if (totalMetrics > this.MAX_TOTAL_METRICS) {
            this.trimOldestMetrics();
        }
    }
    /**
     * Remove oldest metrics across all operations
     */
    trimOldestMetrics() {
        const allMetrics = [];
        // Collect all metrics with their operation names
        for (const [name, metrics] of this.metrics.entries()) {
            metrics.forEach((metric, index) => {
                allMetrics.push({ name, metric, index });
            });
        }
        // Sort by startTime (oldest first)
        allMetrics.sort((a, b) => a.metric.startTime - b.metric.startTime);
        // Remove oldest 20%
        const toRemove = Math.floor(allMetrics.length * 0.2);
        const removeSet = new Set(allMetrics.slice(0, toRemove).map(m => `${m.name}_${m.index}`));
        // Rebuild metrics without removed items
        for (const [name, metrics] of this.metrics.entries()) {
            const filtered = metrics.filter((_, index) => !removeSet.has(`${name}_${index}`));
            this.metrics.set(name, filtered);
        }
        logger.info(`Auto-cleaned metrics: removed ${toRemove} oldest entries`);
    }
    /**
     * Start automatic cleanup interval
     */
    startAutoCleanup() {
        // Check every 5 minutes
        setInterval(() => {
            const totalMetrics = Array.from(this.metrics.values()).reduce((sum, m) => sum + m.length, 0);
            if (totalMetrics > this.MAX_TOTAL_METRICS * 0.8) {
                logger.info(`Auto-cleanup triggered: ${totalMetrics} metrics`);
                this.trimOldestMetrics();
            }
        }, 5 * 60 * 1000);
    }
}
exports.PerformanceMonitor = PerformanceMonitor;
/**
 * Decorator for automatic performance tracking
 */
function trackPerformance(operationName) {
    return function (target, propertyKey, descriptor) {
        const originalMethod = descriptor.value;
        descriptor.value = async function (...args) {
            const monitor = PerformanceMonitor.getInstance();
            const opId = monitor.startOperation(`${operationName}.${propertyKey}`);
            try {
                const result = await originalMethod.apply(this, args);
                monitor.endOperation(opId, true);
                return result;
            }
            catch (error) {
                monitor.endOperation(opId, false, { error: error instanceof Error ? error.message : String(error) });
                throw error;
            }
        };
        return descriptor;
    };
}
//# sourceMappingURL=performanceMonitor.js.map