from ipaddress import ip_address, IPv4Address, IPv6Address, IPv4Network, IPv6Network
from multiprocessing import shared_memory
import ipaddress
import sys
import os
import json
import argparse
import time
import math
import random
import setup
import sampling
import gathering
import strobing
import infrastructure_port_activity as ipa
import pw_logging as log

from datetime import datetime, timedelta
from dateutil import tz
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager


projectid = os.environ.get("PROJECT_ID")
fabricrc = os.environ.get("FABRIC_RC")
workdir = os.environ.get("WORKDIR")
if workdir == None:
    print("Please define WORKDIR environment variable")
    sys.exit(1)
fablib = fablib_manager(
    fabric_rc=f"{fabricrc}", project_id=f"{projectid}", log_file=f"{workdir}/fablib.log"
)

print(f"fablib: {fablib}")
fablib.show_config(output='json');
tcpdump_filter = "all"
experiment_retries = 270
max_iter_per_experiment = 1
wait_interval = 300
listen_time = 20
snaplen = 200

listener_sites = []
# Read argument from commandline to create listener site list
parser = argparse.ArgumentParser(description="Specify site to monitor")
parser.add_argument("site", type=str, help="name of site")
parser.add_argument("tcpdump_filter", type=str, help="tcpdump filter expression")
parser.add_argument("experiment_retries", type=int, help="Retries per experiment")
parser.add_argument("iter_per_experiment", type=int, help="Max iterations per retry")
parser.add_argument("wait_interval", type=int, help="Wait time between retries")
parser.add_argument("listen_time", type=int, help="Sampling time")
parser.add_argument("snaplen", type=int, help="Bytes to capture")
parser.add_argument("only_upstream", type=int, help="Enable only uplink port mirroring")
parser.add_argument("mirror_port", type=str, help="Specific port to be mirrored")
parser.add_argument("enable_gro", type=int, help="Enable GRO on VMs")
parser.add_argument("mode", type=str, help="Operation mode")
parser.add_argument("slice_name", type=str, help="User provided slice name")
parser.add_argument("shared_mem_name", type=str, help="User provided shared memory name")
parser.add_argument("log", type=str, help="Use any one Log mode: NONE / INFO / DEBUG")

cmdline_args = parser.parse_args()

tcpdump_filter = cmdline_args.tcpdump_filter
experiment_retries = cmdline_args.experiment_retries
max_iter_per_experiment = cmdline_args.iter_per_experiment
wait_interval = cmdline_args.wait_interval
listen_time = cmdline_args.listen_time
snaplen = cmdline_args.snaplen
only_upstream = cmdline_args.only_upstream
cmd_mirror_port = cmdline_args.mirror_port
enable_gro = cmdline_args.enable_gro
op_mode = cmdline_args.mode
slice_name = cmdline_args.slice_name
shared_mem_name = cmdline_args.shared_mem_name
log.set_log_mode(cmdline_args.log)

cmdline_args.site = cmdline_args.site.upper()

log.log(log.INFO, f"\nInitiating profiling in SITE {cmdline_args.site}")

listener_sites.append(cmdline_args.site)

log.log(log.DEBUG, f"{op_mode}, {slice_name}")
# Select sites to profile (Setup)
if op_mode == "operator":
    listener_slice_name = f"Traffic Listening Demo {cmdline_args.site}"
else:
    log.log(log.INFO, "mode is not operator")
    listener_slice_name = slice_name
cx6_column_name = "nic_connectx_6_available"
cx5_column_name = "nic_connectx_5_available"
sites_connectx_name = []
no_nic_sites = []

# Maintain a startup log file
startup_log_file = f"{workdir}/{cmdline_args.site}/startup_log.txt"
time_curr = time.time()  # Get current time at the end of the sampling phase
with open(startup_log_file, "w") as slog:
    slog.write(f"Startup Log file for site: {cmdline_args.site}\n")
    slog.write(f"Current time in asctime fmt: {time.asctime(time.gmtime(time_curr))}\n")
    slog.close()
