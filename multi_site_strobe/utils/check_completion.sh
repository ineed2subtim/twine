#!/bin/bash

sites=()
succeeded=0
graceful_degrade=0
failed=0
in_progress=0

sites_used_last=$(cat sites_used_last_experiment | wc -l)
if [ $sites_used_last -ne 0 ]; then
	sites+=($(cat sites_used_last_experiment))
fi

error_statements=("SSH Protocol" "Exception" "retries" "reservation_id" "Sites without" "NEDCOM" "Timeout" "Submitting")
#** If user wants to overwrite the sites to be used, then uncomment this line and input your own set of sites **#
#sites=(PSC CERN TACC CLEM STAR SALT UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI PSC MICH)

echo ${sites[@]} in combined_results
for dir in ${sites[@]};
do
	last_statement=$(tail -3 ../$dir/startup_log.txt)
	exited=$(echo $last_statement | grep 'Exiting from' | wc -l)
	port_reduced=$(echo $last_statement | grep -i 'ports!!!' | wc -l)
	if [ $exited -eq 1 ]; then
		echo "SITE $dir terminated successfully (Last 3 statements below)"
		tail -3 ../$dir/startup_log.txt
		echo " "
		succeeded=$(($succeeded + 1))
	else
		if [ $port_reduced -eq 1 ]; then
			echo "SITE $dir terminated with port reduction successfully"
			tail -2 ../$dir/startup_log.txt
			graceful_degrade=$(($graceful_degrade + 1))
		else
			for statement in ${error_statements[@]}
			do
				found_error=$(echo $last_statement | grep -i $statement | wc -l)
				if [ $found_error -gt 0 ]; then
					break
				fi
			done
			if [ $found_error -gt 0 ]; then
				echo "SITE $dir FAILED (Last 3 statements below)"
				tail -3 ../$dir/startup_log.txt
				echo " "
				failed=$(($failed + 1))
			else
				echo "SITE $dir IN PROGRESS (Last 3 statements below)"
				tail -3 ../$dir/startup_log.txt
				echo " "
				in_progress=$(($in_progress + 1))
			fi
		fi
	fi
done

echo "$succeeded sites succeeded"
echo "$graceful_degrade sites had a graceful_degradation"
echo "$failed sites FAILED"
echo "$in_progress sites IN PROGRESS"
