; ============================================================================
; Powerhouse Commercial-Grade Installer Script
; ============================================================================
; This NSIS script provides professional installation experience
; ============================================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; ============================================================================
; Application Information
; ============================================================================
!define APP_NAME "Powerhouse"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Powerhouse AI"
!define APP_WEB_SITE "https://powerhouse.ai"
!define APP_SUPPORT_URL "https://powerhouse.ai/support"
!define APP_UPDATE_URL "https://powerhouse.ai/updates"
!define APP_EXE "Powerhouse.exe"
!define APP_UNINST "Uninstall.exe"
!define APP_REGKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
!define APP_DIR_REGKEY "Software\${APP_NAME}"

; ============================================================================
; Installer Configuration
; ============================================================================
Name "${APP_NAME}"
OutFile "dist\${APP_NAME} Setup ${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "${APP_DIR_REGKEY}" ""
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

; Compression
SetCompressor /SOLID lzma
SetCompressorDictSize 32

; Version Information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright © ${APP_PUBLISHER}"

; ============================================================================
; Modern UI Configuration
; ============================================================================
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis3-header.bmp"
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APP_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APP_NAME} ${APP_VERSION}.$\r$\n$\r$\n${APP_NAME} is an enterprise-grade multi-agent AI platform.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"
!define MUI_ABORTWARNING

; ============================================================================
; Pages
; ============================================================================
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ============================================================================
; System Requirements Check
; ============================================================================
Function .onInit
    ; Check Windows version (Windows 10 or later)
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_OK|MB_ICONSTOP "This application requires Windows 10 or later.$\r$\nYour system does not meet the minimum requirements."
        Abort
    ${EndIf}
    
    ; Check if already installed
    ReadRegStr $R0 HKLM "${APP_REGKEY}" "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} is already installed. $\n$\nClick `OK` to remove the \
        previous version or `Cancel` to cancel this upgrade." \
        IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        ExecWait '$R0 _?=$INSTDIR'
        
        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:
    
    done:
FunctionEnd

; ============================================================================
; Installation Sections
; ============================================================================
Section "Core Application" SecCore
    SectionIn RO ; Required section
    
    SetOutPath "$INSTDIR"
    
    ; Install main application files
    File /r "resources\app\*.*"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\${APP_UNINST}"
    
    ; Registry entries
    WriteRegStr HKLM "${APP_DIR_REGKEY}" "" $INSTDIR
    WriteRegStr HKLM "${APP_REGKEY}" "DisplayName" "$(^Name)"
    WriteRegStr HKLM "${APP_REGKEY}" "UninstallString" "$INSTDIR\${APP_UNINST}"
    WriteRegStr HKLM "${APP_REGKEY}" "QuietUninstallString" "$INSTDIR\${APP_UNINST} /S"
    WriteRegStr HKLM "${APP_REGKEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${APP_REGKEY}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${APP_REGKEY}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${APP_REGKEY}" "URLInfoAbout" "${APP_WEB_SITE}"
    WriteRegStr HKLM "${APP_REGKEY}" "URLUpdateInfo" "${APP_UPDATE_URL}"
    WriteRegStr HKLM "${APP_REGKEY}" "HelpLink" "${APP_SUPPORT_URL}"
    WriteRegDWORD HKLM "${APP_REGKEY}" "NoModify" 1
    WriteRegDWORD HKLM "${APP_REGKEY}" "NoRepair" 1
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\${APP_UNINST}"
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    
    ; Create data directory
    CreateDirectory "$APPDATA\${APP_NAME}\data"
    CreateDirectory "$APPDATA\${APP_NAME}\logs"
    
    ; Write installation info
    WriteRegStr HKLM "${APP_DIR_REGKEY}" "InstallDate" "$(^GetDate)"
    WriteRegStr HKLM "${APP_DIR_REGKEY}" "Version" "${APP_VERSION}"
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    ; Already created in SecCore, but allow user to choose
SectionEnd

Section "Desktop Shortcut" SecDesktop
    ; Already created in SecCore, but allow user to choose
SectionEnd

; ============================================================================
; Uninstaller
; ============================================================================
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$SMPROGRAMS\${APP_NAME}\*.*"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKLM "${APP_REGKEY}"
    DeleteRegKey HKLM "${APP_DIR_REGKEY}"
    
    ; Remove data (optional - ask user)
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove all ${APP_NAME} data and settings?$\r$\n$\r$\nThis will delete all user data, logs, and configuration files." \
        IDNO skip_data
    RMDir /r "$APPDATA\${APP_NAME}"
    skip_data:
    
    ; Clean up
    SetAutoClose true
SectionEnd

; ============================================================================
; Section Descriptions
; ============================================================================
LangString DESC_SecCore ${LANG_ENGLISH} "Core application files (required)"
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create Start Menu shortcuts"
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create Desktop shortcut"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_SecCore)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
