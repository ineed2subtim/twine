from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager
import os
import argparse
import sys
import json
import logging
import time

def load_checkpoint():
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            try:
                return json.load(f).get("last_checkpoint", None)
            except:
                return None
    return None


# Save checkpoint
def save_checkpoint(checkpoint):
    with open(checkpoint_file, "w") as f:
        json.dump({"last_checkpoint": checkpoint}, f)


projectid = os.environ.get("PROJECT_ID")
fabricrc = os.environ.get("FABRIC_RC")
fablib = fablib_manager(fabric_rc=f"{fabricrc}", project_id=f"{projectid}")
fablib.show_config()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)


parser = argparse.ArgumentParser(description="Specify site to monitor")
parser.add_argument("site", type=str, help="name of site")
parser.add_argument("--dry-run", action="store_true", help="dry run, not creating slice")
parser.add_argument(
    "--extend", action="store_true", help="extend slice, cannot be used with dryrun"
)
parser.add_argument("--time", type=int, help="time in seconds for strobing", default=60)
args = parser.parse_args()
args.site = args.site.upper()
if args.dry_run:
    args.extend = False

file_handler = logging.FileHandler(f"{args.site}/fpga_mirror_uplink.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

logger.info(f"site: {args.site}")
logger.info(f"time: {args.time} seconds")
logger.info(f"extended: {args.extend}")
logger.info(f"dry-run: {args.dry_run}")

checkpoint_file = f"{args.site}/checkpoint.json"

listener_slice_name = f"FPGA Listening Slice {args.site}"
fpga_column_name = "fpga_u280_available"
cx6_column_name = "nic_connectx_6_available"
cx5_column_name = "nic_connectx_5_available"

listener_sites = []
listener_node_name = {}
listener_direction = {}
listener_nodes = {}

last_checkpoint = load_checkpoint()
logger.info(f"Last checkpoint: {last_checkpoint}")
if last_checkpoint is not None:
    logger.info(f"last_checkpoint {last_checkpoint}")
    pmslice = fablib.get_slice(name=listener_slice_name)
    pmslice.show()
    sites = set()
    for node in pmslice.get_nodes():
        logger.info(node.get_name())
        logger.info(node.get_ssh_command())
        sites.add(node.get_site())
        try:
            listener_node_name[node.get_site()].append(node.get_name())
            listener_nodes[node.get_site()].append(node)
        except:
            listener_node_name[node.get_site()] = [node.get_name()]
            listener_nodes[node.get_site()] = [node]

    listener_sites = list(sites)
    logger.info(listener_sites)
    logger.info(listener_node_name)
else:
    listener_sites.append(args.site)
    sites_connectx_name = []
    sites_connectx_json = fablib.list_sites(
        output="json", quiet="false", filter_function=lambda x: x[fpga_column_name] > 0
    )
    sites_connectx = json.loads(sites_connectx_json)
    # Convert json output to list of site names
    for elem in sites_connectx:
        sites_connectx_name.append(elem["name"])
    logger.info(sites_connectx_name)

    for site in listener_sites:
        if site not in sites_connectx_name:
            logger.info(f"ERROR: {site} does not have any FPGA U280 cards available")
            listener_sites.remove(site)
            sys.exit()

    logger.info(f"final listener sites are {listener_sites}")

    fablib.get_resources()
    exclude_list = ("EDC", "AWS", "AL2S", "Azure", "GCP", "Azure-Gov")
    mirror_port_list = {}
    port_count = {}
    for site_name, site_details in fablib.get_resources().topology.nodes.items():
        if site_name in exclude_list:
            continue
        if site_name not in listener_sites:
            continue
        list_site = []
        port_count[site_name] = 0

        for intf, details in site_details.interfaces.items():
            # logger.info(f'  {intf=} ---> {details.labels.local_name}')
            port_name = details.labels.local_name.split(".")[0]
            # Vlans
            if port_name not in list_site and port_name[:6] != "Bundle":
                list_site.append(port_name)
                port_count[site_name] = port_count[site_name] + 1

        if len(list_site) > 0:
            set_site = set(list_site)
            list_site = list(set_site)

            mirror_port_list[site_name] = list_site

    logger.info(mirror_port_list)

    # logger.info listener site information
    for listener_site in listener_sites:
        listener_node_name[listener_site] = []
        listener_direction[listener_site] = "both"  # can also be 'rx' and 'tx'

        # let's see if the traffic generator slice topology provided us with the port name
        if not mirror_port_list[listener_site]:
            logger.info(
                "Can't proceed as the traffic generator topology did not provide the name of the port to mirror"
            )

        logger.info(
            f"Will create slice {listener_slice_name} on {listener_site} listening to ports {mirror_port_list[listener_site]}"
        )

    import math

    image = "docker_ubuntu_20"
    listener_cores = 8
    listener_ram = 16
    listener_disk = 100
    # Create listening slice
    pmslice = fablib.new_slice(name=listener_slice_name)

    listener_interfaces = {}

    for listener_site in listener_sites:
        listener_nodes[listener_site] = []
        c5_avail = 0
        c6_avail = 0
        port_ceil = math.ceil(port_count[listener_site] / 2)

        # Ensure that there are enough dedicated NICs to listen on.
        for elem in sites_connectx:
            if elem["name"] == listener_site:
                fpga_avail = elem[fpga_column_name]
                logger.info(f"fpga_avail: {fpga_avail}")
                if fpga_avail < port_ceil:
                    port_ceil = fpga_avail
                    port_count[listener_site] = port_ceil * 2
                    logger.info(
                        f"Not enough FPGA cards available for site {listener_site}. Reducing port count!!!"
                    )
                    # sys.exit()

        # Add a listening VM per FPGA
        for i in range(0, port_ceil):
            # , cores=listener_cores, ram=listener_ram, disk=listener_disk
            listener_node_name[listener_site].append(f"{listener_site}_node{i}")
            listener_nodes[listener_site].append(
                pmslice.add_node(
                    name=listener_node_name[listener_site][i],
                    site=listener_site,
                    image=image,
                    ram=listener_ram,
                    cores=listener_cores,
                    disk=listener_disk,
                )
            )

        i = 0
        while port_ceil > 0:
            interface_list = []
            if fpga_avail > 0:
                interface_list = (
                    listener_nodes[listener_site][i]
                    .add_component(model="FPGA_Xilinx_U280", name=f"pmnic_{port_ceil}")
                    .get_interfaces()
                )
                fpga_avail = fpga_avail - 1
                listener_interfaces[listener_node_name[listener_site][i]] = interface_list[:]

            port_ceil = port_ceil - 1
            i = i + 1

    pmnet = {}
    num_services = {}
    listener_pmservice_name = {}
    for listener_site in listener_sites:
        pmnet[listener_site] = []
        i = 0
        j = 0
        num_mirror_ports = port_count[listener_site]

        for listener_node in listener_nodes[listener_site]:
            k = 0
            listener_pmservice_name[listener_node] = []
            for listener_interface in listener_interfaces[listener_node_name[listener_site][j]]:
                if i < num_mirror_ports:
                    listener_pmservice_name[listener_node].append(
                        f"{listener_site}_{listener_node_name[listener_site][j]}_pmservice{i}"
                    )
                    pmnet[listener_site].append(
                        pmslice.add_port_mirror_service(
                            name=listener_pmservice_name[listener_node][k],
                            mirror_interface_name=mirror_port_list[listener_site][i],
                            receive_interface=listener_interface,
                            mirror_direction=listener_direction[listener_site],
                        )
                    )
                    i = i + 1
                    k = k + 1

            j = j + 1
            num_services[listener_node] = k

    if not args.dry_run:
        try:
            logger.info("Submitting slice {listener_slice_name}")
            pmslice.submit(progress=True, wait_timeout=2400, wait_interval=120)
            if pmslice.get_state() == "StableError":
                raise Exception("Slice state is StableError")
        except Exception as e:
            logger.info(e)
            fablib.delete_slice(listener_slice_name)
    else:
        exit(0)

    if args.extend:
        from datetime import datetime, timedelta
        from dateutil import tz

        try:
            pmslice = fablib.get_slice(name=listener_slice_name)
            end_date = (datetime.now(tz=tz.tzutc()) + timedelta(days=2)).strftime(
                "%Y-%m-%d %H:%M:%S %z"
            )
            pmslice.renew(end_date)
        except Exception as e:
            logger.info(f"Exception: {e}")

    # save config as checkpoint
    save_checkpoint("config")

if load_checkpoint() == "config":
    commands = list()
    commands.append(
        'sudo sed -i \'s/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="amd_iommu=on iommu=pt default_hugepagesz=1G hugepagesz=1G hugepages=16"/\' /etc/default/grub'
    )
    commands.append("sudo grub-mkconfig -o /boot/grub/grub.cfg")
    commands.append("sudo update-grub")
    commands.append("lspci | grep -i Xilinx")
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            listener_ssh = listener_node.get_ssh_command()
            for command in commands:
                logger.info(f"Executing {command}")
                logger.info(f"Listener SSH {listener_ssh}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")
    logger.info("Done")
    save_checkpoint("grub")

if load_checkpoint() == "grub":
    reboot = "sudo reboot"
    logger.info(reboot)
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            stdout, stderr = listener_node.execute(reboot)
            logger.info(f"{stdout} \n {stderr} \n")
    pmslice.wait_ssh(timeout=360, interval=10, progress=True)
    logger.info("Now testing SSH abilites to reconnect...")
    pmslice.update()
    pmslice.test_ssh()
    logger.info("Reconnected!")

    commands = list()
    commands = [
        "dmesg | grep -i IOMMU",
        "lspci | grep -i Xilinx",
    ]
    logger.info(
        "Observe that the modifications to boot configuration took place and IOMMU is detected"
    )
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                listener_node.execute(command)
            listener_node.config()
    save_checkpoint("reboot")

if load_checkpoint() == "reboot":
    command = "echo 1 | sudo tee /sys/module/vfio/parameters/enable_unsafe_noiommu_mode"
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            stdout, stderr = listener_node.execute(command)
            logger.info(f"{stdout} \n {stderr} \n")
    save_checkpoint("iommu")

if load_checkpoint() == "iommu":
    commands = [
        "sudo usermod -G docker ubuntu",
        "mkdir -p ~/.docker/cli-plugins/",
        "curl -SL https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose",
        "chmod +x ~/.docker/cli-plugins/docker-compose",
        "curl -SL https://github.com/docker/buildx/releases/download/v0.11.2/buildx-v0.11.2.linux-amd64 -o ~/.docker/cli-plugins/docker-buildx",
        "chmod +x ~/.docker/cli-plugins/docker-buildx",
        "docker compose version",
        "docker container ps",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])

            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")
    logger.info("Done")
    save_checkpoint("install_docker_compose")

