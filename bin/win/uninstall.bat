@echo off
CALL :commentary
:commentary
(
	echo Preparing to uninstall components related to KassonLab_MicroscopyPlugin.
	echo This program will search for installation of Fiji.
	echo If successful, the subdirectory ..\Fiji.app\plugins\KassonLab_MicroscopyPlugin\
	echo	will be deleted.
	echo If User wishes to uninstall trace-reviewer from Python, please refer to README.md
	echo For manual uninstallaion, please consult README.md
)

PAUSE

setlocal EnableDelayedExpansion

echo Searching for Fiji...
cd %USERPROFILE%
for /f "delims=" %%f in ('dir /s /b ImageJ*.exe') do (
	for %%a in (%%f) do (
		for %%b in ((%%~dpa\.) do (
			if %%~nxb EQU Fiji.app (
				SET fijidir="%cd%"\
			)
		)
	)
)

PAUSE

if not exist %fijidir% (
	echo WARNING: Cannot find Fiji, program has been moved or deleted!
	PAUSE
	exit -1
) else (
	if not exist %fijidir%plugins\KassonLab_MicroscopyPlugin (
		echo WARNING: Cannot find plugin...
	)
	else (
		rmdir /s /q %fijidir%plugins\KassonLab_MicroscopyPlugin\
	)
)

echo ***
echo uninstallation complete
PAUSE
endlocal
exit 0