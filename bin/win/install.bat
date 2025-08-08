@echo off
CALL :commentary
:commentary
(
	echo This is the batch file for the semi-automated installation of KassonLab_MicroscopyPlugin!
	echo	author: Marcos Cervants
	echo	emails: marcerv12@gmail.com, mc2mn@virginia.edu
	echo The program will search for installation of Fiji and Python
	echo If successful, Fiji will start, the appropriate macros will be installed,
	echo	and dialog boxes should prompt the User for actions.
	echo If Fiji cannot be found, a web browser will open to prompt download.
	echo If Python3 cannot be found, a web browser will open to prompt download.
	echo If necessary Python packages cannot be found, these will also be downloaded.
	echo For a complete list of all dependencies, please consult README.md
	echo For manual installaion, please consult README.md
)

PAUSE

setlocal EnableDelayedExpansion
cd ..\..
SET kassonlibdir="%cd%"\
cd \

python --version
if not %ERRORLEVEL% EQU 0 (
	start https://www.python.org/downloads/
) else (
	CALL :pycheck
)

:pycheck
	python -m pip install trace-reviewer

echo Searching for Fiji...
cd %USERPROFILE%
for /f "delims=" %%f in ('dir /s /b ImageJ*.exe') do (
	for %%a in (%%f) do (
		for %%b in ((%%~dpa\.) do (
			if %%~nxb EQU Fiji.app (
				SET fijidir="%cd%"\
				SET fiji="%%f"
				echo ***
				echo found Fiji - hooray!
				echo ***
			)
		)
	)
)

PAUSE

if not exist %fiji% (
	start https://imagej.net/software/fiji/downloads
) else (
	robocopy %kassonlibdir%KassonLab_MicroscopyPlugin %fijidir%plugins /KassonLab_MicroscopyPlugin
)

echo *** Installation successful ***
PAUSE

endlocal
exit 0
