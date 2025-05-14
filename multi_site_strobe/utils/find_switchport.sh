#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Argument missing"
	echo "Usage: ./find_switchport.sh experiment_run1"
	exit 0
fi
experiment_dir=$1
top_level_dir=$PWD
if [ -d "$experiment_dir" ]; then
	cd $experiment_dir
else
	echo "Invalid experiment directory"
	echo "Usage: ./find_switchport.sh experiment_run1"
	exit 0
fi

directories=$(ls -l | grep ^d | awk '{print $9}')

for dir in $directories
	do
		if [ "$dir" != "./" -a $dir != "../" ]; then
			echo $dir
		fi
	done

curr_dir=$PWD		# Keep track of this current directory
echo "curr_dir : $curr_dir"
for dir in $directories
	do
		cd $curr_dir
		cd $dir
		if [ $(ls | grep tgz | wc -l) -eq 0 ]; then
			echo "no TAR file present in $curr_dir/$dir"
			continue
		fi
		# Untar and go down the directories
		tar -zxvf *.tgz
		sub_dir=$(ls -l | grep ^d | awk '{print $9}')
		cd $sub_dir
		while [ $(ls | grep tgz | wc -l) -eq 0 ] 
			do
				sub_dir=$(ls -l | grep ^d | awk '{print $9}')
				cd $sub_dir
			done
		
		ls

		if [ -f $top_level_dir/match_switchport.py ]; then
			cp $top_level_dir/match_switchport.py .
		else
			echo "Cannot find match_switchport.py"
			echo "Place it in the same directory as this script"
			echo "Exiting!!"
			exit 1
		fi

		# Create specific directories for each node
		ls *.tgz > tar_files.txt
		
		cut -d'_' -f 2 tar_files.txt > node_files.txt
		
		for node_name in $(cat node_files.txt)
			do
				#echo $node_name
				if [ ! -d $node_name ] 
				then
					mkdir $node_name
				fi
			done
		rm tar_files.txt
		
		cnt=0
		for compress_file in $(ls *.tgz)
		do
			dir=$(cat node_files.txt | grep node$cnt)
			file_cnt=$(ls $dir | wc -l)
			if [ $file_cnt -eq 0 ]; then
				tar -zxvf $compress_file -C $dir
			fi
			cnt=$((cnt+1))	
		done	
		# Obtain bringup and bringdown times from startup_log.txt
		for node_name in $(cat node_files.txt)
		do
			cat startup_log.txt | grep -e tcpdump -e submit_start -e Final > $node_name/up_down_times.txt
			cat startup_log.txt | grep $node_name-pmnic_.-p. > $node_name/${node_name}_p1_before_p2.txt
			cat startup_log.txt | grep -B2 $node_name-pmnic_.-p1 | grep 'mirror' > $node_name/${node_name}_mirrored_ports_p1.txt
			cat startup_log.txt | grep -B2 $node_name-pmnic_.-p2 | grep 'mirror' > $node_name/${node_name}_mirrored_ports_p2.txt
		done
		
		# Obtain all the listened times for each interface in each node 
		cwd=$PWD
		for node_name in $(cat node_files.txt)
		do
			cd $cwd
			pcnt=1
			for iface in $(ls $node_name/packet_trace)
			do
				cd $cwd
				cd $node_name/packet_trace/$iface
				datefile="${node_name}_p${pcnt}_listen_time.txt"
				ls > pcap_dir.txt
				awk -F'_' '{print $4"-"$2"-"$3"_"$5}' pcap_dir.txt > time_dir.txt
				rm pcap_dir.txt
				
				awk -F'_' '{print $1}' time_dir.txt > day.txt
				awk -F'_' '{print $2}' time_dir.txt > clock.txt
				day_time=()
				for day in $(cat day.txt)
				do
					day_time+=($day)
				done
				clock_time=()
				for clock in $(cat clock.txt)
				do
					clock_time+=($clock)
				done
				rm time_dir.txt
				rm day.txt
				rm clock.txt
				
				arr_cnt=0
				for day in ${day_time[@]}
				do
					#echo $arr_cnt
					time=$(echo "$day ${clock_time[$arr_cnt]}")
					#echo $time
					if [ $arr_cnt -eq 0 ]; then
						date --date="$time" +%s > ../../${datefile}
					else
						date --date="$time" +%s >> ../../${datefile}
					fi
					arr_cnt=$((arr_cnt + 1))
				
				done
				cd $cwd
				# Execute the switchport to listen port matching program
				python3 match_switchport.py $node_name p$pcnt
		
				rm $node_name/${datefile}
				pcnt=$((pcnt + 1))
			done	
		done
		
		# Clean temp files
		for node_name in $(cat node_files.txt)
		do
			rm $node_name/${node_name}_mirrored_ports_p1.txt
			rm $node_name/${node_name}_mirrored_ports_p2.txt
			rm $node_name/${node_name}_p1_before_p2.txt
		done
		rm node_files.txt
	done
		



