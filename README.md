# 📦 3D Data Management Suite

Welcome to the **3D Data Management Suite**—a collection of specialized Python-based desktop utilities designed for digital archiving, batch renaming, 3D metadata extraction, and data integrity verification. These tools are built with a user-friendly graphical interface (GUI) to simplify workflows for users without programming experience.

---

## 🚀 1. Initial Setup (Installation)

To run these tools locally, you need to set up Python and install the required external libraries.

### Step 1: Install Python
1. **Download**: Visit [python.org](https://www.python.org/downloads/) and download the latest version of Python for Windows.
2. **Installation**: Open the installer.
   * **CRITICAL**: Check the box that says **"Add Python to PATH"** at the bottom of the installer window before clicking "Install Now".
3. **Verification**: Open **Command Prompt** (press `Win + R`, type `cmd`, and press Enter) and run:
   ```bash
   python --version
   ```
   If it returns a version number (e.g., `Python 3.x.x`), you are ready to proceed.

### Step 2: Install Required Libraries
Open your **Command Prompt** and install the required dependencies:
```bash
pip install --upgrade customtkinter trimesh[easy] numpy pillow bagit pyyaml
```

---

## 🛠️ 2. Tool Overview & Instructions

### 🔒 Hash-Brownie (Integrity Tool)
*   **Directory:** [Hash_Brownie/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/Hash_Brownie)
*   **File Name:** `hash_brownie.py`
*   **Function**: Scans any directory recursively and generates a cryptographic fingerprint (checksum) for every file to ensure long-term data integrity.
*   **How to use**: Select your **Root Folder**, choose an **Algorithm** (SHA-256 is recommended), and click **Generate Integrity Report**.
*   **Output**: A report named `[FolderName]_hashes.md` inside your scanned folder.

### 📐 3D Mesh Analyzer
*   **Directory:** [MeshAnalyzer/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/MeshAnalyzer)
*   **File Name:** `MeshAnalyzer.py`
*   **Function**: Extracts geometric metadata (number of vertices and faces) from 3D models (e.g., OBJ, STL, GLB, PLY) without loading the visual mesh, preventing freezes on large files.
*   **How to use**: Select the directory containing your 3D assets and click **Analyze Geometry**.

### 🛠️ GLB Master Manager (Internal Patcher)
*   **Directory:** [GLB_FileRenamer/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/GLB_FileRenamer)
*   **File Name:** `GLB_FileRenamer.py`
*   **Function**: Scans GLB files and updates their internal naming metadata (meshes, nodes, materials, animations, skins) to align with their actual disk filename.
*   **How to use**: Select a folder to **Scan**, inspect the names, and click **Patch Internal Names** to synchronize metadata.

### 🔄 Dynamic Regex Replacer
*   **Directory:** [FileRenamer/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/FileRenamer)
*   **File Name:** `FileRenamer.py`
*   **Function**: Recursively renames directories and files using regular expressions. It runs bottom-up to keep folder paths valid during the renaming process.
*   **How to use**: Select the root folder, define a search pattern (e.g., `SK_?755` matches both `SK755` and `SK_755`), specify a replacement string, and click **Start Dynamic Rename**.

### 🔢 Smart File Renamer
*   **Directory:** [JPG_FileRenamer/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/JPG_FileRenamer)
*   **File Name:** `JPG_FileRenamer.py`
*   **Function**: Sequentially numbers files (e.g., textures or documentation photos) using the parent directory name as a prefix, calculating padding digits automatically. It uses UUID-isolation to avoid file collisions or overwrites.
*   **How to use**: Select a folder, choose the file extension type (e.g., `.jpg`), and click **Start Smart Rename**.

### 🍪 BAG-ETTE (Packaging Tool)
*   **Directory:** [BAG_ETTE/](file:///c:/Users/langm/sciebo/BCDH_Projektbox/1_BCDH%20Intern/Scripts/3D%20Data%20Management%20Suite/BAG_ETTE)
*   **File Name:** `BAG-ETTE.py`
*   **Function**: Packages data folders into standardized archival packages using the library-standard **BagIt** format, incorporating metadata loaded directly from a YAML or Markdown header file.
*   **How to use**: Choose your source directory and metadata file, select which fields to import, toggle compression options (`[ZIP_WRAP]` / `[IN_PLACE]`), and click **[ BAKE BAG-ETTE ]**.

---

## 🛡️ Archival Safety Guidelines
*   **Backups**: Always keep a backup copy of your data directories before running batch renaming (`FileRenamer`, `JPG_FileRenamer`) or patching internal metadata (`GLB_FileRenamer`).
*   **Integrity Reports**: We recommend generating a `Hash-Brownie` integrity report *before* and *after* moving files to ensure no data is lost or altered during transfers.
