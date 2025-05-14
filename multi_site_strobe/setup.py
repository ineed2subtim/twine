import sys
import random
import math
import pw_logging as log


# Method: For each site, obtain listener NICs and return the worker nodes that house them
def get_worker_node_resource(current_site, fablib):
    host_with_smartnics = []
    for site_name, site in fablib.get_resources().sites.items():
        if site_name == current_site:
            for host_name, host in site.get_hosts().items():
                host_dict = host.to_dict()
                if (
                    host_dict["nic_connectx_5_available"] > 0
                    or host_dict["nic_connectx_6_available"] > 0
                ):
                    host_with_smartnics.append(host_dict)
    return host_with_smartnics


# Method: Set weights for each switch port, and split these switch ports amongst both NIC listener ports.
def set_weight_and_split(temp_list, mod_port_list, listener_site, node_name):
    split_idx = int(len(mod_port_list[listener_site][node_name]) / 2)
    m = -1
    k = 0
    for i in range(0, len(temp_list)):
        if i % 2 == 0:
            m += 1
            k = 5 - 2 * m  # Represents the weight(importance) of the port
            if k < 0:
                k = 1
            # Entry is [port_name, current weight, original weight]
            mod_port_list[listener_site][node_name][m + split_idx] = [temp_list[i], k, k]
        else:
            mod_port_list[listener_site][node_name][m] = [temp_list[i], k, k]