if load_checkpoint() == "install_docker_compose":
    commands = [
        "docker pull gitlab-registry.nrp-nautilus.io/esnet/xilinx-labtools-docker && \
    docker tag gitlab-registry.nrp-nautilus.io/esnet/xilinx-labtools-docker xilinx-labtools-docker:ubuntu-dev"
    ]
    # ,"docker pull gitlab-registry.nrp-nautilus.io/esnet/smartnic-dpdk-docker && \
    # docker tag gitlab-registry.nrp-nautilus.io/esnet/smartnic-dpdk-docker smartnic-dpdk-docker:ubuntu-dev"

    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
    dockerfile = "Dockerfile"
    commands = [
        "git clone https://github.com/esnet/smartnic-dpdk-docker.git",
        "cp Dockerfile smartnic-dpdk-docker/",
        "cd smartnic-dpdk-docker/; git submodule update --init --recursive; \
                docker build --pull -t smartnic-dpdk-docker:${USER}-dev . ",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            result = listener_node.upload_file(dockerfile, dockerfile)
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                #logger.info(f"{stderr} \n")
    save_checkpoint("build_docker_images")

if load_checkpoint() == "build_docker_images":
    artifact = "artifacts.au280.twine_alveo.0.zip"
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            listener_node.upload_file(artifact, artifact)
    save_checkpoint("upload_artifact")

if load_checkpoint() == "upload_artifact":
    SN_HW_APP_NAME = "twine_alveo"
    env_file = """
    SN_HW_VER=0
    SN_HW_BOARD=au280
    SN_HW_APP_NAME=twine_alveo
    """
    artifact = "artifacts.au280.twine_alveo.0.zip"
    commands = [
        "git clone https://github.com/esnet/esnet-smartnic-fw.git",
        "cd ~/esnet-smartnic-fw; git checkout c064d4ac775ed1a4c50ec72dea3615f9c644433e",  # c064d... is needed to work with truncation on smartnic-hw
        "cd ~/esnet-smartnic-fw; git submodule init; git submodule update",
        f"cp ~/{artifact} ~/esnet-smartnic-fw/sn-hw/",
        f"echo '{env_file}' | sudo tee ~/esnet-smartnic-fw/.env",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")

    command = "docker image ls"
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            logger.info(f"Executing 'cd ~/esnet-smartnic-fw/; ./build.sh'")
            node_thread = listener_node.execute_thread(
                "cd ~/esnet-smartnic-fw/; ./build.sh", output_file="esnet-smartnic-fw-docker.log"
            )
            stdout, stderr = node_thread.result()
            logger.info(f"Executing {command}")
            stdout, stderr = listener_node.execute(command)
            logger.info(f"{stdout} \n {stderr} \n")
    save_checkpoint("build_esnet-smartnic-fw")

if load_checkpoint() == "build_esnet-smartnic-fw":
    env_file = """
    FPGA_PCIE_DEV=0000:1f:00
    COMPOSE_PROFILES=smartnic-mgr-dpdk-manual
    """
    commands = [f"echo '{env_file}' | tee -a ~/esnet-smartnic-fw/sn-stack/.env"]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")

    commands = [
        "cd ~/esnet-smartnic-fw/sn-stack; docker compose up -d",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")

    commands = [
            "docker ps | grep smartnic-dpdk-docker | wc -l",
            "docker ps | grep esnet-smartnic-fw | wc -l",
            "docker ps | grep xilinx-labtools-docker | wc -l",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            for command in commands:
                stdout, stderr = listener_node.execute(command)
                if int(stdout) == 0:
                    logger.info(f"{command} failed to produce output. Exiting!!!")
                    logger.info(stderr)
                    sys.exit(0)

    save_checkpoint("docker_compose_up")

if load_checkpoint() == "docker_compose_up":
    dpdk_app_script = "dpdk_app_script"
    commands = [
        f"chmod a+x {dpdk_app_script}",
        f" mv {dpdk_app_script} ~/esnet-smartnic-fw/sn-stack/scratch",
        f"cd esnet-smartnic-fw/sn-stack/; docker compose exec smartnic-dpdk scratch/{dpdk_app_script} ",
    ]

    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            result = listener_node.upload_file(dpdk_app_script, dpdk_app_script)
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")

    sn_cli_script = "sn-cli-setup"
    cli_command_script = "cli_command.txt"

    commands = [
        f"chmod a+x {sn_cli_script}",
        f"cp {sn_cli_script} ~/esnet-smartnic-fw/sn-stack/scratch",
        f"cd ~/esnet-smartnic-fw/sn-stack/; docker compose exec smartnic-fw scratch/{sn_cli_script}",
        f"chmod a+x {cli_command_script}",
        f"cp {cli_command_script} ~/esnet-smartnic-fw/sn-stack/scratch",
        f"cd ~/esnet-smartnic-fw/sn-stack/; docker compose exec smartnic-fw sn-p4-cli clear-all; docker compose exec smartnic-fw sn-p4-cli p4bm-apply scratch/{cli_command_script}",
    ]
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            result = listener_node.upload_file(sn_cli_script, sn_cli_script)
            result = listener_node.upload_file(cli_command_script, cli_command_script)
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")
    save_checkpoint("start_dpdk_app")

if load_checkpoint() == "start_dpdk_app":
    time.sleep(args.time)
    dpdk_stop_script = "dpdk_stop_app"
    commands = [
        f"chmod a+x {dpdk_stop_script}",
        f" mv {dpdk_stop_script} ~/esnet-smartnic-fw/sn-stack/scratch",
        f"cd esnet-smartnic-fw/sn-stack/; docker compose exec smartnic-dpdk scratch/{dpdk_stop_script} ",
        f"sudo rm -rf ~/output",
        f"sudo mv /home/ubuntu/esnet-smartnic-fw/sn-stack/scratch/output .",
        f" sudo chown -R ubuntu:ubuntu output/",
    ]

    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            result = listener_node.upload_file(dpdk_stop_script, dpdk_stop_script)
            for command in commands:
                logger.info(f"Executing {command}")
                stdout, stderr = listener_node.execute(command)
                logger.info(f"{stdout} \n {stderr} \n")

    output = "output/"
    local_output = f"{args.site}/output/"
    for listener_site in listener_sites:
        for i in range(0, len(listener_nodes[listener_site])):
            listener_node = pmslice.get_node(name=listener_node_name[listener_site][i])
            result = listener_node.download_directory(local_output, output)
    save_checkpoint("stop_dpdk_app")
