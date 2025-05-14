#!/bin/bash

#sites=(CLEM STAR PSC CERN TACC UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI INDI MAX)
#sites=(TACC MICH)

sites+=($(cat last_used_sites))

echo ${sites[@]}

echo "workdir: $WORKDIR"
if [ -z $WORKDIR ]; then
	echo "ENV variable WORKDIR is not defined. Please run fabric_pyenv_setup.sh script again!!"
	exit 1
fi
if [ -z $sites ]; then
	echo "No SITES specified. Exiting!!!"
	exit 1
fi

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
	if [ -d "$site/latest_run/" ]; then
		if [ -d "$site/output" ]; then
			cp -r $site/output/ $site/latest_run/
		fi
	fi
	python3 fpga_mirror_uplink_cleanup.py $site
done
