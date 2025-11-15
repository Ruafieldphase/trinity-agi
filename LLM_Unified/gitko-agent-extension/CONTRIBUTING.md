# Contributing to Gitko AI Agent Orchestrator

Thank you for your interest in contributing! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

---

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

---

## 🚀 Getting Started

### Prerequisites

- **VS Code**: 1.90.0 or higher
- **Node.js**: 18.x or higher
- **Python**: 3.8 or higher
- **Git**: Latest version

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/agi.git
cd agi/LLM_Unified/gitko-agent-extension
```

---

## 🛠️ Development Setup

### 1. Install Dependencies

```powershell
# Install Node.js dependencies
npm install

# Install Python dependencies (optional)
pip install -r requirements.txt
```

### 2. Build

```powershell
# Compile TypeScript
npm run compile

# Or use watch mode
npm run watch
```

### 3. Run Extension

1. Open VS Code
2. Press `F5` to launch Extension Development Host
3. Test your changes in the new window

---

## 💡 How to Contribute

### Reporting Bugs

**Before submitting a bug report**:
- Check existing issues
- Verify it's reproducible
- Collect error logs from Output Channel

**Bug report should include**:
- Extension version
- VS Code version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error logs (if any)

**Example**:
```markdown
**Extension Version**: v0.3.1
**VS Code Version**: 1.90.0
**OS**: Windows 11

**Steps to Reproduce**:
1. Open Copilot Chat
2. Type `@gitko /review`
3. Error appears

**Expected**: Code review starts
**Actual**: Error: "Python not found"

**Logs**: (paste from Output Channel)
```

### Suggesting Features

**Feature requests should include**:
- Clear use case
- Why it's useful
- Possible implementation approach
- Any alternatives considered

### Submitting Code

See [Pull Request Process](#pull-request-process) below.

---

## 🎨 Code Style

### TypeScript

```typescript
// Use descriptive variable names
const pythonExecutable = getPythonPath();

// Prefer async/await over callbacks
async function runAgent(message: string): Promise<string> {
    const result = await executePython(message);
    return result;
}

// Add JSDoc comments for public functions
/**
 * Executes the Gitko agent with the given message
 * @param message User's input message
 * @returns Agent's response
 */
export async function executeAgent(message: string): Promise<string> {
    // ...
}

// Use interfaces for complex types
interface AgentConfig {
    pythonPath: string;
    scriptPath: string;
    timeout: number;
}
```

### Formatting

```powershell
# Auto-format on save is recommended
# Add to .vscode/settings.json:
{
    "editor.formatOnSave": true,
    "typescript.format.enable": true
}
```

### Naming Conventions

- **Files**: camelCase (e.g., `taskQueueMonitor.ts`)
- **Classes**: PascalCase (e.g., `TaskQueueMonitor`)
- **Functions**: camelCase (e.g., `executeAgent`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Interfaces**: PascalCase with `I` prefix (e.g., `IAgentConfig`)

---

## 🧪 Testing

### Running Tests

```powershell
# Automated test
.\tests\test-extension.ps1

# Integration test
.\tests\test_integration.ps1

# Manual testing
# Press F5 in VS Code
```

### Writing Tests

```typescript
// Example: Testing agent execution
import * as assert from 'assert';
import { executeAgent } from '../extension';

suite('Agent Tests', () => {
    test('should execute successfully', async () => {
        const result = await executeAgent('test message');
        assert.ok(result.length > 0);
    });

    test('should handle errors gracefully', async () => {
        try {
            await executeAgent('');
            assert.fail('Should have thrown');
        } catch (error) {
            assert.ok(error instanceof Error);
        }
    });
});
```

### Test Coverage

- Aim for 80%+ code coverage
- Test edge cases
- Test error handling
- Test async operations

---

## 🔄 Pull Request Process

### 1. Create a Branch

```bash
# Feature branch
git checkout -b feature/add-new-agent

# Bugfix branch
git checkout -b fix/python-path-detection

# Documentation branch
git checkout -b docs/update-readme
```

### 2. Make Changes

- Follow code style guidelines
- Add tests for new features
- Update documentation
- Keep commits atomic and focused

### 3. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format: <type>(<scope>): <subject>

# Examples:
git commit -m "feat(agent): add parallel execution support"
git commit -m "fix(ocr): resolve Tesseract path detection"
git commit -m "docs(readme): add troubleshooting section"
git commit -m "refactor(monitor): simplify UI update logic"
git commit -m "test(integration): add HTTP poller tests"
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### 4. Test Your Changes

```powershell
# Run all checks
npm run compile
.\tests\test-extension.ps1
.\scripts\troubleshoot.ps1
```

### 5. Update Documentation

- Update README if behavior changes
- Update CHANGELOG.md
- Add JSDoc comments
- Update relevant guides in `docs/`

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/add-new-agent

# Create PR on GitHub
# Fill out the PR template
```

### 7. PR Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: Maintainer review
3. **Testing**: Manual testing if needed
4. **Approval**: Maintainer approval
5. **Merge**: Squash and merge to main

---

## 📦 Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

- [ ] Update version in `package.json`
- [ ] Update CHANGELOG.md
- [ ] Create release notes
- [ ] Test VSIX package
- [ ] Create Git tag
- [ ] Publish release

### Creating a Release

```powershell
# 1. Update version
npm version minor  # or major/patch

# 2. Build VSIX
vsce package

# 3. Test installation
code --install-extension gitko-agent-extension-x.x.x.vsix

# 4. Create Git tag
git tag -a v0.4.0 -m "Release v0.4.0"
git push --tags

# 5. Create GitHub Release
# Upload VSIX file
# Copy CHANGELOG section
```

---

## 📚 Additional Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [GitHub Copilot Extension Guide](https://docs.github.com/en/copilot)
- [Project Structure](PROJECT_STRUCTURE.md)
- [Quick Start Guide](QUICKSTART.md)

---

## ❓ Questions?

- 💬 Open a [Discussion](https://github.com/Ruafieldphase/agi/discussions)
- 🐛 Report a [Bug](https://github.com/Ruafieldphase/agi/issues/new?template=bug_report.md)
- 💡 Request a [Feature](https://github.com/Ruafieldphase/agi/issues/new?template=feature_request.md)

---

**Thank you for contributing!** 🚀
