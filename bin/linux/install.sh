#!/bin/bash

echo This is the batch file for the semi-automated installation of ViralFusionAnalysis for the Kasson Lab!
echo author: Marcos Cervants
echo emails: marcerv12@gmail.com, mc2mn@virginia.edu
echo If Python3 cannot be found, a message will appear with URL to download.
echo If necessary Python packages cannot be found, these will also be downloaded via pip.
echo User will be prompted to input ImageJ/Fiji path, and be provided URL to download.
echo For a complete list of all dependencies, please consult README.md
echo For manual installaion, please consult README.md

read -n 1 -p "Press any key to continue: "

cd ../..
kassonlibdir="${PWD}/"
cd "${PWD}/scripts/ijm"
cfg="${PWD}/config.ijm"
if [ ! "$cfg" ]
then
	read -n 1 -p "Something went horribly wrong, please consult UserGuide for manual install, press any key to exit...";
	exit -1
fi
stp="${PWD}/setup.ijm"
if [ ! "$stp" ]
then
        read -n 1 -p "Something went horribly wrong, please consult UserGuide for manual install, press any key to exit...";
	exit -2
fi

cd

python3 --version
if [ $? == 0 ]
then
        sudo apt install python3-pip
        python3 -m pip install --upgrade pip
        python3 -m pip install numpy
        python3 -m pip install matplotlib
        python3 -m pip install pandas
        python3 -m pip install imageio
	python3 -m pip install ruptures
	python3 -m pip install tqdm
	python3 -m pip install pygetwindow
        python3 -m pip install fusion_review
else
        echo ***
        echo please get Python3: https://www.python.org/downloads/
        read -n 1 -p "Press press any key to exit and try again...";
	exit -3
fi

echo ***
echo If Fiji is not on this machine, please download and install: https://imagej.net/software/fiji/downloads
read -p "Please enter Fiji application path: " fiji
if [ ! "$fiji" ]
then
       read -n 1 -p "Cannot verify existence of file, please consult UserGuide for manual install, press any key to exit..."
       exit -4
else
	$fiji>>$kassonlibdirlog/ijpath.txt
        $fiji --headless -macro "$cfg" "$stp"
        $fiji -macro $stp $kassonlibdir
fi
