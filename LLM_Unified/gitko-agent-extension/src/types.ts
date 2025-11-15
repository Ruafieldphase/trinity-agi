// Shared types

export interface OperationSummaryEntry {
  count: number;
  successRate: number; // 0..100 percent or 0..1? Consumers define
  avgDuration: number; // milliseconds
}
