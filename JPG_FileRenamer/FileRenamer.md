# Smart File Renamer Documentation

## Overview
The **Smart File Renamer** is a specialized utility designed to standardize file naming conventions within a directory. It focuses on maintaining perfect sorting and consistency by applying **Dynamic Zero-Padding** based on the actual number of files being renamed.

---

## Features

### 1. Folder-Based Naming
The tool uses the name of the selected folder as the base prefix for all renamed files.
* **Example:** If the folder is named `SK_755_Sirenenrelief`, the files will be named `SK_755_Sirenenrelief_01.jpg`, `SK_755_Sirenenrelief_02.jpg`, etc.

### 2. Dynamic Smart Padding
The number of leading zeros is automatically calculated based on the total file count of the selected type in the folder. This ensures alphabetical sorting is identical to numerical sorting.
* **1 - 9 files:** No padding (`1.jpg`, `2.jpg`)
* **10 - 99 files:** Two digits (`01.jpg`, `02.jpg`)
* **100 - 999 files:** Three digits (`001.jpg`, `002.jpg`)

### 3. File Type Selection
Before renaming, the tool scans the folder and identifies all present file extensions. This allows you to rename only specific groups (e.g., only `.jpg` files) while leaving other files (e.g., `.glb`, `.txt`) untouched.

### 4. Robust Collision Prevention (UUID Isolation)
To prevent Windows errors (like `WinError 183`), the tool uses a two-phase process:
1. **Isolation:** All targeted files are renamed to unique random identifiers (UUIDs) to clear the namespace.
2. **Reconstruction:** Files are then renamed to their final formatted names. This allows you to run the tool multiple times on the same folder without errors.

---

## Usage Instructions

1. **Launch the Script:** Run the Python script.
2. **Select Folder:** Click **'Browse'** and select the folder containing your files.
3. **Select File Type:** Choose the desired extension from the dropdown menu (e.g., `.jpg`).
4. **Start Rename:** Click **'Start Smart Rename'**.
5. **Monitor:** The progress bar and status label will show the current operation. A success message appears when finished.

---

## Requirements
* **Python 3.x**
* Standard libraries: `os`, `uuid`, `tkinter`

---

## Safety Note
> **Backup Recommended:** This tool performs permanent file operations. It is always recommended to have a backup of your data before performing batch renames.
