
## Output directory structure

The directory structure for Twine's output is as below:
```
The SITE_NAME is the root of the directory structure, in this example it is WASH

WASH/
    ---  all_packet_traces_2024-07-08_22-17-47.tgz
    ---  download_tar.sh
    ---  startup_log.txt
    ---  upload_files.sh
    ---  all_packet_traces_2024-07-08_22-17-47/                 <---- Shows the date and time when the files were gathered.
                                        --- startup_log.txt                 <---- Log file for the Twine implementation on this site
                                        --- WASH_node0_packet_trace.tgz     <--- A compressed archive of pcaps and system logs for each listening node on that site
                                        --- WASH_node1_packet_trace.tgz
                                        --- WASH_node0_packet_trace/
                                                            ---     end_detect_log.log  <--- Process synchronization log
                                                            ---     packet_trace.log    <--- Packet capture log
                                                            ---     packet_trace/       <--- Contains the pcap files
                                                                            --- enp7s0/     <---- Each of the listening interfaces
                                                                                     --- pcap_07_08_2024_21:00:21/      <--- Time of capture in dir name (MM_DD_YYYY_hh:mm:ss)
                                                                                     --- pcap_07_08_2024_21:05:41/      <--- 20second listen; 300s wait
                                                                                     --- pcap_07_08_2024_21:11:01/
                                                                                     --- pcap_07_08_2024_21:16:21/
                                                                            --- enp8s0/
                                                                                     --- pcap_07_08_2024_21:00:26/
                                                                                                              --- 07_08_2024_21:00:26-1.pcap
                                                                                                              --- ethtool_stats.log
                                                                                                              --- ip_link_show.log
                                                                                                              --- stderr.log
                                                                                                              --- stdout.log
                                                                                     --- pcap_07_08_2024_21:05:46/
                                                                                     --- pcap_07_08_2024_21:11:06/
                                                                                     --- pcap_07_08_2024_21:16:26/
```

## STARTUP log file structure:

Every Slice will have a file called 'startup_log.txt'. This contains information on: <br>
1. The ports to be monitored
2. The slice requested parameters
3. Mirror links
4. Sampling phase start and end. (This is the phase that starts to listen and record the traffic seen on the port)
5. Strobing phase start and end. (This is the phase used to handle switch port coverage when the listener ports available are less than the switch ports on that SITE. )
6. Gathering phase start and end. (This phase begins after strobing. It handles archiving the traffic information and downloading it to the local system from the FABRIC VMs. )

Below we explain in detail, the information seen in the log file 'startup_log.txt' <br>

### Obtain site port information

```
 Sites without Smart NICs are []		<--- An empty list indicates that the site has SmartNICs available
 
 Sites without Smart NICs are [<site_name>]	<--- Indicates there are no smartNICs on this site
 
```

The log will list the active ports on the SITE, obtained from the FABRIC information model(FIM) <br>
```
Opening file json_records/UTAH_records.json to get port information
HundredGigE0/0/0/5
HundredGigE0/0/0/9
HundredGigE0/0/0/4
HundredGigE0/0/0/2
TwentyFiveGigE0/0/0/10/2
HundredGigE0/0/0/21
TwentyFiveGigE0/0/0/10/0
TwentyFiveGigE0/0/0/8/0
TwentyFiveGigE0/0/0/10/1
...
...
```
### Setup slice parameters

