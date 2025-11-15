import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { buildI18nReport, sortObject, readLocale } from './i18nGuardCore';
import type { I18nReport } from './i18nGuardCore';

export async function runI18nCheck(): Promise<I18nReport> {
  const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || path.resolve(__dirname, '..');
  const report = buildI18nReport(root);
  const ch = vscode.window.createOutputChannel('Gitko i18n Check');
  ch.clear();
  ch.appendLine('=== Gitko i18n Coverage Check ===\n');
  ch.appendLine(`Used keys: ${report.usedKeys.length}`);
  ch.appendLine(`en keys: ${report.enKeys.length}`);
  ch.appendLine(`ko keys: ${report.koKeys.length}\n`);
  if (report.missingInEn.length) {
    ch.appendLine('Missing in en.json:');
    for (const k of report.missingInEn) ch.appendLine(`  - ${k}`);
    ch.appendLine('');
  }
  if (report.missingInKo.length) {
    ch.appendLine('Missing in ko.json:');
    for (const k of report.missingInKo) ch.appendLine(`  - ${k}`);
    ch.appendLine('');
  }
  if (report.unusedInEn.length) {
    ch.appendLine('Unused keys in en.json:');
    for (const k of report.unusedInEn) ch.appendLine(`  - ${k}`);
    ch.appendLine('');
  }
  if (report.unusedInKo.length) {
    ch.appendLine('Unused keys in ko.json:');
    for (const k of report.unusedInKo) ch.appendLine(`  - ${k}`);
    ch.appendLine('');
  }
  if (report.missingInEn.length === 0 && report.missingInKo.length === 0) {
    ch.appendLine('✅ No missing keys.');
  }
  ch.show();
  return report;
}

export async function runI18nSync(): Promise<void> {
  const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || path.resolve(__dirname, '..');
  const enPath = path.join(root, 'src', 'locales', 'en.json');
  const koPath = path.join(root, 'src', 'locales', 'ko.json');
  const en = readLocale(enPath);
  const ko = readLocale(koPath);
  const report = buildI18nReport(root);

  let changed = false;
  for (const k of report.missingInEn) {
    en[k] = k; // default string = key
    changed = true;
  }
  for (const k of report.missingInKo) {
    ko[k] = en[k] || k;
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(enPath, JSON.stringify(sortObject(en), null, 4) + '\n', 'utf-8');
    fs.writeFileSync(koPath, JSON.stringify(sortObject(ko), null, 4) + '\n', 'utf-8');
    vscode.window.showInformationMessage('✅ i18n sync complete (missing keys added).');
  } else {
    vscode.window.showInformationMessage('i18n sync: no changes needed.');
  }
}

  const ch = vscode.window.createOutputChannel('Gitko i18n Check');
