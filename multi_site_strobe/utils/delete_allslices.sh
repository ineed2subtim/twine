#!/bin/bash

sites=()

sites_used_last=$(cat sites_used_last_experiment | wc -l)
if [ $sites_used_last -ne 0 ]; then
	sites+=($(cat sites_used_last_experiment))
fi

#** If user wants to overwrite the sites to be used, then uncomment this line and input your own set of sites **#
#sites=(PSC CERN TACC CLEM STAR SALT UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI PSC MICH)

for site in ${sites[@]}
	do
		python3 delete_slice.py $site
	done

