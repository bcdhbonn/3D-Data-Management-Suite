# 📦 3D Data Management Suite

Welcome to the **3D Data Management Suite**—a collection of specialized Python-based desktop utilities designed for **long-term digital preservation (LZA)**, **data normalization**, and **quality assurance** of 3D datasets.

These tools provide user-friendly graphical interfaces (GUIs based on CustomTkinter) tailored specifically for archivists, researchers, and curators in the Digital Humanities (such as archaeology, heritage conservation, and museology). They simplify complex data validation, renaming, and packaging workflows without requiring programming experience.

---

## 🚀 1. Installation & Setup

To run these tools locally, you need to set up Python and install the required external libraries.

### Step 1: Install Python
1. **Download**: Visit [python.org](https://www.python.org/downloads/) and download the latest version of Python for Windows.
2. **Installation**: Launch the installer.
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

## 🛠️ 2. Tool Overview in the Context of 3D Archiving

Each tool performs a specific, critical task in validating, normalising, and packaging 3D objects for long-term ingestion into research data repositories.

---

### 🔒 Hash-Brownie (Integrity & Consistency Verification)
*   **Directory:** `Hash_Brownie/` | **Entry Script:** `hash_brownie.py`
*   **Significance for Digital Preservation (LZA):**
    During long-term digital preservation, data must be migrated across different storage media (servers, cloud storage, magnetic tapes) over decades. This migration poses a silent threat of data corruption or loss due to transfer errors, bit rot (slow degradation of storage hardware), or accidental modifications. Cryptographic checksums (hashes) serve as a unique digital fingerprint of a file. A hash comparison before and after any data migration provides mathematical proof that the files have remained completely unaltered.
*   **Function**:
    Scans any directory recursively and generates a cryptographic hash value for every single file (SHA-256 is recommended).
*   **How to use**:
    1. Select the **Root Directory** (the target folder to secure).
    2. Choose the cryptographic algorithm (Default: SHA-256).
    3. Click **Generate Integrity Report**.
*   **Output**: A detailed Markdown report named `[FolderName]_hashes.md` inside the scanned directory, documenting all relative paths, file sizes, modification dates, and hash values.

---

### 📐 3D Mesh Analyzer (Metadata Extraction & Geometry Validation)
*   **Directory:** `MeshAnalyzer/` | **Entry Script:** `MeshAnalyzer.py`
*   **Significance for Digital Preservation (LZA):**
    Precise geometric metadata is essential for the indexing and cataloging of 3D datasets. Manually loading high-poly photogrammetry models (often consisting of millions of polygons) into standard CAD or rendering software is extremely time-consuming and frequently freezes systems. Furthermore, archived 3D assets must be validated for geometric integrity: structural holes (non-manifold geometry or lack of watertightness) can prevent models from rendering correctly in future engines or cause failure in 3D printing pipelines.
*   **Function**:
    Instantly extracts geometry data (vertices, faces, bounding boxes, texture references, generator software) from **OBJ, PLY, STL, and GLB** files.
    *   *Super-Fast Mode*: To prevent freezes on massive photogrammetry scans, the tool automatically detects if a file is larger than **25 MB** and bypasses heavy topological checks (watertightness, manifoldness) to parse only core metadata directly from file headers in seconds.
*   **How to use**:
    1. Select the directory containing the 3D files.
    2. Click **Analyze Geometry**.
*   **Output**: 
    *   An interactive GUI table showing all files and their attributes.
    *   An automatic report named `[MeshName]_report.md` (or `[FolderName]_report.md` if multiple models are scanned) written in the target folder. The report formats metrics as clean, vertical 2-column HTML tables with top-aligned texture maps.

---

### 🛠️ GLB Master Manager (Internal Metadata Patcher)
*   **Directory:** `GLB_FileRenamer/` | **Entry Script:** `GLB_FileRenamer.py`
*   **Significance for Digital Preservation (LZA):**
    GLB files (binary glTF) store the names of internal meshes, materials, textures, nodes, and animations inside an internal JSON chunk. When a model file is renamed on disk (e.g., to conform to inventory numbers or institutional naming conventions), these internal names remain set to their old or generic defaults (e.g., *Cube.001* or Blender export templates). This metadata discrepancy causes index mismatch and rendering synchronization issues when loading the files into online database repositories or web viewer platforms.
*   **Function**:
    Analyzes the binary structure of GLB files, opens the JSON chunk, identifies all internal name references, and patch-renames them to synchronize with the current disk filename. The chunk is then padded and re-aligned to bytes before saving.
*   **How to use**:
    1. Select the folder containing GLB files and click **Scan**.
    2. Review the detected internal-external naming discrepancies in the list.
    3. Click **Patch Internal Names** to rewrite internal metadata to sync with disk names.

---

### 🔄 Master File Renamer (File Name Normalization)
*   **Directory:** `FileRenamer/` | **Entry Script:** `FileRenamer.py`
*   **Significance for Digital Preservation (LZA):**
    Inconsistent or cryptic filenames (e.g., `scan_new_final_v2.obj`) are the biggest enemy of structured long-term repositories. To maintain data organization and cross-system referential integrity, filenames must be normalized according to standardized institutional naming schemas (e.g. incorporating inventory numbers or archaeological excavation contexts).
*   **Function**:
    Provides two renaming modes:
    1.  **Smart Sequential Rename**: Standardizes file names by assigning sequential numbering based on the parent folder name (e.g., `Excavation_A_001.jpg`, `Excavation_A_002.jpg`). It runs namespace isolation using temporary UUIDs to prevent collision data overwrites.
    2.  **Dynamic Regex Replace**: Recursively replaces folder and filename patterns using regular expressions (operating bottom-up to ensure directory paths remain valid during execution).
*   **How to use**:
    1. Select the **Root Directory**.
    2. Navigate between tabs to choose your renaming mode.
    3. Generate a **Preview (Show Preview)** to review changes without risk.
    4. Click **Start Renaming**.

---

### 🍪 BAG-ETTE (IETF BagIt Archival Packager)
*   **Directory:** `BAG_ETTE/` | **Entry Script:** `BAG-ETTE.py`
*   **Significance for Digital Preservation (LZA):**
    When delivering research datasets to official digital archives or repositories (such as RADAR, DSpace, or national library databases), packages must conform to strict standardized formats. The **BagIt file packaging format (IETF RFC 8493)** is the global standard for this purpose. A "bag" wraps the actual payload files in a `data/` subdirectory, validates them via manifest files containing SHA-256 hashes of all payloads, and records descriptive archival metadata directly in the package header.
*   **Function**:
    Packages data folders into RFC-8493-compliant BagIt structures.
    *   *YAML/Markdown Metadata Mapping*: Loads descriptive metadata (e.g. inventory codes, author lists, or descriptions) directly from an external header file and maps them to standardized BagIt metadata headers (e.g., `External-Identifier`, `Contact-Name`).
    *   *ZIP Compression*: Offers option to package the generated Bag directory into a ZIP archive for distribution.
*   **How to use**:
    1. Select the source directory (`Source Dir`).
    2. Load your metadata file (`Metadata YAML`).
    3. Select which YAML metadata keys to map into the package header.
    4. Set options (`In-Place` to package directly, or `ZIP Archive` to output a compressed file).
    5. Click **Bake Bag-It Package**.

---

## 🛡️ Archival Safety Guidelines & Best Practices

1. **Keep Backups**: Always create a backup copy of your raw data before running batch renaming (`FileRenamer`) or patching internal binaries (`GLB_FileRenamer`).
2. **End-to-End Hash Validation**: Generate an integrity report with `Hash-Brownie` immediately upon data ingest. Run the validation checks again after copying or migrating data to guarantee zero transmission losses.
3. **Validate Before Packing**: Run the `MeshAnalyzer` before packaging folders with `BAG-ETTE` to intercept damaged model geometries before they are committed to long-term storage.
