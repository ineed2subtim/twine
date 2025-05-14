import time
import sys
import random
import pw_logging as log


def strobe_bringdown(
    fablib,
    listener_sites,
    startup_log_file,
    listener_nodes,
    listener_pmservice_name,
    pmslice,
    bring_down_port_group,
):
    # Bring down half the mirrored ports
    for listener_site in listener_sites:
        with open(startup_log_file, "a") as slog:
            slog.write("-" * 80 + "\n")
            slog.write("-" * 80 + "\n")
            slog.close()
        for listener_node in listener_nodes[listener_site]:
            # Get list of listening interfaces on the node and delete the pmservices associated with it.
            for port_idx in range(0, len(listener_pmservice_name[listener_node])):
                if port_idx % 2 == bring_down_port_group:
                    network = pmslice.get_network(
                        name=listener_pmservice_name[listener_node][port_idx]
                    )
                    # log.log(log.DEBUG, network)
                    with open(startup_log_file, "a") as slog:
                        slog.write(f"Bringing network down in \n {network}\n")
                        slog.close()
                    network.delete()
                    log.log(log.DEBUG, listener_pmservice_name[listener_node][port_idx])
        with open(startup_log_file, "a") as slog:
            slog.write("\n\n\n")
            slog.close()

    bringdown_submit_start = time.time()
    with open(startup_log_file, "a") as slog:
        slog.write(f"bringdown_submit_start: {bringdown_submit_start} seconds\n")
        slog.close()
    # Request the above modification
    sliceid = pmslice.submit(progress=True, wait_timeout=1200, wait_interval=120)
    with open(startup_log_file, "a") as slog:
        slog.write(f"sliceid bringup: {sliceid}\n")
        slog.close()
    log.log(log.DEBUG, f"sliceid: {sliceid}")
    with open(startup_log_file, "a") as slog:
        slog.write("Brought down half the mirror networks\n")
        slog.close()

    bringdown_submit_stop = time.time()
    with open(startup_log_file, "a") as slog:
        slog.write(
            f"bringdown_submit_stop: {bringdown_submit_stop - bringdown_submit_start} seconds\n"
        )
        slog.close()


def check_weights(start_idx, end_idx, weighted_ports, startup_log_file, listener_site):
    weight_sum = 0
    for i in range(start_idx, end_idx + 1):
        weight_sum += weighted_ports[i][1]

    # Reset weight back to original value once it reaches 0
    if weight_sum == 0:
        with open(startup_log_file, "a") as slog:
            slog.write(
                f"{listener_site}# {weighted_ports} port weights have become zero. Going to reset\n"
            )
            slog.close()
        for i in range(start_idx, end_idx + 1):
            weighted_ports[i][1] = weighted_ports[i][2]


def strobe_bringup(
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
):
    #  Randomize and Re-add port mirror service for a group of ports a.k.a strobing
    pmnet = {}
    num_pmservices = {}
    for listener_site in listener_sites:
        pmnet[listener_site] = []
        j = 0

        for listener_node in listener_nodes[listener_site]:
            k = 0
            port_idx = 0
            node_name = listener_node_name[listener_site][j]
            avail_port_node_maxcnt = len(mod_port_list[listener_site][node_name])
            for listener_interface in listener_interfaces[node_name]:
                if port_idx % 2 == bring_down_port_group:
                    if port_idx % 2 == 0:
                        # first interface randomizes within the first half
                        random_index = random.randint(0, int(avail_port_node_maxcnt / 2 - 1))
                        while mod_port_list[listener_site][node_name][random_index][1] == 0:
                            check_weights(
                                0,
                                int(avail_port_node_maxcnt / 2 - 1),
                                mod_port_list[listener_site][node_name],
                                startup_log_file,
                                listener_site,
                            )
                            # first interface randomizes within the first half
                            random_index = random.randint(0, int(avail_port_node_maxcnt / 2 - 1))
                    else:
                        # second interface randomizes within the second half
                        random_index = random.randint(
                            int(avail_port_node_maxcnt / 2), avail_port_node_maxcnt - 1
                        )
                        while mod_port_list[listener_site][node_name][random_index][1] == 0:
                            check_weights(
                                int(avail_port_node_maxcnt / 2),
                                avail_port_node_maxcnt - 1,
                                mod_port_list[listener_site][node_name],
                                startup_log_file,
                                listener_site,
                            )
                            # second interface randomizes within the second half
                            random_index = random.randint(
                                int(avail_port_node_maxcnt / 2), avail_port_node_maxcnt - 1
                            )

                    # Reset weight back to original value once it reaches 0
                    # if mod_port_list[listener_site][node_name][random_index][1] == 0:
                    #    mod_port_list[listener_site][node_name][random_index][1] = mod_port_list[listener_site][node_name][random_index][2]

                    log.log(log.DEBUG, listener_pmservice_name[listener_node])
                    listener_pmservice_name[listener_node].pop(
                        port_idx
                    )  # Remove metadata of port to be brought down
                    """
                    with open(startup_log_file, "a") as slog:
                        slog.write(f"After pop active pmservice names in node\n {listener_node}\n are: {listener_pmservice_name[listener_node]}\n\n")
                        slog.close()
                    """
                    listener_pmservice_name[listener_node].insert(
                        port_idx,
                        f"{listener_site}_{node_name}_pmservice{ports_mirrored[listener_site]}",
                    )
                    pmnet[listener_site].append(
                        pmslice.add_port_mirror_service(
                            name=listener_pmservice_name[listener_node][port_idx],
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
                            f"{listener_site}# {mod_port_list[listener_site][node_name][random_index][0]}'s current weight is {mod_port_list[listener_site][node_name][random_index][1]}\n"
                        )
                        slog.write(
                            f"{listener_site}# {mod_port_list[listener_site][node_name][random_index][0]}'s original weight: {mod_port_list[listener_site][node_name][random_index][2]}\n"
                        )
                        slog.write(
                            f"{listener_site}# mirror interface name: {mod_port_list[listener_site][node_name][random_index][0]} mirrored to \n{listener_interface}\n\n"
                        )
                        slog.close()
                    log.log( log.INFO,
                        f"{listener_site}# mirror interface name: {mod_port_list[listener_site][node_name][random_index][0]} mirrored to \n {listener_interface}"
                    )

                k = k + 1
                port_idx += 1
                # Accumulative counter to create a unique listener_pmservice_name
                ports_mirrored[listener_site] = ports_mirrored[listener_site] + 1
            j = j + 1
            num_pmservices[listener_node] = k
        # In the next iteration, select the other half of mirrored ports
        bring_down_port_group ^= 1

    bringup_submit_start = time.time()
    with open(startup_log_file, "a") as slog:
        slog.write(f"bringup_submit_start: {bringup_submit_start} seconds\n")
        slog.write(
            f"Current time in asctime fmt: {time.asctime(time.gmtime(bringup_submit_start))}\n"
        )
        slog.close()
    # Request the above modification
    sliceid = pmslice.submit(progress=True, wait_timeout=2400, wait_interval=120)
    with open(startup_log_file, "a") as slog:
        slog.write(f"sliceid bringup: {sliceid}\n")
        slog.close()
    log.log(log.INFO, f"sliceid bringup: {sliceid}")
    if pmslice.get_state() == "StableError":
        raise Exception("Slice state is StableError")
    bringup_submit_stop = time.time()  # Update current time

    with open(startup_log_file, "a") as slog:
        slog.write(f"bringup_submit_stop: {bringup_submit_stop - bringup_submit_start} seconds\n")
        slog.close()

    return bring_down_port_group