log.log(log.INFO, f"Current time in asctime fmt: {time.asctime(time.gmtime(time_curr))}")
# Check if site has atleast 1 connectx6/connectx5 card available
# sites_connectx_json = fablib.list_sites(output="json", quiet="true", latlon=False)
sites_connectx_json = fablib.list_sites(
    output="json",
    quiet="true",
    filter_function=lambda x: x[cx6_column_name] > 0 or x[cx5_column_name] > 0,
    latlon=False,
)
sites_connectx = json.loads(sites_connectx_json)

# Convert json output to list of site names
for elem in sites_connectx:
    sites_connectx_name.append(elem["name"])

for site in listener_sites:
    if site not in sites_connectx_name:
        no_nic_sites.append(site)
        listener_sites.remove(site)
        with open(startup_log_file, "a") as slog:
            slog.write(f"{site} removed from site list due to lack of ConnectX resources\n")
            slog.close()

with open(startup_log_file, "a") as slog:
    slog.write(f"final listener sites are {listener_sites}\n")
    slog.write(f" Sites without Smart NICs are {no_nic_sites}\n")
    slog.write("\n")
    slog.close()

if len(listener_sites) == 0:
    log.log(log.INFO, f"{no_nic_sites} have no smartNICS available. Exiting!!")
    sys.exit(1)

# Create list of switch ports per site
exclude_list = (
    "EDC",
    "AWS",
    "AL2S",
    "AZURE",
    "GCP",
    "AZURE-GOV",
    "AZUREGOV",
    "OCI",
    "OCIGOV",
    "NONCLOUD",
)

# Create a list of ports to mirror per site
mirror_port_list = {}
port_count = {}


if cmd_mirror_port == "unused":
    for site_name, site_details in fablib.get_resources().topology.nodes.items():
        if site_name in exclude_list:
            continue
        if site_name not in listener_sites:
            continue
        list_site = []
        list_port = []
        uplink_count = 0
        port_count[site_name] = 0
        start_time = "1d"
        mirror_port_list[site_name] = []

        result = ipa.busy_switch_ports(listener_sites, start_time)
        log.log(log.DEBUG, f"{result}\n")
        result_list = result[0]["port_data"]
        log.log(log.DEBUG, f"{result_list}\n")
        for elem in result_list:
            list_site.append(elem[0])

        # If busy_switch_ports does not provide a return, read port names from the json file
        if len(list_site) == 0:
            fp = open(f"{workdir}/json_records/{site_name}_records.json", "r", encoding="utf-8-sig")
            with open(startup_log_file, "a") as slog:
                slog.write(
                    f"Opening file {workdir}/json_records/{site_name}_records.json to get port information\n"
                )
                slog.close()
            json_data = json.load(fp)
            for conn_point in json_data:
                str_cp = conn_point["cp"]["properties"]["Name"]
                # print(str_cp)
                with open(startup_log_file, "a") as slog:
                    slog.write(f"{str_cp}\n")
                    slog.close()
                if str_cp.startswith("p") or str_cp[:6] == "Bundle":  # Skipping dedicated ports
                    continue
                if only_upstream == 1:
                    if "." in str_cp:
                        list_site.append(str_cp.split(".")[0])
                else:
                    list_site.append(str_cp.split(".")[0])

        # print(f'{site_name}: {port_count[site_name]}')
        # print(f'ports: {port_count}')
        # print(f'vlans: {uplink_count}')
        if len(list_site) > 0:
            # Final list of ports to mirror
            for elem in list_site:
                if elem not in mirror_port_list[site_name]:
                    mirror_port_list[site_name].append(elem)
                    port_count[site_name] += 1
        log.log(log.DEBUG, mirror_port_list[site_name])
else:  # To support user specified mirror ports
    mirror_port_list[site] = []
    for site in listener_sites:
        log.log(log.DEBUG, cmd_mirror_port.split(".")[0])
        mirror_port_list[site].append(cmd_mirror_port.split(".")[0])
        port_count[site] = 1
