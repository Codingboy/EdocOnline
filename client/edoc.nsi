SetCompressor /SOLID /FINAL lzma

!include "FileFunc.nsh"
!define StrRep "!insertmacro StrRep"
!macro StrRep output string old new
    Push `${string}`
    Push `${old}`
    Push `${new}`
    !ifdef __UNINSTALL__
        Call un.StrRep
    !else
        Call StrRep
    !endif
    Pop ${output}
!macroend
 
!macro Func_StrRep un
    Function ${un}StrRep
        Exch $R2 ;new
        Exch 1
        Exch $R1 ;old
        Exch 2
        Exch $R0 ;string
        Push $R3
        Push $R4
        Push $R5
        Push $R6
        Push $R7
        Push $R8
        Push $R9
 
        StrCpy $R3 0
        StrLen $R4 $R1
        StrLen $R6 $R0
        StrLen $R9 $R2
        loop:
            StrCpy $R5 $R0 $R4 $R3
            StrCmp $R5 $R1 found
            StrCmp $R3 $R6 done
            IntOp $R3 $R3 + 1 ;move offset by 1 to check the next character
            Goto loop
        found:
            StrCpy $R5 $R0 $R3
            IntOp $R8 $R3 + $R4
            StrCpy $R7 $R0 "" $R8
            StrCpy $R0 $R5$R2$R7
            StrLen $R6 $R0
            IntOp $R3 $R3 + $R9 ;move offset by length of the replacement string
            Goto loop
        done:
 
        Pop $R9
        Pop $R8
        Pop $R7
        Pop $R6
        Pop $R5
        Pop $R4
        Pop $R3
        Push $R0
        Push $R1
        Pop $R0
        Pop $R1
        Pop $R0
        Pop $R2
        Exch $R1
    FunctionEnd
!macroend
!insertmacro Func_StrRep ""
!insertmacro Func_StrRep "un."

Name "Edoc"
OutFile "setup.exe"
RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\Edoc"
InstallDirRegKey HKCU "Software\Edoc" ""

!include "MUI2.nsh"

!define MUI_ICON "img\logo.ico"
!define MUI_HEADERIMAGE
!define MUI_ABORTWARNING
#!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_LANGDLL_ALLLANGUAGES
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\Edoc"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "German"
#!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_RESERVEFILE_LANGDLL
Function .onInit
	!insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd
Function un.onInit
	!insertmacro MUI_UNGETLANGUAGE
FunctionEnd

Section "Edoc" Edoc
	SetAutoClose true
	SetOutPath $INSTDIR
	File /r img
	File edoc.py
	File LICENSE.txt
	File README.md
	Var /GLOBAL pathToExe
	StrCpy "$pathToExe" "$INSTDIR\edoc.py"
	${StrRep} $pathToExe "$pathToExe" "\" "\\"
	#WriteRegStr HKCR "Directory\Background\shell\EncodeStr\command" "" "python $\"$pathToExe$\" -e"
	#WriteRegExpandStr HKCR "Directory\Background\shell\EncodeStr" "Icon" "$INSTDIR\img\encode.ico"
	#WriteRegStr HKCR "Directory\Background\shell\DecodeStr\command" "" "python $\"$pathToExe$\" -d"
	#WriteRegExpandStr HKCR "Directory\Background\shell\DecodeStr" "Icon" "$INSTDIR\img\decode.ico"
	WriteRegStr HKCR "*\shell\Encode\command" "" "python $\"$pathToExe$\" -e -f $\"%1$\""
	WriteRegExpandStr HKCR "*\shell\Encode" "Icon" "$INSTDIR\img\encode.ico"
	WriteRegStr HKCR "Directory\shell\Encode\command" "" "python $\"$pathToExe$\" -e -f $\"%1$\""
	WriteRegExpandStr HKCR "Directory\shell\Encode" "Icon" "$INSTDIR\img\encode.ico"
	WriteRegStr HKCR ".edoc\shell\Decode\command" "" "python $\"$pathToExe$\" -d -f $\"%1$\""
	WriteRegExpandStr HKCR ".edoc\shell\Decode" "Icon" "$INSTDIR\img\decode.ico"
	WriteUninstaller "$INSTDIR\uninstall.exe"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "DisplayName" "Edoc"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "NoModify" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "NoRepair" 1
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "DisplayIcon" "$INSTDIR\edoc.py"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "InstallLocation" "$INSTDIR"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "Publisher" "Daniel Tkocz"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "Readme" "$INSTDIR\README.md"
	${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
	IntFmt $0 "0x%08X" $0
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "EstimatedSize" "$0"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc" "Contact" "daniel.tkocz42@gmail.com"
SectionEnd

Section /o "Development Files" DevFiles
	SetAutoClose true
	SetOutPath $INSTDIR
	File edoc.nsi
	#File Doxyfile
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${Edoc} "This option will install the absolute minimum required files to use Edoc."
!insertmacro MUI_DESCRIPTION_TEXT ${DevFiles} "This option will install all further files needed to develop and build. This option is intended for developers/programmer only."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "un.Edoc"
	SetAutoClose true
	#DeleteRegKey HKCR "Directory\Background\shell\EncodeStr"
	#DeleteRegKey HKCR "Directory\Background\shell\DecodeStr"
	DeleteRegKey HKCR "*\shell\Encode"
	DeleteRegKey HKCR "Directory\shell\Encode"
	DeleteRegKey HKCR ".edoc"
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Edoc"
	DeleteRegKey HKCU "Software\Edoc"
	RMDir /r $INSTDIR
SectionEnd