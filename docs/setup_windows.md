# Windows Setup and Troubleshooting Guide: SOLARIS-A1

## Overview
This document provides instructions for setting up the local Python virtual environment for `SOLARIS-A1` on Windows, along with solutions to common Windows-specific platform issues.

---

## 1. Prerequisites
- **Operating System:** Windows 10 or Windows 11 (64-bit).
- **Python:** Python 3.10, 3.11, or 3.12 (standard official distribution from python.org or Microsoft Store). Ensure "Add Python to PATH" was selected during installation.
- **Git:** Git for Windows.

---

## 2. Step-by-Step PowerShell Setup

Execute the following commands from the root directory of `SOLARIS-A1`:

### Step 2.1: Open PowerShell and Navigate to Workspace
```powershell
cd C:\Users\melvi\Desktop\SOLARIS-A1
```

### Step 2.2: Create the Virtual Environment
Create an isolated Python virtual environment named `.venv`:
```powershell
python -m venv .venv
```

### Step 2.3: Configure Script Execution Policy (Scoped)
Windows PowerShell may block script execution by default, producing an error such as:
> `File ...\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`

**Do NOT disable security globally.** Instead, set the execution policy specifically for the current PowerShell process session:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```
*Note: This setting applies only to your active terminal window and automatically resets when the window closes.*

### Step 2.4: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
Upon activation, your PowerShell prompt will show the prefix `(.venv)`.

### Step 2.5: Upgrade Pip
```powershell
python -m pip install --upgrade pip
```

### Step 2.6: Install Project Dependencies
Install all core and development packages:
```powershell
python -m pip install -r requirements-dev.txt
```

### Step 2.7: Run Environment Verification
Run the verification script to validate package imports, directory structure, and configuration loading:
```powershell
python scripts/verify_environment.py
```

### Step 2.8: Run Test Suite
Confirm that all unit tests pass:
```powershell
python -m pytest -v
```

---

## 3. Windows-Specific Troubleshooting Notes

### 3.1 PowerShell Execution Policy Errors
- **Symptom:** `Activate.ps1 cannot be loaded because running scripts is disabled`.
- **Cause:** Windows default `Restricted` execution policy for scripts.
- **Resolution:** Execute `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`. If using Command Prompt (`cmd.exe`) instead of PowerShell, activate using `.\.venv\Scripts\activate.bat` which does not require PowerShell script permissions.

### 3.2 Windows Long Path Limit (MAX_PATH)
- **Symptom:** Errors when pip installs packages with deeply nested directory structures, or file not found errors during build steps.
- **Cause:** Standard Windows filesystem default limits path lengths to 260 characters.
- **Resolution:** Enable Win32 Long Paths in an elevated Administrator PowerShell prompt:
  ```powershell
  Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
  ```

### 3.3 Terminal Character Encoding (UTF-8)
- **Symptom:** `UnicodeEncodeError` when scripts print UTF-8 characters to the PowerShell console.
- **Resolution:** Set the console code page to UTF-8 before running scripts:
  ```powershell
  chcp 65001
  $OutputEncoding = [System.Text.UTF8Encoding]::new()
  ```

### 3.4 Antivirus File Locking
- **Symptom:** `PermissionError: [WinError 5] Access is denied` during `pip install` or virtualenv creation when replacing files in `.venv\Lib\site-packages\`.
- **Cause:** Windows Defender or third-party real-time scanning momentarily locking `.dll` or `.pyd` binaries.
- **Resolution:** Re-run the install command, or temporarily add the project `.venv` folder to your antivirus scan exclusion list.
