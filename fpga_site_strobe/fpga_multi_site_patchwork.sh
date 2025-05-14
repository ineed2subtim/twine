#!/bin/bash

#sites=(CLEM STAR PSC CERN TACC UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI INDI MAX)
sites=(UTAH)

# FPGA experiment listen time in seconds
time=100
# Slice extension, if enabled is extended for 2 days, else the default is 1 day
enable_extend=0

#**#
	#Right now, file creation is relative to the directory housing this file. In future,
	# if we want to use a WORKDIR relative file traversal, this check will be useful 
#**#

#echo "workdir: $WORKDIR"
#if [ -z $WORKDIR ]; then
#	echo "ENV variable WORKDIR is not defined. Please run fabric_pyenv_setup.sh script again!!"
#	exit 1
#fi
if [ -z $sites ]; then
	echo "No SITES specified. Exiting!!!"
	exit 1
fi

echo ${sites[@]} > last_used_sites

allowed_sites=(STAR TACC MICH UTAH NCSA WASH DALL SALT UCSD CLEM LOSA KANS PRIN SRI)

for site in ${sites[@]}; do
	flag=0
	for allowed_site in ${allowed_sites[@]}; do
		if [ $site == $allowed_site ]; then
			flag=1
			break
		fi
	done
	if [ $flag -eq 0 ]; then
		echo "$site does not support Esnet workflow. Skipping!!" 
		continue
	fi
	if [ ! -d $site ]; then
		mkdir -p $site/latest_run
	fi
	if [ -d "$site/latest_run/" ]; then
		rm $site/latest_run/*
	fi
	if [ $enable_extend -eq 1 ]; then
		python3 fpga_mirror_uplink.py $site --time $time --extend &
	else
		python3 fpga_mirror_uplink.py $site --time $time &
	fi
done