The final list of ports to be mirrored and monitored is then logged next <br>
```
FINAL LIST OF PORTS TO BE MIRRORED:
Will create slice Traffic Listening Demo UTAH on UTAH listening to ports ['TwentyFiveGigE0/0/0/8/0', 'HundredGigE0/0/0/25/2', 'HundredGigE0/0/0/4', 'HundredGigE0/0/0/17', 'TwentyFiveGigE0/0/0/10/1', 'TwentyFiveGigE0/0/0/16/2', 'HundredGigE0/0/0/2', 'HundredGigE0/0/0/0', 'TwentyFiveGigE0/0/0/10/2', 'HundredGigE0/0/0/24/3', 'HundredGigE0/0/0/7', 'TwentyFiveGigE0/0/0/16/1', 'HundredGigE0/0/0/8', 'HundredGigE0/0/0/10', 'HundredGigE0/0/0/5', 'TwentyFiveGigE0/0/0/18/0', 'HundredGigE0/0/0/24/1', 'TwentyFiveGigE0/0/0/18/2', 'HundredGigE0/0/0/22', 'HundredGigE0/0/0/25/1', 'HundredGigE0/0/0/24/0', 'TwentyFiveGigE0/0/0/10/3', 'HundredGigE0/0/0/11', 'TwentyFiveGigE0/0/0/16/0', 'HundredGigE0/0/0/25/0', 'TwentyFiveGigE0/0/0/8/3', 'HundredGigE0/0/0/9', 'HundredGigE0/0/0/24/2', 'TwentyFiveGigE0/0/0/8/2', 'TwentyFiveGigE0/0/0/16/3', 'HundredGigE0/0/0/21', 'TwentyFiveGigE0/0/0/18/1', 'HundredGigE0/0/0/6', 'HundredGigE0/0/0/25/3', 'TwentyFiveGigE0/0/0/10/0', 'TwentyFiveGigE0/0/0/18/3', 'HundredGigE0/0/0/13', 'TwentyFiveGigE0/0/0/8/1'] in both direction/s

```

The log contains the total number(n) of switch ports to be monitored and we would thus need (n/2) smartNICs to monitor these. (Since each smartNIC has 2 listening ports) <br>
However there may not be enough smartNICs available on a site. If so the NIC count requested will reduce <br>
```
port_count: {'UTAH': 38}
Not enough NIC cards available for site UTAH. Reducing NIC count from 19 to 6!!!

```
### Setup mirror links

The log include the mapping of listening node and the switch ports assigned to this node: <br>
```
Site: UTAH
 Node:
 -----------------  --------------------------------------------------------------------------------------------------------------------------------------------
ID
Name               UTAH_node0
Cores
RAM
Disk
Image              default_ubuntu_20
Image Type         qcow2
Host
Site               UTAH
Management IP
Reservation State
Error Message
SSH Command        ssh -i {{ _self_.private_ssh_key_file }} -F /home/nshyamkumar/work/fabric_config/ssh_config {{ _self_.username }}@{{ _self_.management_ip }}
-----------------  --------------------------------------------------------------------------------------------------------------------------------------------
 ['TwentyFiveGigE0/0/0/8/0', 'HundredGigE0/0/0/25/2', 'HundredGigE0/0/0/4', 'HundredGigE0/0/0/17', 'TwentyFiveGigE0/0/0/10/1', 'TwentyFiveGigE0/0/0/16/2']

```

It will also contain information on the mirror links requested (ie, from switch port to listener port): <br>
```
mirror interface name: HundredGigE0/0/0/25/2 mirrored to
 ---------------  --------------------------
Name             UTAH_node0-pmnic_6-p1		<---- listen on VM node0 and port1(p1) of the assigned NIC (pmnic_6).
Network          UTAH_UTAH_node0_pmservice0
Bandwidth        100
Mode             config
VLAN
MAC
Physical Device
Device
Address
Numa Node
Switch Port
---------------  --------------------------

```
### Slice submission

Submitting slice request to backend

### Submission success

