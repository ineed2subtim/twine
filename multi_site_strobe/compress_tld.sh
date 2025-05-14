#!/bin/bash

# This script is invoked by Twine

### COMPRESS top level directory and COPY it to latest_run/  ###

SITE=$1
TOP_DIR=$(cat top_dir_name_$SITE.txt)
if [ -z "$TOP_DIR" ]; then
    echo "No top directory specified. Exiting !!! "
    exit 1
fi
echo "$TOP_DIR"
tar -zcvf "$SITE/$TOP_DIR.tgz" "$SITE/$TOP_DIR/"

#SITE_DIR=$(echo "$TOP_DIR" | cut -d'/' -f 1)
if [ -d "$SITE/latest_run/" ]; then
	rm $SITE/latest_run/*
else
	mkdir $SITE/latest_run/
fi
cp "$SITE/$TOP_DIR.tgz" $SITE/latest_run/
rm top_dir_name_$SITE.txt