log.log(log.DEBUG, mirror_port_list)


def slice_deletion(op_mode, deletion_type, slice_name, listner_nodes, listener_sites):
    if op_mode == "operator":
        if deletion_type == 1:
            fablib.delete_slice(slice_name)
        elif deletion_type == 2:
            pmslice = fablib.get_slice(slice_name)
            pmslice.delete()
    else:
        pmslice = fablib.get_slice(slice_name)
        log.log(log.DEBUG, f"pmslice.get_nodes(): {pmslice.get_nodes()}")
        lnodes = pmslice.get_nodes()
        log.log(log.DEBUG, listener_nodes)
        for node in lnodes:
            for listnode in listener_nodes[listener_sites[0]]:
                if node.get_name() == listnode.get_name():
                    log.log(log.INFO, f"Deleting node {node}")
                    node.delete()
                    break


# Global variables
pmslice = None
modulo_val = 1
listener_node_name = {}
listener_nodes = {}
listener_direction = {}
listener_interfaces = {}
ports_mirrored = {}
mod_port_list = {}
listener_pmservice_name = {}
pmnet = {}
num_pmservices = {}

# Specify listener uplink mirror direction for each site
for listener_site in listener_sites:
    if not mirror_port_list[listener_site]:
        log.log(log.INFO, "Can't proceed as there are no ports to mirror")
        sys.exit(1)
    listener_node_name[listener_site] = []
    listener_nodes[listener_site] = []
    listener_direction[listener_site] = "both"  # can also be 'rx' and 'tx'
    ports_mirrored[listener_site] = 0
    mod_port_list[listener_site] = {}
    listener_pmservice_name[listener_site] = []

    log.log(log.INFO,
        f"Will create slice {listener_slice_name} on {listener_site} listening to ports {mirror_port_list[listener_site]} in {listener_direction[listener_site]} direction/s"
    )
    with open(startup_log_file, "a") as slog:
        slog.write(f"\n\n\nFINAL LIST OF PORTS TO BE MIRRORED:\n")
        slog.write(
            f"Will create slice {listener_slice_name} on {listener_site} listening to ports {mirror_port_list[listener_site]} in {listener_direction[listener_site]} direction/s\n"
        )
        slog.write(f"port_count: {port_count}\n")
        slog.close()

    log.log(log.INFO, f"port_count: {port_count}\n")


# PHASE1 Setup: Submit Slice Request
port_reduce_count = 0
retry = 0
consecutive_retries = 0
retry_limit = 3
fail_count_file = f"{workdir}/{cmdline_args.site}/fail_count.txt"

while retry != 1:
    try:
        consecutive_retries += 1
        modulo_val, pmslice, listener_interfaces = setup.setup_slice(
            port_reduce_count,
            fablib,
            startup_log_file,
            listener_slice_name,
            listener_sites,
            listener_nodes,
            listener_interfaces,
            mod_port_list,
            pmnet,
            num_pmservices,
            listener_pmservice_name,
            ports_mirrored,
            port_count,
            sites_connectx,
            listener_node_name,
            mirror_port_list,
            listener_direction,
            modulo_val,
            op_mode,
        )
        log.log(log.INFO, "\nSubmitting slice request to backend\n")
        with open(startup_log_file, "a") as slog:
            slog.write("\nSubmitting slice request to backend\n")
            slog.close()
        ret_val = pmslice.submit(progress=True, wait_timeout=2400, wait_interval=120)
        log.log(log.DEBUG, f"Initial phase return value {ret_val}")
        if pmslice.get_state() == "StableError":
            raise Exception("Slice state is StableError")
        retry = 1
    except Exception as e:
        with open(startup_log_file, "a") as slog:
            slog.write(f"{pmslice.get_state()}\n")
            slog.close()

        if pmslice.get_state() == "StableError":
            slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
            #fablib.delete_slice(listener_slice_name)
        else:
            slice_deletion(op_mode, 2, listener_slice_name, listener_nodes, listener_sites)
            #pmslice.delete()

        if consecutive_retries >= retry_limit:
            log.log(log.INFO, f"Exiting due to too many retries\n")
            with open(startup_log_file, "a") as slog:
                slog.write(f"Exiting due to too many retries\n")
                slog.close()
            sys.exit(1)

        time.sleep(120)
        with open(startup_log_file, "a") as slog:
            slog.write(f"Setup exception: {e}\n")
            slog.close()
            os.system(
                f"cat {startup_log_file} | grep -i Exception | sort | uniq | wc -l > {fail_count_file}"
            )
            with open(fail_count_file, "r") as flog:
                port_reduce_count = int(flog.read())
                log.log(log.DEBUG, f" port_reduce_count: {port_reduce_count}")
                flog.close()
            os.system(f"rm {fail_count_file}")
        log.log(log.DEBUG, pmslice.get_state())

