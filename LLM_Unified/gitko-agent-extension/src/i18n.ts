import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Internationalization (i18n) support
 */

type LocaleStrings = Record<string, string>;

let currentLocale: string = 'en';
let translations: LocaleStrings = {};

/**
 * Initialize i18n with VS Code locale
 */
export function initializeI18n(extensionPath: string): void {
    // Get VS Code locale (e.g., 'en', 'ko', 'ja')
    const vscodeLocale = vscode.env.language || 'en';

    // Map to supported locales (en, ko)
    currentLocale = vscodeLocale.startsWith('ko') ? 'ko' : 'en';

    // Load translations
    const localePath = path.join(extensionPath, 'out', 'locales', `${currentLocale}.json`);
    const fallbackPath = path.join(extensionPath, 'out', 'locales', 'en.json');

    try {
        if (fs.existsSync(localePath)) {
            translations = JSON.parse(fs.readFileSync(localePath, 'utf-8'));
        } else if (fs.existsSync(fallbackPath)) {
            translations = JSON.parse(fs.readFileSync(fallbackPath, 'utf-8'));
            currentLocale = 'en';
        }
    } catch (error) {
        console.error('[i18n] Failed to load translations:', error);
        translations = {};
    }
}

/**
 * Get localized string
 * @param key Translation key (e.g., 'extension.activated')
 * @param args Optional format arguments
 */
export function t(key: string, ...args: (string | number)[]): string {
    let text = translations[key] || key;

    // Replace placeholders {0}, {1}, etc.
    args.forEach((arg, index) => {
        text = text.replace(`{${index}}`, String(arg));
    });

    return text;
}

/**
 * Get current locale
 */
export function getLocale(): string {
    return currentLocale;
}

/**
 * Check if locale is Korean
 */
export function isKorean(): boolean {
    return currentLocale === 'ko';
}
