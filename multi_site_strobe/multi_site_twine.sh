#!/bin/bash

#sites=(CLEM STAR PSC CERN TACC UCSD UTAH MASS FIU GPN AMST BRIST HAWI KANS RUTG SEAT TOKY GATECH NEWY ATLA PRIN LOSA WASH SRI INDI MAX NCSA MICH SALT DALL)
sites=(SRI)
#sites=(RUTG GATECH MASS)

mirror_port="unused"
slice_name="unused"
mode="operator"
shared_mem_name=""
# If argument count is 5, then program is running in user mode
if [ $# -eq 5 ]; then
	mode=$1
	sites=($2)
	mirror_port=$3
	slice_name="$4"
	shared_mem_name="$5"
fi

# If argument count is 2, then operator has explicitly provided the port to mirror
if [ $# -eq 2 ]; then
	sites=($1)
	mirror_port=$2
fi

echo "workdir: $WORKDIR"
if [ -z $WORKDIR ]; then
	echo "ENV variable WORKDIR is not defined. Please run fabric_pyenv_setup.sh script again!!"
	exit 1
fi

if [ -f $FABRIC_BASTION_KEY_LOCATION ]; then
	bastion_perm=$(ls -l $FABRIC_BASTION_KEY_LOCATION | awk -e '{print $1}')
	if [ "$bastion_perm" != "-rw-------" ]; then
		echo "Please set bastion key private key permissions to 0600. Exiting!!!"
	fi	
fi


echo ${sites[@]} > $WORKDIR/utils/sites_used_last_experiment

# This stands for the filter expression that tcpdump will utilize inorder to filter packets. Default = "all"
tcpdump_filter="all"
# This is the number of times the packet capture program will run on the listener. Between each run, it will wait for 'wait_interval' seconds
experiment_retries=4
# The time in seconds, that the program will wait before restarting tcpdump to listen for packets
wait_interval=40
# The maximum number of bytes of the packet that will be written to the pcap file.
snaplen=200
# The time in seconds, that tcpdump will listen and filter for packets
listen_time=20
# The number of times the tcpdump program will be started and stopped without any wait times.
max_iter_per_retry=1
# Enable only uplink port mirroring
only_upstream=0

echo "Parameters selected are:"
echo "tcpdump_filter : $tcpdump_filter"
echo "experiment_retries: $experiment_retries"
echo "wait_interval: $wait_interval"
echo "listen_time: $listen_time"
echo "max_iter_per_retry: $max_iter_per_retry"
echo "snaplen: $snaplen"
echo "only_upstream: $only_upstream"
if [ $# -eq 5 ]; then
	echo "slice_name: $slice_name"
	echo "shared_mem_name: $shared_mem_name"
fi

# Enable GRO to improve capture performance (as a side effect may see large jumbo packets in the pcap file)
enable_gro=0


# Set logging mode as one of NONE / INFO / DEBUG 
log="INFO"
echo "Log mode selected is $log"

if [ -z $sites ]; then
	echo "No SITES specified. Exiting!!!"
	exit 1
fi
for site in ${sites[@]}; do
	if [ ! -d $WORKDIR/$site ]; then
		mkdir -p $WORKDIR/$site/latest_run
	fi
	if [ -d "$WORKDIR/$site/latest_run/" ]; then
		rm $WORKDIR/$site/latest_run/*
	fi
	# Add mirror_port argument
	python3 $WORKDIR/twine.py $site "$tcpdump_filter" $experiment_retries $max_iter_per_retry $wait_interval $listen_time $snaplen $only_upstream $mirror_port $enable_gro $mode "$slice_name" "$shared_mem_name" $log&
done
