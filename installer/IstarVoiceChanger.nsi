; Istar Voice Changer - NSIS Installer Script (MIT)
; Builds a professional Windows installer with Start Menu shortcut + uninstaller.
;
; Requirements:
;   - NSIS installed (https://nsis.sourceforge.io/)
;   - dist/IstarVoiceChanger.exe built by build_installer.py
;
; Build:
;   makensis installer\IstarVoiceChanger.nsi

!define APPNAME "Istar Voice Changer"
!define APPVERSION "1.0.0"
!define PUBLISHER "Istar Voice Changer"
!define EXE "IstarVoiceChanger.exe"

; Resolve the EXE path relative to this script's parent directory so the build
; works no matter the current working directory.
!define SRC_DIR ".."

; ---- installer basics ----
Name "${APPNAME}"
OutFile "${SRC_DIR}\dist\IstarVoiceChanger-Setup.exe"
InstallDir "$LOCALAPPDATA\${APPNAME}"
InstallDirRegKey HKCU "Software\${APPNAME}" "InstallDir"
RequestExecutionLevel user
Unicode True

; ---- pages ----
Page directory
Page instfiles

; ---- version info ----
VIProductVersion "${APPVERSION}.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "FileVersion" "${APPVERSION}"
VIAddVersionKey "LegalCopyright" "(c) ${PUBLISHER} - MIT"

Section "Install"
  SetOutPath "$INSTDIR"
  File "${SRC_DIR}\dist\${EXE}"

  ; Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\${APPNAME}" "InstallDir" "$INSTDIR"

  ; Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${EXE}"
  CreateShortcut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

  ; Desktop shortcut
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${EXE}"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\${EXE}"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\${APPNAME}"
SectionEnd