# Method: Identify required resources for the listening slice and submit request
def setup_slice(
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
):
    # Listening VM requested resource
    image = "default_ubuntu_20"
    listener_cores = 2
    listener_ram = 8
    listener_disk = 100

    if op_mode == "operator":
        pmslice = fablib.new_slice(name=listener_slice_name)
    else:
        pmslice = fablib.get_slice(name=listener_slice_name)
    listener_interfaces = {}

    # Get minimum of available ports to mirror and available listener NICS.
    for listener_site in listener_sites:
        mod_port_list[listener_site] = {}
        listener_nodes[listener_site] = {}
        c5_avail = 0
        c6_avail = 0
        port_ceil = math.ceil(port_count[listener_site] / 2)
        # port_ceil = 1
        # Ensure that there are enough dedicated NICs to listen on.
        for elem in sites_connectx:
            if elem["name"] == listener_site:
                c5_avail = elem["nic_connectx_5_available"]
                log.log(log.INFO, f"{listener_site} c5_avail: {c5_avail}")
                c6_avail = elem["nic_connectx_6_available"]
                log.log(log.INFO, f"{listener_site} c6_avail: {c6_avail}")
                with open(startup_log_file, "a") as slog:
                    slog.write(f"c5_avail: {c5_avail}\n  c6_avail: {c6_avail}\n")
                    slog.close()
                if (c5_avail + c6_avail) < port_ceil:
                    port_ceil_old = port_ceil
                    port_ceil = c5_avail + c6_avail
                    log.log( 
                        log.INFO,
                        f"Not enough NIC cards available for site {listener_site}. Reducing NIC count from {port_ceil_old} to {port_ceil}!!!"
                    )
                    with open(startup_log_file, "a") as slog:
                        slog.write(
                            f"Not enough NIC cards available for site {listener_site}. Reducing NIC count from {port_ceil_old} to {port_ceil}!!!\n"
                        )
                        slog.close()

        port_ceil_old = port_ceil
        # To overcome node allocation failures due to insufficient resources
        port_ceil = port_ceil - port_reduce_count

        if port_ceil < 0:  # Safety check
            port_ceil = 0
        if port_ceil_old != port_ceil:
            log.log( 
                log.INFO,
                f"To overcome node allocation failure on site {listener_site}, reducing port count from {port_ceil_old} to {port_ceil}!!!"
            )
            with open(startup_log_file, "a") as slog:
                slog.write(
                    f"To overcome node allocation failure on site {listener_site}, reducing port count from {port_ceil_old} to {port_ceil}!!!\n"
                )
                slog.close()
        log.log(log.DEBUG, f" port_ceil = {port_ceil}")

        if port_ceil == 0:
            with open(startup_log_file, "a") as slog:
                slog.write(f"Exiting due to no available ports!!!\n")
                slog.close()
            sys.exit(1)

        # Split a single set of 'n' mirrorable ports into --> 'port_ceil' sets of 'modulo_val' ports
        modulo_val = int(port_count[listener_site] / port_ceil)
        log.log(log.DEBUG, modulo_val)
        listener_node_name[listener_site] = []
        listener_nodes[listener_site] = []

        # Get resource availability on SmartNIC hosts
        host_with_smartnics = get_worker_node_resource(listener_site, fablib)
        log.log(log.DEBUG, f"listener_site: {listener_site}")
        for host in host_with_smartnics:
            total_nics_on_host = host["nic_connectx_5_available"] + host["nic_connectx_6_available"]
            if total_nics_on_host * listener_ram > host["ram_available"]:
                log.log(log.INFO, f'RAM unavailable on {host["name"]}')
            if total_nics_on_host * listener_disk > host["disk_available"]:
                log.log(log.INFO, f'Storage unavailable on {host["name"]}')
            if total_nics_on_host * listener_cores > host["cores_available"]:
                log.log(log.INFO, f'Cores unavailable on {host["name"]}')
            with open(startup_log_file, "a") as slog:
                slog.write(f"Host: {host} \n")
                slog.write(f'ram_available: {host["ram_available"]}\n')
                slog.write(f'disk_available: {host["disk_available"]}\n')
                slog.write(f'cores_available: {host["cores_available"]}\n\n')
                slog.close()

        # Add a listening VM per smartNIC and create port list set(each containing modulo_val ports) for that VM
        for i in range(0, port_ceil):
            num_vms = i
            node_name = f"Twine_{listener_site}_node{i}"
            listener_node_name[listener_site].append(node_name)
            log.log(log.DEBUG, listener_node_name[listener_site])
            listen_node = pmslice.add_node(
                name=listener_node_name[listener_site][i],
                site=listener_site,
                image=image,
                ram=listener_ram,
                cores=listener_cores,
                disk=listener_disk,
            )
            listener_nodes[listener_site].append(listen_node)

            # Each VM listens to a set of modulo_val ports, to avoid port mirror conflicts
            mod_port_list[listener_site][node_name] = []
            j = i
            while j < port_count[listener_site]:
                mod_port_list[listener_site][node_name].append(mirror_port_list[listener_site][j])
                j += port_ceil

            # Split the ports such that the most busy ports are spread across the VM NIC's 2 ports
            # e.g. if the 5 busiest ports are [A, B, C, D, E] and there are 2 listener NIC ports, then this code
            # splits it as port1 will listen to [A C E] and  port2 will listen to [B D]

            temp_list = mod_port_list[listener_site][node_name].copy()

            set_weight_and_split(temp_list, mod_port_list, listener_site, node_name)

            """
            # To account for final port which falls outside the python range functions inclusiveness
            if num_vms == port_ceil - 1 :
                final_port_idx = num_vms * modulo_val + modulo_val
                if final_port_idx < port_count[listener_site]:
                    mod_port_list[listener_site][node_name].append(mirror_port_list[listener_site][final_port_idx])

            """
            """
            #Old Mechanism of splitting ports among VMs
            for j in range(num_vms * modulo_val, num_vms * modulo_val + modulo_val):
                if j < port_count[listener_site]:
                    mod_port_list[listener_site][node_name].append(mirror_port_list[listener_site][j])
            # To account for final port which falls outside the python range functions inclusiveness
            if num_vms == port_ceil - 1 :
                final_port_idx = num_vms * modulo_val + modulo_val
                if final_port_idx < port_count[listener_site]:
                    mod_port_list[listener_site][node_name].append(mirror_port_list[listener_site][final_port_idx])
            """
            with open(startup_log_file, "a") as slog:
                slog.write(
                    f"Site: {listener_site}\n Node:\n {listen_node}\n {mod_port_list[listener_site][node_name]}\n\n"
                )
                # slog.write("-" * 80 + "\n")
                slog.close()
        # Assign NICs to VMs; Prefer cx6 NICs first
        i = 0
        while port_ceil > 0:
            interface_list = []
            if c6_avail > 0:
                interface_list = (
                    listener_nodes[listener_site][i]
                    .add_component(model="NIC_ConnectX_6", name=f"pmnic_{port_ceil}")
                    .get_interfaces()
                )
                c6_avail = c6_avail - 1
                listener_interfaces[listener_node_name[listener_site][i]] = interface_list[:]
            else:
                interface_list = (
                    listener_nodes[listener_site][i]
                    .add_component(model="NIC_ConnectX_5", name=f"pmnic_{port_ceil}")
                    .get_interfaces()
                )
                c5_avail = c5_avail - 1
                listener_interfaces[listener_node_name[listener_site][i]] = interface_list[:]
            port_ceil = port_ceil - 1
            i = i + 1

    # port mirroring is a network service of a special kind
    # it mirrors one or both directions of traffic ('rx', 'tx' or 'both') of a port that we identified in
    # Traffic Generator Topology into a port of a card we allocated in this slice (listener_interface)
    # NOTE: if you select 'both' directions that results in potentially 200Gbps of traffic, which
    # of course is impossible to fit into a single 100Gbps port of a ConnectX_6 card - be mindful of the
    # data rates.

    pmnet = {}
    random.seed(None, 2)
    # Create a port mirror channel for each VM from: NIC port on VM as the sink <---- 1 port from 1 set of modulo_val ports as source
    for listener_site in listener_sites:
        pmnet[listener_site] = []
        # To keep track of ports mirrored on each site, within the port list
        ports_mirrored[listener_site] = 0
        j = 0
        max_active_ports = port_count[listener_site]
        for listener_node in listener_nodes[listener_site]:
            num_pmservices[listener_node] = 0

        for listener_node in listener_nodes[listener_site]:
            k = 0
            listener_interface_idx = 0
            ports_mirrored_node = 0
            listener_pmservice_name[listener_node] = []
            node_name = listener_node_name[listener_site][j]
            # Each node(VM) monitors an assigned fraction of the total available ports.
            avail_port_node_maxcnt = len(mod_port_list[listener_site][node_name])

            for listener_interface in listener_interfaces[node_name]:
                if avail_port_node_maxcnt >= 2:
                    if listener_interface_idx % 2 == 0:
                        # first listener interface of NIC randomizes within the first half
                        random_index = random.randint(0, int(avail_port_node_maxcnt / 2 - 1))
                    else:
                        # second listener interface randomizes within the second half
                        random_index = random.randint(
                            int(avail_port_node_maxcnt / 2), avail_port_node_maxcnt - 1
                        )
                else:
                    random_index = 0
                listener_interface_idx += 1
                if (
                    ports_mirrored[listener_site] < max_active_ports
                    and ports_mirrored_node < avail_port_node_maxcnt
                ):
                    listener_pmservice_name[listener_node].append(
                        f"{listener_site}_{node_name}_pmservice{ports_mirrored[listener_site]}"
                    )
                    pmnet[listener_site].append(
                        pmslice.add_port_mirror_service(
                            name=listener_pmservice_name[listener_node][k],
                            mirror_interface_name=mod_port_list[listener_site][node_name][
                                random_index
                            ][0],
                            receive_interface=listener_interface,
                            mirror_direction=listener_direction[listener_site],
                        )
                    )
                    mod_port_list[listener_site][node_name][random_index][1] -= 1
                    with open(startup_log_file, "a") as slog:
                        slog.write(
                            f"{listener_site}# {mod_port_list[listener_site][node_name][random_index][0]}'s current weight: {mod_port_list[listener_site][node_name][random_index][1]}\n"
                        )
                        slog.write(
                            f"{listener_site}# {mod_port_list[listener_site][node_name][random_index][0]}'s original weight: {mod_port_list[listener_site][node_name][random_index][2]}\n"
                        )
                        slog.write(
                            f"mirror interface name: {mod_port_list[listener_site][node_name][random_index][0]} mirrored to\n {listener_interface} \n\n"
                        )
                        slog.close()
                    ports_mirrored[listener_site] = ports_mirrored[listener_site] + 1
                    ports_mirrored_node += 1
                    k = k + 1
                else:
                    with open(startup_log_file, "a") as slog:
                        slog.write(f"No more ports available for mirroring\n")
                        slog.close()
                        break

            j = j + 1
            num_pmservices[listener_node] = k  # Track mirrored port count per VM
    log.log(log.INFO, listener_nodes)
    return modulo_val, pmslice, listener_interfaces
