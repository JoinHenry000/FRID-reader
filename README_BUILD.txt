
RFID Reader — Build for Windows (GitHub Actions)

This package contains:
- rfid_reader.py        : Python GUI application (reads tags like E200...)
- requirements.txt
- .github/workflows/build-windows.yml : GitHub Actions workflow to build a Windows .exe

How to get a ready exe using GitHub Actions:
1. Create a new GitHub repository (private or public).
2. Upload the files from this package to the repository root (keep the .github folder).
3. Push to GitHub (branch main). Then in the Actions tab, run the "Build Windows EXE" workflow or push to trigger it.
4. When the workflow completes, download the artifact `rfid_reader_windows_exe` containing `rfid_reader.exe`.

How to build locally on Windows:
1. Install Python 3.8+ and Git.
2. Open Command Prompt in the folder and run:
   pip install pyinstaller pyserial
   pyinstaller --onefile --windowed rfid_reader.py
3. Find the exe under the `dist` folder: dist\rfid_reader.exe

Usage:
- Run rfid_reader.exe on Windows 11.
- Select COM port (e.g., COM5), set baud (9600), click Start.
- Scan tags — they should look like: E2000017221101441890A1B3
- The app shows unique tags and total count. Click Clear to reset.

If you want, I can also build the exe for you (I will provide a GitHub repo and run Actions) — but I cannot push to your GitHub account without your permission.
