Unicode true
!include "installer_version.nsh"
!include "MUI2.nsh"
!include "LogicLib.nsh"
Name "CrossHud Setup"
OutFile "dist\${APP_NAME}_Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
RequestExecutionLevel admin
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!define MUI_PAGE_CUSTOMFUNCTION_SHOW DisableBrowseButton
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Russian"
Function DisableBrowseButton
  FindWindow $0 "#32770" "" $HWNDPARENT
  GetDlgItem $1 $0 1019
  EnableWindow $1 0
  GetDlgItem $1 $0 1001
  EnableWindow $1 0
  GetDlgItem $1 $0 1006
  SendMessage $1 0x000C 0 "STR:Для корректной работы поверх всех окон и игр программа$\r$\nОБЯЗАНА находиться в системной папке Program Files.$\r$\n$\r$\nИзменение пути установки заблокировано для вашей$\r$\nбезопасности и гарантии работоспособности всех функций."
FunctionEnd
Section "Основное приложение" SEC_MAIN
  SectionIn RO
  nsExec::ExecToStack 'taskkill /F /IM "${EXE_NAME}"'
  Pop $0
  Pop $1
  nsExec::ExecToStack 'taskkill /F /IM "CrossHud_By_PetyaBlatnoy.exe"'
  Pop $0
  Pop $1
  IfFileExists "$PROGRAMFILES64\${APP_NAME}\${EXE_NAME}" 0 +2
    RMDir /r "$PROGRAMFILES64\${APP_NAME}"
  IfFileExists "$PROGRAMFILES\${APP_NAME}\${EXE_NAME}" 0 +2
    RMDir /r "$PROGRAMFILES\${APP_NAME}"
  IfFileExists "$PROGRAMFILES64\CrossHud_By_PetyaBlatnoy\CrossHud_By_PetyaBlatnoy.exe" 0 +2
    RMDir /r "$PROGRAMFILES64\CrossHud_By_PetyaBlatnoy"
  IfFileExists "$PROGRAMFILES\CrossHud_By_PetyaBlatnoy\CrossHud_By_PetyaBlatnoy.exe" 0 +2
    RMDir /r "$PROGRAMFILES\CrossHud_By_PetyaBlatnoy"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$DESKTOP\CrossHud_By_PetyaBlatnoy.lnk"
  Delete "$DESKTOP\Crosshud_By_Petyablatnoy-HudsightKiller.lnk"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"
  RMDir /r "$SMPROGRAMS\CrossHud_By_PetyaBlatnoy"
  RMDir /r "$SMPROGRAMS\Crosshud_By_Petyablatnoy-HudsightKiller"
  SetOutPath "$INSTDIR"
  File /r "dist\${APP_NAME}\*.*"
  File "dist\CrossHudCert.cer"
  nsExec::ExecToStack 'certutil.exe -addstore "Root" "$INSTDIR\CrossHudCert.cer"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Не удалось добавить сертификат в доверенные корневые центры.$\r$\nКод: $0$\r$\n$1"
    Abort
  ${EndIf}
  nsExec::ExecToStack 'certutil.exe -addstore "TrustedPublisher" "$INSTDIR\CrossHudCert.cer"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Не удалось добавить сертификат в доверенные издатели.$\r$\nКод: $0$\r$\n$1"
    Abort
  ${EndIf}
  nsExec::ExecToStack `powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$$sig = Get-AuthenticodeSignature -FilePath '$INSTDIR\${EXE_NAME}'; if ($$sig.Status -ne 'Valid') { exit 1 }"`
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Подпись приложения не прошла проверку после установки.$\r$\nКод: $0$\r$\n$1"
    Abort
  ${EndIf}
  Delete "$INSTDIR\CrossHudCert.cer"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CrossHud_By_PetyaBlatnoy"
  IfSilent 0 +2
    Exec '"$INSTDIR\${EXE_NAME}"'
SectionEnd
Section "Ярлык на рабочем столе" SEC_DESKTOP
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
SectionEnd
Section "Ярлыки в меню Пуск" SEC_STARTMENU
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${EXE_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\Удалить.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd
LangString DESC_SEC_MAIN ${LANG_RUSSIAN} "Основные файлы приложения."
LangString DESC_SEC_DESKTOP ${LANG_RUSSIAN} "Создать ярлык на рабочем столе."
LangString DESC_SEC_STARTMENU ${LANG_RUSSIAN} "Создать ярлыки в меню Пуск."
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MAIN} $(DESC_SEC_MAIN)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} $(DESC_SEC_DESKTOP)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} $(DESC_SEC_STARTMENU)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
Section "Uninstall"
  nsExec::ExecToStack 'taskkill /F /IM "${EXE_NAME}"'
  Pop $0
  Pop $1
  nsExec::ExecToStack 'certutil.exe -delstore "Root" "CrossHud_Permanent_Cert"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    DetailPrint "Не удалось удалить сертификат из Root: $0 $1"
  ${EndIf}
  nsExec::ExecToStack 'certutil.exe -delstore "TrustedPublisher" "CrossHud_Permanent_Cert"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    DetailPrint "Не удалось удалить сертификат из TrustedPublisher: $0 $1"
  ${EndIf}
  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$DESKTOP\Crosshud_By_Petyablatnoy-HudsightKiller.lnk"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"
  RMDir /r "$SMPROGRAMS\Crosshud_By_Petyablatnoy-HudsightKiller"
  StrCpy $2 "0"
  ${If} "$INSTDIR" == "$PROGRAMFILES64\${APP_NAME}"
    StrCpy $2 "1"
  ${EndIf}
  ${If} "$INSTDIR" == "$PROGRAMFILES\${APP_NAME}"
    StrCpy $2 "1"
  ${EndIf}
  ${If} $2 == "1"
  ${AndIf} ${FileExists} "$INSTDIR\${EXE_NAME}"
  ${AndIf} ${FileExists} "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
  ${Else}
    DetailPrint "Каталог установки не удален: путь или файлы не прошли проверку безопасности."
  ${EndIf}
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  MessageBox MB_YESNO "Удалить ваши настройки и профили прицелов?" IDNO +2
  RMDir /r "$PROFILE\CrossHud"
  RMDir /r "$PROFILE\CrossHud_By_PetyaBlatnoy"
SectionEnd