# Add slice info to logs
with open(startup_log_file, "a") as slog:
    slog.write(f"{pmslice.show()}\n\n\n")
    slog.write(f"{pmslice.list_nodes()}\n\n\n")
    slog.write(f"{pmslice.list_networks()}\n\n\n")
    slog.write(f"{pmslice.list_interfaces()}\n\n\n")
    slog.close()

# Method: Extend the slice
def extend_slice():
    try:
        pmslice = fablib.get_slice(name=listener_slice_name)
        end_date = (datetime.now(tz=tz.tzutc()) + timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )
        pmslice.renew(end_date)
    except Exception as e:
        log.log(log.INFO, f"Exception: {e}")


extend_slice()  # Invoke slice extension

# PHASE2 SAMPLING: Copy helper scripts to listener VM
out_file = f"{workdir}/{cmdline_args.site}/upload_files.sh"

# Invoke helper copy method to generate copy scripts
try:
    listener_ssh = sampling.copy_helpers(
        fablib,
        startup_log_file,
        listener_node_name,
        listener_slice_name,
        out_file,
        listener_sites,
        listener_nodes,
    )
except Exception as e:
    with open(startup_log_file, "a") as slog:
        log.log(log.INFO, f"Sampling.copy_helpers exception: {e}")
        slog.write(f"Sampling.copy_helpers exception: {e}\n")
        slog.close()
        slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
        #fablib.delete_slice(listener_slice_name)
        sys.exit(1)

# Execute generated copy scripts
os.system(f"chmod u+x {out_file}")
os.system(f"{out_file}")

# Method: Execute tcpdump script on listener (Sampling)
with open(startup_log_file, "a") as slog:
    slog.write(f"\nInitiating sampling phase\n")
    slog.close()

# Execute sampling method
try:
    total_experiment_time = sampling.pw_sampling(
        fablib,
        startup_log_file,
        listener_node_name,
        listener_pmservice_name,
        listener_slice_name,
        num_pmservices,
        cmdline_args,
        listener_sites,
        listener_nodes,
        enable_gro,
    )

except Exception as e:
    with open(startup_log_file, "a") as slog:
        log.log(log.INFO, f"Sampling.pw_sampling exception: {e}")
        slog.write(f"Sampling.pw_sampling exception: {e}\n")
        slog.close()
        slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
        #fablib.delete_slice(listener_slice_name)
        sys.exit(1)
# Note down time when tcpdump sampling has begun
try:
    # In Python, try does not create it's own block scope, so time_tcpdump_start can be reused
    time_tcpdump_start = time.time()
except Exception as e:
    with open(startup_log_file, "a") as slog:
        slog.write(f"Startup exception: {e}\n")
        slog.close()
    log.log(log.INFO, f"Startup exception {e}")
    slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
    #fablib.delete_slice(listener_slice_name)

with open(startup_log_file, "a") as slog:
    slog.write(f"time_tcpdump_start {time_tcpdump_start} seconds\n")
    slog.close()

# Start synchronization process for single user mode
if op_mode != "operator":
    shm_key = shared_mem_name
    shm_twine = shared_memory.SharedMemory(shm_key)
    shm_twine.buf[:5] = b'start'
    shm_twine.close()

