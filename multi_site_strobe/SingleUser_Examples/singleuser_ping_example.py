#!/usr/bin/env python
# coding: utf-8

# # Create a PortMirror service to snoop on dataplane traffic

# FABRIC provides a special PortMirror Network Service that allows experimenters to snoop on traffic in the dataplane. The service is limited to mirroring all traffic from one physical port on the dataplane switch in a FABRIC site, to another physical port on the same site. Any active port can be mirrored, regardless of whether it belongs to the user experiment or not. For this reason this service requires a __Net.PortMirror__ project permission tag on the project and granting this permission requires a review by the FABRIC team to ensure the project takes proper security precautions to prevent the misuse of this feature.
#
# In this notebook we demonstrate the process by creating two slices - one a FABNetv4 slice - this is the slice we are eavesdropping on and the other slice is the slice utilising PortMirror service to receive the traffic.

# ## Step 0: Import the FABlib Library

from ipaddress import ip_address, IPv4Address, IPv6Address, IPv4Network, IPv6Network
import twine_shm
import ipaddress
import os
import time
import sys

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

projectid = os.environ.get("PROJECT_ID")
fablib = fablib_manager(project_id=f"{projectid}")

print(f"fablib pm2n: {fablib}")
fablib.show_config()

# ## Step 1: Create the slice that generates traffic
# We will use the same approach as a [FABNetv4 full-auto notebook](../create_l3network_fabnet_ipv4_auto/create_l3network_fabnet_ipv4_auto.ipynb) here. The only difference is for better isolation we will use ConnectX-5 10/25Gbps SmartNICs as endpoints of the service.
#
# ### Initialize variables
# The following code is split up into two cells so they can be executed separately, if needed.


# find two available sites

# we will use CX5 to generate traffic and CX6 to mirror traffic into so need sites that have both for this example.
cx5_column_name = "nic_connectx_5_available"
cx6_column_name = "nic_connectx_6_available"

# find two sites with available ConnectX-5 and ConnectX-6 cards
(site1, site2) = fablib.get_random_sites(
    count=2, filter_function=lambda x: x[cx5_column_name] > 0 and x[cx6_column_name] > 0
)

#slice_name = "Traffic Generator Slice"
slice_name = "Traffic Generator Slice9"

# you can use the below line to override site locations
#site1, site2 = ("MASS", "RUTG")
site1, site2 = ("MASS", "ATLA")

print(f'Will create "{slice_name}" on {site1} and {site2}')

node1_name = "Node1"
node2_name = "Node2"

network1_name = "net1"
network2_name = "net2"


# ### Create the slice
print(f"Deleting slice {slice_name}")
try:
    fablib.delete_slice(slice_name)
except Exception as e:
    print(e)

# Create Traffic generator slice
print(f"Submitting slice {slice_name}")
slice = fablib.new_slice(name=slice_name)

# Networks
net1 = slice.add_l3network(name=network1_name, type="IPv4")
net2 = slice.add_l3network(name=network2_name, type="IPv4")

# Node1
node1 = slice.add_node(name=node1_name, site=site1)
iface1 = node1.add_component(model="NIC_ConnectX_5", name="nic1").get_interfaces()[0]
iface1.set_mode("auto")
net1.add_interface(iface1)
node1.add_route(subnet=fablib.FABNETV4_SUBNET, next_hop=net1.get_gateway())

# Node2
node2 = slice.add_node(name=node2_name, site=site2)
iface2 = node2.add_component(model="NIC_ConnectX_5", name="nic1").get_interfaces()[0]
iface2.set_mode("auto")
net2.add_interface(iface2)
node2.add_route(subnet=fablib.FABNETV4_SUBNET, next_hop=net2.get_gateway())

# Submit Slice Request
slice.submit()

# ### Query the slice
# You can re-execute this cell any time you need to remember what the traffic generator slice looks like.
slice = fablib.get_slice(slice_name)

node1 = slice.get_node(name=node1_name)
node2 = slice.get_node(name=node2_name)

site1 = node1.get_site()
site2 = node2.get_site()

node1_addr = node1.get_interface(network_name=f"{network1_name}").get_ip_addr()
node2_addr = node2.get_interface(network_name=f"{network2_name}").get_ip_addr()

slice.list_nodes()
slice.list_networks()
print(f"Node1 FABNetV4 IP Address is {node1_addr}")
print(f"Node2 FABNetV4 IP Address is {node2_addr}")


# ### Test the slice
#
# Let's make sure the two nodes can communicate as expected.
slice = fablib.get_slice(slice_name)

node1 = slice.get_node(name=node1_name)
node2 = slice.get_node(name=node2_name)

node2_addr = node2.get_interface(network_name=network2_name).get_ip_addr()

stdout, stderr = node1.execute(f"ping -c 5 {node2_addr}")


# ## Step 2: Create the slice that listens in
#
# We'll pick the first site of the two selected for the Traffic Generator Slice and create a single VM connected to a PortMirror network service that listens in on the other slice.
#
# We will introspect into the Traffic Generator Slice topology to get the name of the port to which node1's SmartNIC is connected to.

# let's see if the traffic generator slice topology provided us with the port name

# The switch port connected to node1 NIC aka peer port.
mirror_port_name = node1.get_interfaces()[0].get_peer_port_name()

if not mirror_port_name:
    print(
        "Can't proceed as the traffic generator topology did not provide the name of the port to mirror"
    )
    fablib.delete_slice(slice_name)
    sys.exit(1)

listener_site = site1
print(f"{listener_site} listening to port {mirror_port_name}")


# Now we can create the listening slice
time_to_run=150

init_node_cnt = 0
init_nodes = slice.get_nodes()
for node in init_nodes:
    init_node_cnt += 1

shm_name, shm_p = twine_shm.create_sharedmem()

print(f"init_node_cnt is {init_node_cnt}")
print("Running Twine")
mode="single_user"
workdir = os.environ.get("WORKDIR")
os.system(f"{workdir}/multi_site_twine.sh {mode} {site1} {mirror_port_name} \"{slice_name}\" \"{shm_name}\"")

twine_shm.synch_twine("start", shm_p, 400)

# ## Run the experiment
#
# As a trivial experiment we start a `ping` between the two nodes in the Traffic Generator Slice and see if we can see it in the Lister Slice.
slice = fablib.get_slice(slice_name)

node1 = slice.get_node(name=node1_name)
node2 = slice.get_node(name=node2_name)

node2_addr = node2.get_interface(network_name=network2_name).get_ip_addr()

# run everything for 10 seconds
traffic_command = f"timeout {time_to_run}s ping -c {time_to_run} {node2_addr}"

print("Starting ping")
# start traffic generation in the background
node2_thread = node1.execute_thread(traffic_command, output_file="node1_ping.log")

# check for errors
stdout, stderr = node2_thread.result()
if stderr and len(stderr):
    print(f"Error output from Traffic Generator Slice: {stderr}")

print("Ending ping")

print("Checking if slice can be deleted")

#print("Ending Node2")
#node2.delete()


twine_shm.synch_twine("stop", shm_p, 400)
twine_shm.remove_sharedmem(shm_p)

slice_nodes = slice.get_nodes()
for node in slice_nodes:
    print(f"User program: {node}")
# ## Delete slice
try:
    fablib.delete_slice(slice_name)
except Exception as e:
    print(e)

print("Done")
