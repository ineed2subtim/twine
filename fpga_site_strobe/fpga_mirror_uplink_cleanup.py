from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import logging
import sys
import argparse
import os

projectid = os.environ.get("PROJECT_ID")
fabricrc = os.environ.get("FABRIC_RC")
fablib = fablib_manager(fabric_rc=f"{fabricrc}", project_id=f"{projectid}")
fablib.show_config()

parser = argparse.ArgumentParser(description="Specify site to monitor")
parser.add_argument("site", type=str, help="name of site")
args = parser.parse_args()

listener_slice_name = f"FPGA Listening Slice {args.site}"
listener_sites = []
listener_node_name = {}
listener_direction = {}
listener_nodes = {}

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)



file_handler = logging.FileHandler(f"{args.site}/fpga_mirror_uplink_cleanup.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)
logging.info(args)

pmslice = fablib.get_slice(name=listener_slice_name)
pmslice.show()
sites = set()
for node in pmslice.get_nodes():
    logging.info(node.get_name())
    logging.info(node.get_ssh_command())
    sites.add(node.get_site())
    try:
        listener_node_name[node.get_site()].append(node.get_name())
        listener_nodes[node.get_site()].append(node)
    except:
        listener_node_name[node.get_site()] = [node.get_name()]
        listener_nodes[node.get_site()] = [node]
listener_sites = list(sites)

commands = [f"cd esnet-smartnic-fw/sn-stack/; docker compose down --remove-orphans "]

for listener_site in listener_sites:
    for i in range(0, len(listener_nodes[listener_site])):
        listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
        for command in commands:
            logging.info(f"Executing {command}")
            stdout, stderr = listener_node.execute(command)

pmslice = fablib.get_slice(name=listener_slice_name)
logging.info(pmslice.get_lease_end())

try:
    fablib.delete_slice(listener_slice_name)
    os.remove(f"{args.site}/checkpoint.json")
except Exception as e:
    logging.info(e)
