import * as fs from 'fs';
import * as path from 'path';

export interface I18nReport {
  usedKeys: string[];
  enKeys: string[];
  koKeys: string[];
  missingInEn: string[];
  missingInKo: string[];
  unusedInEn: string[];
  unusedInKo: string[];
}

function walk(dir: string, acc: string[] = []): string[] {
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const it of items) {
    const p = path.join(dir, it.name);
    if (it.isDirectory()) walk(p, acc);
    else if (it.isFile() && (p.endsWith('.ts') || p.endsWith('.tsx'))) acc.push(p);
  }
  return acc;
}

export function scanUsedKeys(root: string): string[] {
  const srcDir = path.join(root, 'src');
  const files = walk(srcDir);
  const keys = new Set<string>();
  const re = /\bt\(\s*["'`]([^"'`]+)["'`]/g;
  for (const f of files) {
    const text = fs.readFileSync(f, 'utf-8');
    let m: RegExpExecArray | null;
    while ((m = re.exec(text))) {
      keys.add(m[1]);
    }
  }
  return Array.from(keys).sort();
}

export function readLocale(file: string): Record<string, string> {
  if (!fs.existsSync(file)) return {};
  try {
    return JSON.parse(fs.readFileSync(file, 'utf-8')) as Record<string, string>;
  } catch {
    return {};
  }
}

export function buildI18nReport(root: string): I18nReport {
  const usedKeys = scanUsedKeys(root);
  const enPath = path.join(root, 'src', 'locales', 'en.json');
  const koPath = path.join(root, 'src', 'locales', 'ko.json');
  const en = readLocale(enPath);
  const ko = readLocale(koPath);
  const enKeys = Object.keys(en).sort();
  const koKeys = Object.keys(ko).sort();

  const missingInEn = usedKeys.filter((k) => !(k in en));
  const missingInKo = usedKeys.filter((k) => !(k in ko));
  const unusedInEn = enKeys.filter((k) => !usedKeys.includes(k));
  const unusedInKo = koKeys.filter((k) => !usedKeys.includes(k));

  return { usedKeys, enKeys, koKeys, missingInEn, missingInKo, unusedInEn, unusedInKo };
}

export function sortObject(obj: Record<string, string>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const k of Object.keys(obj).sort()) out[k] = obj[k];
  return out;
}
