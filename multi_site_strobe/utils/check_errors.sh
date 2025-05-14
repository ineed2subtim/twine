#!/bin/bash

sites=()
logfile="startup_log.txt"

sites_used_last=$(cat sites_used_last_experiment | wc -l)
if [ $sites_used_last -ne 0 ]; then
	sites+=($(cat sites_used_last_experiment))
fi

#** If user wants to overwrite the sites to be used, then uncomment this line and input your own set of sites **#
#sites=(PSC CERN TACC CLEM STAR SALT UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI PSC MICH)

echo ${sites[@]} in combined_results

for site in ${sites[@]}; do
	if [ ! -f ../$site/$logfile ]; then
		echo "**** File ../$site/$logfile does not exist ****"
		continue
	fi
	output=$(tail -20 ../$site/$logfile | grep -B10 -e "Deleting" -e "Exiting from")
	if [ -z "$output" ]; then
		echo "**** ../$site/$logfile has an error ****"
		tail -15 ../$site/$logfile
	else
		echo "**** $site: No error ****"
	fi
done
