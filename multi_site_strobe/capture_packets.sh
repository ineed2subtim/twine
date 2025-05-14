#!/bin/bash

# This script is run inside the VM by Twine

TOP_LEVEL_DIR="packet_trace"
LOG_FILE="packet_trace.log"
REFCNT_FILE="refcnt.txt"

echo "RUNSCRIPT" >> "$REFCNT_FILE"
if [ ! -d $TOP_LEVEL_DIR ]; then
        mkdir $TOP_LEVEL_DIR
fi

if [ $# -ne 7 ]; then
    echo "Usage: ./capture_packets.sh <interface_name> <experiment_retries> <max_iterations_per_experiment> <interval_between_experiments> <listen_time> <snaplen> <tcpdump_filter> " >> $LOG_FILE
    echo "ERROR" >> $LOG_FILE
    exit 1
fi

RETRIES=2
MAX_ITERATIONS=5
WAIT_INTERVAL=10
TIMEOUT=10
SNAPLEN=64
TCPDUMP_FILTER="all"
DATEFORMAT="%m_%d_%Y_%T"
LISTEN_IFACE=$1
RETRIES=$2
MAX_ITERATIONS=$3
WAIT_INTERVAL=$4
TIMEOUT=$5
SNAPLEN=$6
TCPDUMP_FILTER=$7
if [ "$TCPDUMP_FILTER" == "all" ]; then
        CAPTURE_CMD="tcpdump -i $LISTEN_IFACE -Q in -s $SNAPLEN -B 32768"
else
        CAPTURE_CMD="tcpdump -i $LISTEN_IFACE -Q in -s $SNAPLEN -B 32768 $TCPDUMP_FILTER"
fi
echo "Running capture command: $CAPTURE_CMD" >> $LOG_FILE

avail_percent=100
min_free_storage=40
check_free_storage(){
	total=$(df -m | grep '/$' | awk '{print $2}')
	avl=$(df -m | grep '/$' | awk '{print $4}')
	avail_percent=$(($avl * 100 / $total))
}


NUM=1
capture() {
        ITERATION=1
        CURR_TIME=$(date +"$DATEFORMAT")
        PCAP_DIR="$TOP_LEVEL_DIR/$LISTEN_IFACE/pcap_${CURR_TIME}"
        mkdir $PCAP_DIR
        while [ $ITERATION -le $MAX_ITERATIONS ]; do
                FILENAME="$CURR_TIME-""$ITERATION"".pcap"
                OUT_FILE="$PCAP_DIR/$FILENAME"
                echo "### BEFORE generating $CURR_TIME-$ITERATION.pcap ###" >> "$PCAP_DIR/ethtool_stats.log"
                ethtool -S $LISTEN_IFACE | grep rx >> "$PCAP_DIR/ethtool_stats.log" 2>&1
                echo "### BEFORE generating $CURR_TIME-$ITERATION.pcap ###" >> "$PCAP_DIR/ip_link_show.log"
                ip -s -s link show dev $LISTEN_IFACE >> "$PCAP_DIR/ip_link_show.log" 2>&1
                echo " " >> "$PCAP_DIR/ethtool_stats.log"                
                sudo timeout ${TIMEOUT}s $CAPTURE_CMD -w $OUT_FILE >>"$PCAP_DIR/stdout.log" 2>>"$PCAP_DIR/stderr.log"
                echo "### AFTER generating $CURR_TIME-$ITERATION.pcap ###" >> "$PCAP_DIR/ethtool_stats.log"
                ethtool -S $LISTEN_IFACE | grep rx >> "$PCAP_DIR/ethtool_stats.log" 2>&1 
                echo "### AFTER generating $CURR_TIME-$ITERATION.pcap ###" >> "$PCAP_DIR/ip_link_show.log"
                ip -s -s link show dev $LISTEN_IFACE >> "$PCAP_DIR/ip_link_show.log" 2>&1
                echo " " >> "$PCAP_DIR/ethtool_stats.log"                
                ITERATION=$(($ITERATION+1))
        done
        return
}

while [ $NUM -le $RETRIES ]; do
        echo "$LISTEN_IFACE: Capturing packets try number $NUM of $RETRIES" >> $LOG_FILE
        if [ ! -d $TOP_LEVEL_DIR/$LISTEN_IFACE ]; then
            mkdir $TOP_LEVEL_DIR/$LISTEN_IFACE
            if [ $? -ne 0 ]; then
                echo "Failed to create $TOP_LEVEL_DIR/$LISTEN_IFACE. Exiting!"
                echo "ERROR" >> $LOG_FILE
                exit 1
            fi
        fi
        capture
	check_free_storage
	echo "avail_percent is $avail_percent" >> $LOG_FILE
	echo "avail_percent is $avail_percent"
	if [ $avail_percent -lt $min_free_storage ]; then
        	echo "ERROR: NOT ENOUGH STORAGE" >> $LOG_FILE
        	exit 1
	fi
		
        sleep $WAIT_INTERVAL
        NUM=$(($NUM+1))
done

echo "$LISTEN_IFACE: Finished packet capture successfully" >> $LOG_FILE
echo "EOF" >> $LOG_FILE