pmslice = fablib.get_slice(name=listener_slice_name)

# PHASE3 Strobing
time_curr = time.time()
time_bringdown_start = time_curr  # Holds initial value of bringdown timer's start value
bring_down_port_group = 0  # Select which half of ports need to be brought down
bringdown_time = 1800
with open(startup_log_file, "a") as slog:
    slog.write(f"total_sampling_time: {total_experiment_time} seconds\n")
    slog.close()
with open(startup_log_file, "a") as slog:
    slog.write(f"\nInitiating strobing phase\n")
    if modulo_val <= 2:
        slog.write(
            f"\nStrobing disabled. Will listen on all ports for the duration of the experiment\n"
        )
    slog.close()
# +100 seconds to ensure that tar files have been generated
while (time_curr - time_tcpdump_start) < (total_experiment_time + 100):
    # Every 'bringdown_time seconds, conduct port strobing
    if time_curr - time_bringdown_start > bringdown_time and modulo_val > 2:
        with open(startup_log_file, "a") as slog:
            slog.write(f"time_since_sampling_start: {time_curr - time_tcpdump_start} seconds\n")
            slog.write(f"last strobe cycle took: {time_curr - time_bringdown_start} seconds\n\n\n")
            slog.write(f"Current time in asctime fmt: {time.asctime(time.gmtime(time_curr))}\n")
            slog.close()
        time_bringdown_start = time_curr  # Update timer start window

        # Bring down half the mirrored ports
        try:
            strobing.strobe_bringdown(
                fablib,
                listener_sites,
                startup_log_file,
                listener_nodes,
                listener_pmservice_name,
                pmslice,
                bring_down_port_group,
            )
        except Exception as e:
            with open(startup_log_file, "a") as slog:
                slog.write(f"strobing.strobe_bringdown exception {e}\n")
                slog.write(f"Deleting slice \n")
                slog.close()
            log.log(log.INFO, f"strobing.strobe_bringdown exception {e}")
            if pmslice.get_state() == "StableError":
                slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
                #fablib.delete_slice(listener_slice_name)
            else:
                slice_deletion(op_mode, 2, listener_slice_name, listener_nodes, listener_sites)
                #pmslice.delete()
            sys.exit(1)
        #  Randomize and Re-add port mirror service for a group of ports a.k.a strobing
        try:
            bring_down_port_group = strobing.strobe_bringup(
                fablib,
                pmslice,
                listener_sites,
                listener_nodes,
                listener_node_name,
                mod_port_list,
                listener_interfaces,
                bring_down_port_group,
                listener_pmservice_name,
                listener_direction,
                ports_mirrored,
                startup_log_file,
            )
        except Exception as e:
            with open(startup_log_file, "a") as slog:
                slog.write(f"strobing.strobe_bringup exception {e}\n")
                slog.write(f"Deleting slice \n")
                slog.close()
            log.log(log.INFO, f"strobing.strobe_bringup exception {e}")
            if pmslice.get_state() == "StableError":
                slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
                #fablib.delete_slice(listener_slice_name)
            else:
                slice_deletion(op_mode, 2, listener_slice_name, listener_nodes, listener_sites)
                #pmslice.delete()
            sys.exit(1)
    else:
        time.sleep(5)
    time_curr = time.time()  # Update current time

time_curr = time.time()  # Get current time at the end of the sampling phase
with open(startup_log_file, "a") as slog:
    slog.write(f"Final experiment time: {time_curr - time_tcpdump_start} seconds\n")
    slog.write(f"last strobe cycle took: {time_curr - time_bringdown_start} seconds\n\n\n")
    slog.write(f"Current time in asctime fmt: {time.asctime(time.gmtime(time_curr))}\n")
    slog.close()
log.log(log.DEBUG, time_curr)

now = datetime.now(tz=tz.tzutc()).strftime("%Y-%m-%d_%H-%M-%S")
log.log(log.DEBUG, now)

