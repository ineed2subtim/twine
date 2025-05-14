#!/bin/bash

if [ $# -lt 1 ]; then
	echo "Usage: ./combine_results.sh <directory_name>" 
	echo " E.g: ./combine_results.sh 08_20_evening_12hr_upstream"
	exit 1
fi

dirname=$1

sites=()

sites_used_last=$(cat sites_used_last_experiment | wc -l)
if [ $sites_used_last -ne 0 ]; then
	sites+=($(cat sites_used_last_experiment))
fi

#** If user wants to overwrite the sites to be used, then uncomment this line and input your own set of sites **#
#sites=(PSC CERN TACC CLEM STAR SALT UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI PSC MICH)

echo ${sites[@]} in combined_results

log_file="startup_log.txt"

if [ ! -d $dirname ]; then
	mkdir $dirname
else
	echo "Directory $dirname already exists. Exiting"
	exit 1
fi

for site in ${sites[@]}; do
	if [ -d ../$site ]; then
		mkdir $dirname/${site}
		cp ../$site/$log_file ../$site/latest_run/
		cp ../$site/latest_run/* $dirname/${site}
	fi
done

./check_completion.sh ${sites[@]} > $dirname/${1}_summary.txt

# Add total size and size of individual files to the summary
cd $dirname
echo ""
echo "----- TOTAL COMBINED SIZE --------" >> ${1}_summary.txt
du -sh . >> ${1}_summary.txt
echo ""
echo "---- SITE SPECIFIC SIZE ---------" >> ${1}_summary.txt
ls | xargs du -sh >> ${1}_summary.txt

cd -

