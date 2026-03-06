; ==========================================================
; ⚽ SPORTS AI - PACHECO RUAA EDITION INSTALLER
; ==========================================================

!include "MUI2.nsh"
!include "nsDialogs.nsh"

Name "Sports AI - Pacheco Ruaa Edition"
OutFile "SportsAI_Setup.exe"
InstallDir "$PROGRAMFILES\SportsAI"
RequestExecutionLevel admin

; Branding
!define MUI_WELCOMEFINISHPAGE_BITMAP "loro.png"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "loro.png"

; ----------------------------------------------------------
; Custom Pages
; ----------------------------------------------------------

Var Dialog
Var Label
Var Text
Var Response

Page Custom DedicationPage
Page Custom QuestionPage
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

Function DedicationPage
    nsDialogs::Create 1018
    Pop $Dialog

    ${NSD_CreateLabel} 0 10u 100% 40u "DEDICADO A YEISON VELASQUEZ, ALIAS PACHECO RUAA"
    Pop $Label
    SendMessage $Label ${WM_SETFONT} ${MUI_FONT_HEADER} 0

    ${NSD_CreateBitmap} 0 60u 100% 80u "loro.png"
    Pop $Text ; Just a placeholder for the bitmap

    nsDialogs::Show
FunctionEnd

Function QuestionPage
    nsDialogs::Create 1018
    Pop $Dialog

    ${NSD_CreateLabel} 0 10u 100% 20u "¿no te gusta el color de tu ano?"
    Pop $Label

    ${NSD_CreateText} 0 40u 100% 12u ""
    Pop $Text
    
    ${NSD_OnChange} $Text OnInputChange

    ; Disable next button until correct answer
    GetDlgItem $0 $HWNDPARENT 1
    EnableWindow $0 0

    nsDialogs::Show
FunctionEnd

Function OnInputChange
    ${NSD_GetText} $Text $Response
    
    ; Answer is case insensitive check for "si" or "no" or anything the user wants? 
    ; The request says "pregúntale... para poder avanzar", usually implies a specific answer or just any input.
    ; Let's make it accept "si" or "no" (or anything non-empty to be safe and let them pass)
    ; But let's be funny and require "me encanta" or just any response.
    
    GetDlgItem $0 $HWNDPARENT 1
    ${If} $Response != ""
        EnableWindow $0 1
    ${Else}
        EnableWindow $0 0
    ${EndIf}
FunctionEnd

; ----------------------------------------------------------
; Installation
; ----------------------------------------------------------

Section "Main"
    SetOutPath "$INSTDIR"
    File /r "dist\*.*" ; We will put the compiled backend/frontend here
    
    ; Create Shortcuts
    CreateShortCut "$DESKTOP\Sports AI.lnk" "$INSTDIR\SportsAI_Runner.exe" "" "$INSTDIR\loro.png" 0
SectionEnd