On success the SSH parameters for the VMs will be printed <br>
```
UTAH_node0: ssh -i /home/nshyamkumar/.ssh/bastion//slice_key -F /home/nshyamkumar/.ssh/bastion//ssh_config ubuntu@2001:1948:417:7:f816:3eff:fe08:4041
UTAH_node1: ssh -i /home/nshyamkumar/.ssh/bastion//slice_key -F /home/nshyamkumar/.ssh/bastion//ssh_config ubuntu@2001:1948:417:7:f816:3eff:fec3:6a10
UTAH_node2: ssh -i /home/nshyamkumar/.ssh/bastion//slice_key -F /home/nshyamkumar/.ssh/bastion//ssh_config ubuntu@2001:1948:417:7:f816:3eff:fe61:2877
UTAH_node3: ssh -i /home/nshyamkumar/.ssh/bastion//slice_key -F /home/nshyamkumar/.ssh/bastion//ssh_config ubuntu@2001:1948:417:7:f816:3eff:feef:ca3f
UTAH_node4: ssh -i /home/nshyamkumar/.ssh/bastion//slice_key -F /home/nshyamkumar/.ssh/bastion//ssh_config ubuntu@2001:1948:417:7:f816:3eff:fe4f:7fe6
```
### Submission failure

On failure, the slice submission will return an exception with an error message
```
Closing
Setup exception: Slice Exception: Slice Name: Traffic Listening Demo UTAH, Slice ID: fcf990c1-bb7e-4cab-95e1-5a5cdc52a1e1: Slice Exception: Slice Name: Traffic Listening Demo UTAH, Slice ID: fcf990c1-bb7e-4cab-95e1-5a5cdc52a1e1: Node: UTAH_node0, Site: UTAH, State: None,
Slice Exception: Slice Name: Traffic Listening Demo UTAH, Slice ID: fcf990c1-bb7e-4cab-95e1-5a5cdc52a1e1: Slice Exception: Slice Name: Traffic Listening Demo UTAH, Slice ID: fcf990c1-bb7e-4cab-95e1-5a5cdc52a1e1: Node: UTAH_node0, Site: UTAH, State: None,
...
...
```

### Sampling initiate

The log for the sampling phase will display the commands being run on the VM node, as well as the time when tcpdump is initiated. <br> 
```
Initiating sampling phase
UTAH:./capture_packets.sh enp7s0 135 1 300 20 200 "all"		<--- Sampling with user provided parameters
UTAH:./capture_packets.sh enp8s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp7s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp8s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp7s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp8s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp7s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp8s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp7s0 135 1 300 20 200 "all"
UTAH:./capture_packets.sh enp8s0 135 1 300 20 200 "all"
end_command: ./end_detect.sh 45360
end_command: ./end_detect.sh 45360
end_command: ./end_detect.sh 45360
end_command: ./end_detect.sh 45360
end_command: ./end_detect.sh 45360
time_tcpdump_start 1732584373.3693376 seconds 			<---- Time tcpdump listen begins
total_sampling_time: 45360 seconds				<---- Total sampling time based on provided parameters
```
### Strobing phase

The strobing phase will contain information of the mirror link being brought down. <br>
```
Bringing network down in
 -------  ------------------------------------
ID       fb5c4fe1-dbdc-4ccb-b840-58c5977b7c09
Name     UTAH_UTAH_node0_pmservice0
Layer    L2
Type     PortMirror
Site     UTAH
Gateway
Subnet
State    Active
Error
-------  ------------------------------------

```

It also contains information on the new mirror link to be brought up: <br>
```
UTAH# mirror interface name: TwentyFiveGigE0/0/0/8/3 mirrored to
---------------  --------------------------
Name             UTAH_node4-pmnic_2-p1
Network          UTAH_UTAH_node4_pmservice8
Bandwidth        25
Mode             config
VLAN
MAC
Physical Device
Device
Address
Numa Node
Switch Port
---------------  --------------------------

```

During the entire strobing phase, periodically there will be timer information logged. <br>
```
time_since_sampling_start: 273.2554596699774     <--- Time since tcpdump started listening for packets
time_curr internal: 270.0000001974404		 <--- Time taken for 1 strobe operation

```
### Gathering and cleanup phase

In the end of the log, there will be logged the total experiment time, and other bookkeeping information <br>
```
Final experiment time: 689.4736372902989

 Initiating Gathering phase
 Gathering pcap files from VMs

Deleting the slice Traffic Listening Demo UTAH

Exiting from Traffic Listening Demo UTAH

```

