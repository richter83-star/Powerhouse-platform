================================================================
   POWERHOUSE - INSTALLATION FIX
================================================================

THE PROBLEM YOU SAW:
"The system cannot find the path specified" error during 
Python package installation.

THE SOLUTION:
Use the new INSTALL_FIXED_V2.bat which has better path handling
and provides detailed diagnostics.


STEP 1: RUN DIAGNOSTICS FIRST
================================================================

Before installing, run this:

    DIAGNOSE.bat

This will check:
- If all folders are in the right place
- If Python, Node.js, and Docker are properly installed
- If you can access the backend/frontend folders
- Current installation status

This will tell you exactly what's wrong!


STEP 2: USE THE FIXED INSTALLER
================================================================

Once diagnostics show everything is OK, run:

    INSTALL_FIXED_V2.bat

This version:
- Uses better Windows path handling (pushd/popd)
- Checks folder existence before accessing them
- Provides detailed error messages
- Creates a full log file


COMMON ISSUES AND FIXES:
================================================================

Issue: "Cannot find backend folder"
Fix: 
  - Make sure you extracted the FULL zip file
  - Don't run from inside a subfolder
  - The batch file must be in the same folder as "backend" and "frontend"

Issue: "Python not found in PATH"  
Fix:
  - Reinstall Python
  - Check "Add Python to PATH" during installation
  - Restart your computer
  - Run: python --version (should work)

Issue: "Node.js not found in PATH"
Fix:
  - Reinstall Node.js (LTS version)
  - Restart your computer  
  - Run: node --version (should work)

Issue: "Failed to install Python packages"
Fix:
  - Check internet connection
  - Try running as Administrator (right-click > Run as Administrator)
  - Check if antivirus/firewall is blocking pip
  - Look at install_log.txt for the specific package that failed


RECOMMENDED EXTRACTION PATH:
================================================================

Extract the zip to a SIMPLE path without spaces:

GOOD:
  C:\Powerhouse\
  D:\Apps\Powerhouse\
  C:\Users\YourName\Desktop\Powerhouse\

BAD:
  C:\Program Files (x86)\Powerhouse\  (spaces and special chars)
  C:\Users\YourName\My Documents\folder with spaces\Powerhouse\


INSTALLATION ORDER:
================================================================

1. DIAGNOSE.bat         - Check your system
2. INSTALL_FIXED_V2.bat - Install everything
3. 1_START_DATABASE.bat - Start PostgreSQL
4. 2_START_BACKEND.bat  - Start Python API
5. 3_START_FRONTEND.bat - Start Next.js web app

Then open: http://localhost:3000


IF IT STILL FAILS:
================================================================

1. Run DIAGNOSE.bat and take a screenshot
2. Run INSTALL_FIXED_V2.bat and let it fail
3. Open install_log.txt
4. Find the FIRST [ERROR] line
5. Send me:
   - Screenshot of DIAGNOSE.bat results
   - The [ERROR] line from install_log.txt
   - What folder you extracted to


WHAT'S FIXED IN THIS VERSION:
================================================================

- Better path handling using %~dp0 and pushd/popd
- Pre-checks folder existence before accessing
- More detailed error messages
- Full diagnostic tool (DIAGNOSE.bat)
- Absolute paths for log files
- Better error recovery


QUICK START:
================================================================

1. Extract this zip to: C:\Powerhouse\
2. Double-click: DIAGNOSE.bat
3. If all checks pass, double-click: INSTALL_FIXED_V2.bat
4. Wait for installation to complete
5. Follow the "To start Powerhouse" instructions

That's it!

================================================================
