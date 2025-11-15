import { describe, it, expect } from 'vitest';
import { buildI18nReport } from '../src/i18nGuardCore';
import * as path from 'path';

// Enforce that there are no missing keys in en/ko for current codebase

describe('i18n coverage', () => {
  it('has no missing keys', () => {
    const root = path.resolve(__dirname, '..');
    const r = buildI18nReport(root);
    // If this fails, run the VS Code command: Gitko Dev: i18n Sync Missing Keys
    expect(r.missingInEn, `Missing in en.json: ${r.missingInEn.join(', ')}`).toHaveLength(0);
    expect(r.missingInKo, `Missing in ko.json: ${r.missingInKo.join(', ')}`).toHaveLength(0);
  });
});
