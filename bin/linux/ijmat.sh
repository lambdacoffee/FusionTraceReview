#!/bin/bash

klib=$1
xtrxn="$klibscripts/mat/automation/main.m"
txt="$kliblog/binmatlabpath.txt"
if [ test -f "$txt" ]
then
	read mat < "$txt"
	"$mat" -nosplash -r "run(\"$xtrxn\")"
else
	exit -1
fi
exit 0

