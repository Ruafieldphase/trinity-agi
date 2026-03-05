---
name: FileOrganizer
description: Intelligently organizes files and folders by understanding context, finding duplicates, and suggesting better organizational structures.
---

# File Organizer

When a user requests file organization help:

1. **Understand the Scope**
   - Which directory needs organization? (Downloads, Documents, entire home folder?)
   - What's the main problem? (Can't find things, duplicates, too messy, no structure?)
   - Any files or folders to avoid? (Current projects, sensitive data?)
   - How aggressively to organize? (Conservative vs. comprehensive cleanup)

2. **Analyze Current State**
   Review the target directory:
   ```bash
   ls -la [target_directory]
   find [target_directory] -type f -exec file {} \; | head -20
   du -sh [target_directory]/* | sort -rh | head -20
   find [target_directory] -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn
   ```

3. **Identify Organization Patterns**
   Based on the files, determine logical groupings:
   - **By Type**: Documents, Images, Videos, Code, etc.
   - **By Purpose**: Work vs. Personal, Active vs. Archive.
   - **By Date**: Current year, archive candidates.

4. **Find Duplicates**
   ```bash
   find [directory] -type f -exec md5 {} \; | sort | uniq -d
   ```

5. **Propose Organization Plan**
   Present a clear plan before making changes.

6. **Execute Organization**
   - Create folders: `mkdir -p "path"`
   - Move files: `mv "source" "dest"`
   - Always confirm before deleting.

7. **Provide Summary and Maintenance Tips**
