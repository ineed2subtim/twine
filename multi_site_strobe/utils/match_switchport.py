#! /usr/bin/python3

import sys
import argparse
import time


# Convert seconds from EPOCH to specified format
def seconds_to_date(listen_time):
    date_struct = time.gmtime(listen_time)
    date_str = time.strftime("pcap_%m_%d_%Y_%H:%M:%S", date_struct)
    return date_str


""" 
Search matches for interval listen_time(q) --- listen_time+interval(q') and bringup_time(m) and bringdown_time(n)
Conditions are:
    q < q' < m < n    -- No intersection
    m < n < q < q'    -- No intersection
    q < m < q' < n    -- Partial match in the last q'-m seconds
    m < q < n < q'    -- Parital match in the first n - q seconds
    m < q < q' < n    -- Full match
"""


def bin_search_interval(
    q_start, bringup_time, bringdown_time, mirrored_ports, output_file, start, end, interval=20
):
    global node_dir
    # print(f"start: {start} ; end: {end}")
    if start > end:
        date_str = seconds_to_date(q_start)
        print(f"No match on {date_str}")
        with open(f"{node_dir}/{output_file}", "a") as out:
            out.write(f"No match on {date_str}")
            out.write("\n")
        return
    mid = int((start + end) / 2)

    q_end = q_start + interval
    bringup = float(bringup_time[mid])
    bringdown = float(bringdown_time[mid])
    if q_start < bringup and q_end > bringup:
        date_str = seconds_to_date(q_start)
        print(
            f"Partial match of last {q_end - bringup} seconds on {date_str}: Port mirrored is {mirrored_ports[mid]}"
        )
        with open(f"{node_dir}/{output_file}", "a") as out:
            out.write(
                f"Partial match of last {q_end - bringup} seconds on {date_str}: Port mirrored is {mirrored_ports[mid]}"
            )
            out.write("\n")
        return
    elif q_start < bringdown and q_end > bringdown:
        date_str = seconds_to_date(q_start)
        print(
            f"Partial match on first {bringdown - q_start} seconds on {date_str}: Port mirrored is {mirrored_ports[mid]}"
        )
        with open(f"{node_dir}/{output_file}", "a") as out:
            out.write(
                f"Partial match on first {bringdown - q_start} seconds on {date_str}: Port mirrored is {mirrored_ports[mid]}"
            )
            out.write("\n")
        return
    elif q_start > bringup and q_end < bringdown:
        date_str = seconds_to_date(q_start)
        print(f"Full match on {date_str}: Port mirrored is {mirrored_ports[mid]}")
        with open(f"{node_dir}/{output_file}", "a") as out:
            out.write(f"Full match on {date_str}: Port mirrored is {mirrored_ports[mid]}")
            out.write("\n")
        return
    elif q_start < bringup:
        end = mid - 1
    elif q_start > bringdown:
        start = mid + 1

    bin_search_interval(
        q_start, bringup_time, bringdown_time, mirrored_ports, output_file, start, end, interval
    )


parser = argparse.ArgumentParser(description="Specify node and port")
parser.add_argument("node", type=str, help="node identifier")
parser.add_argument("port", type=str, help="listen port identifier")
cmdline_args = parser.parse_args()

node_dir = cmdline_args.node
lport = cmdline_args.port
# Create output file
output_file = f"{lport}_mirrorinfo.txt"
with open(f"{node_dir}/{output_file}", "w") as out:
    out.write(f"Information displaying which switch port was mirrored to {node_dir} port {lport}")
    out.write("\n\n")

# Find which port goes down first, since ports are brought down as p1, p2, p1, p2... OR p2, p1, p2, p1...
p1_before_p2 = 0
p1_before_p2_content = []
with open(f"{node_dir}/{node_dir}_p1_before_p2.txt", "r") as p1bp2:
    p1_before_p2_content = p1bp2.readlines()

if "p1" in p1_before_p2_content[0]:
    p1_before_p2 = 1

# Read bringup and bringdown times
updown_filecontent = []
with open(f"{node_dir}/up_down_times.txt", "r") as udfd:
    updown_filecontent = udfd.readlines()
bringup_time = []
bringdown_time = []

bringdown_count = 0
bringup_count = 0
experiment_start = 0
# print(len(updown_filecontent))
for content in updown_filecontent:
    if "tcpdump" in content:
        experiment_start = content.split(" ")[1]
        bringup_time.append(experiment_start)
    elif "bringdown" in content:
        bringdown_count += 1
        # Pattern of port bringdown changes based on which is the first port(p1 or p2) that is brought down
        if p1_before_p2 == 1:
            if bringdown_count % 2 == 1:
                if lport == "p1":
                    bringdown_time.append(content.split(" ")[1])
            else:
                if lport == "p2":
                    bringdown_time.append(content.split(" ")[1])
        else:
            if bringdown_count % 2 == 1:
                if lport == "p2":
                    bringdown_time.append(content.split(" ")[1])
            else:
                if lport == "p1":
                    bringdown_time.append(content.split(" ")[1])
    elif "bringup" in content:
        bringup_count += 1
        # Pattern of port bringdown changes based on which is the first port(p1 or p2) that is brought down
        if p1_before_p2 == 1:
            if bringdown_count % 2 == 1:
                if lport == "p1":
                    bringup_time.append(content.split(" ")[1])
            else:
                if lport == "p2":
                    bringup_time.append(content.split(" ")[1])
        else:
            if bringdown_count % 2 == 1:
                if lport == "p2":
                    bringup_time.append(content.split(" ")[1])
            else:
                if lport == "p1":
                    bringup_time.append(content.split(" ")[1])

    elif "Final" in content:
        experiment_end = content.split(" ")[3]
        bringdown_time.append(float(experiment_start) + float(experiment_end))
print(f"bringup_time: {bringup_time}")
print(f"len bringup_time", len(bringup_time))
print(f"bringdown_time: {bringdown_time}")
print(f"len bringdown_time", len(bringdown_time))

# Get times when port 'lport' started listening for traffic
node_port_times = []
with open(f"{node_dir}/{node_dir}_{lport}_listen_time.txt", "r") as iflisten:
    node_port_times = iflisten.readlines()
# print(f"node_port_times: {node_port_times}")

# Get all the switch ports that were mirrored
node_mports = []
node_read_mirrports = []
with open(f"{node_dir}/{node_dir}_mirrored_ports_{lport}.txt") as mport:
    node_read_mirrports = mport.readlines()
for i in range(0, len(node_read_mirrports)):
    if i == 0:
        node_mports.append(node_read_mirrports[i].split(" ")[3])
    else:
        node_mports.append(node_read_mirrports[i].split(" ")[4])
# print(node_mports)
# print(len(node_mports))
# print(len(node_port_times))

# Do interval matching and record result in output_file
for i in range(0, len(node_port_times)):
    q_start = float(node_port_times[i])
    bin_search_interval(
        q_start,
        bringup_time,
        bringdown_time,
        node_mports,
        output_file,
        0,
        len(bringdown_time) - 1,
        20,
    )
