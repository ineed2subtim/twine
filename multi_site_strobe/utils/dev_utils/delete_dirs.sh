#!/bin/bash

#sites=(MICH STAR NCSA DALL CERN TACC CLEM SALT UCSD UTAH WASH MASS FIU GPN AMST BRIST HAWI KANS PSC RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA INDI MAX)
sites=()
if [ -n $sites ]; then
	echo "No sites specified"
	exit 1
fi
for site in ${sites[@]}; do
	if [ -d ../$site ]; then
		echo "rm -r ../$site"
	fi
done