with open(startup_log_file, "a") as slog:
    slog.write(f" \n")
    slog.write(f" Initiating Gathering phase\n")
    slog.write(f" Gathering pcap files from VMs\n")
    slog.close()
# Method: Download tarred file from VM to current workspace (Gathering)
out_file = f"{workdir}/{cmdline_args.site}/download_tar.sh"
top_dir = f"all_packet_traces_{now}"
full_path_top_dir = f"{workdir}/{cmdline_args.site}/{top_dir}"

# PHASE4 Gathering: Execute method to gather the output of sampling phase
try:
    gathering.pw_gather(
        fablib,
        listener_slice_name,
        listener_sites,
        listener_nodes,
        listener_node_name,
        listener_ssh,
        startup_log_file,
        out_file,
        full_path_top_dir,
        top_dir,
        cmdline_args,
    )
except Exception as e:
    with open(startup_log_file, "a") as slog:
        slog.write(f"Gathering exception: {e}\n")
        slog.close()
    log.log(log.INFO, f"Gathering exception: {e}")

# Copy tar files from each VM to a single top level directory
log.log(log.INFO, "Copy tar files from each VM to a single top level directory")
with open(startup_log_file, "a") as slog:
    slog.write(f" \n")
    slog.write(f" Copy tar files from each VM to a single top level directory\n")
    slog.close()

os.system(f"chmod u+x {workdir}/{cmdline_args.site}/download_tar.sh")
os.system(f"{workdir}/{cmdline_args.site}/download_tar.sh")

if op_mode == "operator":
    # Delete the slice
    log.log(log.INFO, f"Deleting the slice {listener_slice_name}\n")
    with open(startup_log_file, "a") as slog:
        slog.write(f" \n")
        slog.write(f"Deleting the slice {listener_slice_name}\n")
        slog.close()
    try:
        slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
    except Exception as e:
        with open(startup_log_file, "a") as slog:
            slog.write(f" {e}\n")
            slog.close()
        log.log(log.INFO, f" Delete slice exception {e}")
else:
    slice_deletion(op_mode, 1, listener_slice_name, listener_nodes, listener_sites)
    '''    
    for listener_site in listener_sites:
        i = 0
        for node in listener_nodes[listener_site]:
            lnode = pmslice.get_node(name=listener_node_name[listener_site][i])
            print(f"Deleting node {lnode} on site {listener_site}")
            lnode.delete()
    '''
    log.log(log.DEBUG, f"pmslice: {pmslice}")
    log.log(log.DEBUG, f"pmslice.show(): {pmslice.show()}")
    log.log(log.DEBUG, f"pmslice.get_nodes() : {pmslice.get_nodes()}")
    pmslice.update()

log.log(log.INFO, f"Exiting from {listener_slice_name}\n")
with open(startup_log_file, "a") as slog:
    slog.write(f" \n")
    slog.write(f"Exiting from {listener_slice_name}\n")
    slog.close()

# Compress top level directory for download
log.log(log.INFO, "Run compress_tld")
os.system(f"cd {workdir}; ./compress_tld.sh {cmdline_args.site}; cd -;")

# Copy the log file to the latest_run directory for analysis
log.log(log.INFO, f"Copy log file to latest_run directory\n")
os.system(
    f"cp {workdir}/{cmdline_args.site}/startup_log.txt {workdir}/{cmdline_args.site}/latest_run/"
)
os.system(
    f"cp {workdir}/{cmdline_args.site}/startup_log.txt {workdir}/{cmdline_args.site}/all_packet_traces_{now}/"
)

if op_mode != "operator":
    shm_key = shared_mem_name
    shm_twine = shared_memory.SharedMemory(shm_key)
    # Clear shared memory content
    shm_twine.buf[:5] = bytearray([00,00,00,00,00])
    # Send stop signal
    shm_twine.buf[:4] = b'stop'
    shm_twine.close()

log.log(log.INFO, "Exiting program")
sys.exit(0)
