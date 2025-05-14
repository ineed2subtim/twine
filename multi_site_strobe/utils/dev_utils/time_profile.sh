#!/bin/bash

sites=(INDI MAX)
#sites=(STAR NCSA DALL CERN TACC SALT UCSD UTAH WASH MASS FIU GPN AMST BRIST HAWI KANS PSC RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA)
out_file=time_profile.txt
python_script=plot_time_profile.py
graph_dir=time_profile_graphs

if [ -d $graph_dir ]; then
	rm -r $graph_dir
fi
mkdir $graph_dir

if [ -f $out_file ]; then
	rm $out_file
	touch $out_file
fi

for site in ${sites[@]}; do
	down_time=$(cat ../$site/startup_log.txt | grep 'bringdown_submit_stop' | awk '{print $2}')
	up_time=$(cat ../$site/startup_log.txt | grep 'bringup_submit_stop' | awk '{print $2}')
	tot_time=$(cat ../$site/startup_log.txt | grep 'strobe cycle' | awk '{print $5}')
	
	echo "$site bringdown times" >> $out_file
	echo $down_time >> $out_file
	echo "$site bringup times" >> $out_file
	echo $up_time >> $out_file
	echo "$site cycle times" >> $out_file
	echo $tot_time >> $out_file
	
		
done

python3 $python_script
