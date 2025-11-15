import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    include: ['test/**/*.test.ts'],
    exclude: ['out/**', 'node_modules/**'],
    reporters: 'default',
    passWithNoTests: false,
  },
});
