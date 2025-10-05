# 🔒 LLVM-Based Code Obfuscation Tool

## 🧠 Overview
This project is a **software obfuscation tool** built using **LLVM (Low Level Virtual Machine)**.  
It is designed to protect **intellectual property**, **prevent reverse engineering**, and **mitigate software piracy** by generating obfuscated binaries that are extremely difficult to decompile or understand.

The tool takes **C/C++ source code**, compiles it via LLVM, applies **multiple obfuscation passes**, and generates an obfuscated **binary** for both **Windows** and **Linux** platforms.  
It also generates a **detailed report** describing the obfuscation process and metrics.

---

## 🚀 Features
- 🧩 **Multi-pass Obfuscation** using LLVM IR transformations
- 🔐 **String Encryption**, **Bogus Code Insertion**, and **Control Flow Flattening**
- ⚙️ **Configurable Parameters** to control obfuscation intensity
- 📄 **Comprehensive Report** including:
  - Input parameters used  
  - Output file attributes (size, hash, methods used)  
  - Bogus code count  
  - Number of obfuscation cycles  
  - String encryption stats  
  - Fake loop insertions  
- 🧰 **Cross-platform binary output** (Windows/Linux)
- 🧾 Auto-generated report in `.txt` and `.html` formats

---

## 🧰 Tech Stack
- **Language:** Python, C/C++  
- **Compiler Infrastructure:** LLVM  
- **Build System:** CMake + MinGW / Clang  
- **Frameworks:** FastAPI (for backend)  
- **Platform:** Windows & Linux

---

## 📦 Project Structure

```
backend/
├── main.py                     # FastAPI server entry point
├── obfuscate.py                # Core obfuscation logic
├── run_advanced_obfuscation.py # Multi-pass obfuscation manager
├── src                         # C++ backend files
└── build/                      # Build output directory
frontend/                       Frontend for web usage
reports/
├── obfuscation_report.txt
└── comprehensive_obfuscation_report.html
```

---

## ⚙️ Installation & Setup

### 🔧 Prerequisites
Ensure the following are installed:
- **LLVM** (>= 15)
- **CMake**
- **MinGW / Clang**
- **Python 3.9+**
- **pip packages**:  
  ```bash
  pip install -r requirements.txt
  ```

### 🧱 Build Steps
```bash
# Clone the repository
git clone <your_repo_url>
cd backend

# Create build directory
mkdir build && cd build

# Configure CMake
cmake ..

# Build the project
mingw32-make   # or 'make' on Linux
```

If `mingw32-make` doesn’t work, ensure:
- You’re inside `backend/build`
- `CMakeLists.txt` exists in `../`
- LLVM and MinGW are correctly installed and added to PATH

---

## ▶️ Usage

### 🧑‍💻 Run via Backend API
```bash
cd backend
python main.py
```
Then open:  
➡️ http://127.0.0.1:8000/docs  
Upload your C/C++ file and run obfuscation.

---

### 💻 Run via CLI
```bash
cd python
python obf_cli.py --input path/to/source.c --output obfuscated.exe --passes 3
```

Example:
```bash
python obf_cli.py --input hello.c --passes 2 --string-encryption True
```

---

## 📊 Output
After successful execution, you’ll get:
1. **Obfuscated Binary**
   - `output/obfuscated_<timestamp>.exe` (Windows)
   - `output/obfuscated_<timestamp>` (Linux)

2. **Report Files**
   - `reports/obfuscation_report.txt`
   - `reports/comprehensive_obfuscation_report.html`

---

## 📝 Example Report Snippet

```
🔐 LLVM Obfuscation Report
===========================
Input File: hello.c
Output Binary: obfuscated_2025.exe
Obfuscation Passes: 3
String Encryptions: 12
Bogus Code Inserted: 54 lines
Fake Loops: 8
Final Binary Size: 1.2 MB
```

---

## 🧪 Debugging & Logging
You can toggle debug messages in `obfuscate.py` or `run_advanced_obfuscation.py`:
```python
DEBUG_MODE = True
```

All debug prints are wrapped using:
```python
debug_print("Message")
```
so you can easily silence them when not needed.

---

## 📄 Expected Output Files
| File | Description |
|------|--------------|
| `obfuscated_<name>.exe` | Final obfuscated binary |
| `obfuscation_report.txt` | Text report |
| `comprehensive_obfuscation_report.html` | Detailed HTML report |

---

## 🧰 Troubleshooting

| Issue | Possible Fix |
|-------|---------------|
| `mingw32-make: command not found` | Add MinGW to PATH |
| `CMake Error: CMakeLists.txt missing` | Run from `build/` folder |
| No output binary | Check console logs for errors, ensure LLVM linked |
| Too many debug prints | Set `DEBUG_MODE = False` |

---
