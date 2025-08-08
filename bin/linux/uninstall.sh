#!/bin/bash

echo Preparing to uninstall components related to Kasson Tool for ViralFusionAnalysis.
echo This program will search for installation of Fiji or ImageJ.
echo If successful, Fiji or ImageJ will start, and the appropriate macros for
echo	uninstallation will be executed with dialog boxes for User actions.
echo If User wishes to uninstall FusionReview from Python, please refer to README.md
echo For manual uninstallaion, please consult README.md

read -n 1 -p "Press any key to continue: "

cd ../..
cd "${PWD}/scripts/ijm"
uninst="${PWD}/uninstall.ijm"
if [ ! "$cfg" ]
then
	exit -1
fi

cd ../..
cd "${PWD}"/log
txt="${PWD}/ijpath.txt"
if [ test -f "$txt" ]
then
	read ij < "$txt"
else
	exit -2
fi
if [ test -f "$ij" ]
then
	"$ij" -macro $uninst
else
	echo WARNING: Cannot find ImageJ/Fiji, program has been moved or deleted!
	read -n 1 -p "Press any key to exit: "
	exit -3
fi
echo ***
echo uninstallation complete
read -n 1 -p "Press any key to exit: "
