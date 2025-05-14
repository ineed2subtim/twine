
from ipaddress import ip_address, IPv4Address, IPv6Address, IPv4Network, IPv6Network
import ipaddress
import sys
import os
import json
import argparse

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

projectid = os.environ.get('PROJECT_ID')
fabricrc = os.environ.get('FABRIC_RC')

fablib = fablib_manager(fabric_rc=f"{fabricrc}", project_id=f"{projectid}")
                     
fablib.show_config(output='json');

parser = argparse.ArgumentParser("Enter site name")
parser.add_argument("site_name", type=str)

args = parser.parse_args()
site_name = args.site_name

# Maintain a startup log file

startup_log_file = "startup_log.txt"
with open(startup_log_file, "w") as slog:
    slog.write("Startup Log file\n")
    slog.close()

# Select sites to profile (Setup)    

listener_slice_name = f"Traffic Listening Demo {site_name}"
cx6_column_name = 'nic_connectx_6_available'

# Delete the slice
with open(startup_log_file, "a") as slog:
    slog.write("Deleting slice in %s\n" %site_name)
    slog.close()

try:
    fablib.delete_slice(listener_slice_name)
except Exception as e:
    print(e)
