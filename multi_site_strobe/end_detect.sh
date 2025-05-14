#!/bin/bash
TOP_LEVEL_DIR="packet_trace"
LOG_FILE="packet_trace.log"
REFCNT_FILE="refcnt.txt"
END_LOG="end_detect_log.log"

# The timeout script is dependent on experiment sampling time. 
# It is run inside the VM by the Twine program
if [ $# -ne 1 ]; then
    echo "Usage: ./end_detect.sh <timeout> "
    exit
fi

TIMEOUT=$1
tot_scripts=$(cat $REFCNT_FILE | wc -l)
i=0

start_time=$(date +%s)
while true; do
        curr_time=$(date +%s)
        time_elapsed=$((curr_time - start_time))
        if [ $((time_elapsed % 100)) -eq 0 ]; then
            echo "time_elapsed: $time_elapsed" >> $END_LOG
        fi
        if [ $time_elapsed -gt $TIMEOUT ]; then
            echo "Enddetect exiting after timeout of $TIMEOUT seconds" >> $END_LOG
            break
        fi
        output=$(cat $LOG_FILE | tail -1)
        if [ "$output" == "EOF"  -o  "$output" == "ERROR" ]; then
                i=$((i+1))
                if [ $i -eq $tot_scripts ]; then
                    echo "Enddetect exiting after reading $i times" >> $END_LOG
                    break
                fi
        fi
        sleep 1
done

tar -zcvf $TOP_LEVEL_DIR.tgz $TOP_LEVEL_DIR $LOG_FILE $END_LOG >/dev/null 

echo "Completed end detect on $(hostname)"
