# Hash-Brownie | Data Integrity Utility

## Overview
**Hash-Brownie** is a recursive file verification tool designed for high-fidelity data archiving. It generates standardized Markdown reports containing modification timestamps and cryptographic hashes (checksums) to ensure data hasn't been altered or corrupted over time.

## Functional Core
1. **Recursive Indexing:** Automatically traverses all sub-directories within a chosen root path.
2. **Directory Grouping:** Organizes results by folder to maintain project structure within the documentation.
3. **Buffered Processing:** Handles large binary data (e.g., 3D scans, 4K textures) using a 64KB buffer to maintain low memory overhead.
4. **Automated Naming:** Generates the report file based on the parent folder's name.

## Technical Specifications
- **Report Format:** Markdown (.md)
- **Hashing Standards:** SHA-256 (recommended), SHA-512, MD5
- **UI:** Tkinter-based Graphical User Interface
- **Execution:** Asynchronous threading for UI responsiveness

## Operation Manual
1. **Select Root Folder:** Click "Browse" and choose the main directory of your dataset.
2. **Select Algorithm:** Choose the appropriate hash function (SHA-256 is the archival standard).
3. **Execute:** Click "Generate Integrity Report".
4. **Verification:** Upon completion, a `.md` file is generated inside the root folder. Open this file to verify that all intended files have been hashed correctly.