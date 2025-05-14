import os
import re
import pw_logging as log

script_listener = "capture_packets.sh"
end_detector = "end_detect.sh"


def replace_ssh_config(ssh_params, new_config_path):
    pattern = r"(-F\s+)(\S+)"
    new_ssh_params = re.sub(pattern, f"\\1{new_config_path}", ssh_params)
    return new_ssh_params


def copy_helpers(
    fablib,
    startup_log_file,
    listener_node_name,
    listener_slice_name,
    out_file,
    listener_sites,
    listener_nodes,
):
    global script_listener
    global end_detector
    workdir = os.environ.get("WORKDIR")
    listener_scp = {}
    listener_ssh = {}
    slice = fablib.get_slice(listener_slice_name)
    for listener_site in listener_sites:
        i = 0
        # log.log(log.DEBUG, listener_nodes[listener_site])
        for listener_node in listener_nodes[listener_site]:
            node_name = listener_node_name[listener_site][i]
            listener_ssh[node_name] = slice.get_node(name=node_name).get_ssh_command()
            with open(startup_log_file, "a") as slog:
                slog.write(f"{node_name}: {listener_ssh[node_name]}\n")
                slog.close()
            # creating appropriate scp command for host listener

            listener_param = listener_ssh[node_name].split("ssh ")[1]
            if os.getenv("FABRIC_BASTION_SSH_CONFIG_FILE"):
                listener_param = replace_ssh_config(
                    listener_param, os.getenv("FABRIC_BASTION_SSH_CONFIG_FILE")
                )

            listener_scp[node_name] = ""
            listener_scp[node_name] = "scp " + listener_param
            scp_addr = listener_scp[node_name].split("@")[1]
            scp_config = listener_scp[node_name].split("@")[0]
            scp_addr_brkted = "[" + scp_addr + "]"
            listener_scp[node_name] = scp_config + "@" + scp_addr_brkted
            listener_scp[node_name] = (
                listener_scp[node_name].split("ubuntu")[0]
                + " "
                + f"{workdir}/{script_listener}"
                + " "
                + f"{workdir}/{end_detector}"
                + " ubuntu"
                + listener_scp[node_name].split("ubuntu")[1]
                + ":~"
            )
            i = i + 1

    log.log(log.INFO, listener_scp)

    with open(out_file, "w") as out:
        out.write("#!/bin/bash" + "\n")
        for listener_site in listener_sites:
            i = 0
            for listener_node in listener_nodes[listener_site]:
                out.write(listener_scp[listener_node_name[listener_site][i]] + "\n")
                i = i + 1
        out.close()


    return listener_ssh


def pw_sampling(
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
):
    slice = fablib.get_slice(listener_slice_name)
    global script_listener
    global end_detector
    log_dir = "packet_trace/"
    log_file = "packet_trace.log"
    log_end_script = "end_detect_log.log"
    refcnt_file = "refcnt.txt"
    delay_factor = 1
    tcpdump_filter = cmdline_args.tcpdump_filter
    experiment_retries = cmdline_args.experiment_retries
    max_iter_per_experiment = cmdline_args.iter_per_experiment
    wait_interval = cmdline_args.wait_interval
    listen_time = cmdline_args.listen_time
    snaplen = cmdline_args.snaplen
    for listener_site in listener_sites:
        i = 0
        for node in listener_nodes[listener_site]:
            print(listener_node_name[listener_site][i])
            listener_node = slice.get_node(name=listener_node_name[listener_site][i])
            stdout, stderr = listener_node.execute("chmod u+x " + script_listener + " " + end_detector)
            listener_node.execute(f" rm {log_file} {log_end_script} {refcnt_file}")

            # Run capture packet script for each node in parallel
            j = 0
            while j < num_pmservices[node]:
                listener_node_intf_name = listener_node.get_interface(
                    network_name=listener_pmservice_name[node][j]
                ).get_device_name()
                listen_command = f'./{script_listener} {listener_node_intf_name} {experiment_retries} {max_iter_per_experiment} {wait_interval} {listen_time} {snaplen} "{tcpdump_filter}"'
                log.log(log.INFO, f"{listener_site}:{listen_command}")
                with open(startup_log_file, "a") as slog:
                    slog.write(f"{listener_site}:{listen_command}\n")
                    slog.close()
                listener_node.execute(f"sudo ip link set {listener_node_intf_name} up")
                if enable_gro == 0:
                    listener_node.execute(f"sudo ethtool -K {listener_node_intf_name} gro off")
                    with open(startup_log_file, "a") as slog:
                        slog.write(f"Disabled GRO on {listener_node}\n")
                        slog.close()
                listener_node.execute(f"sudo ethtool -K {listener_node_intf_name} rx off")
                listener_node.execute(f"sudo ethtool -K {listener_node_intf_name} rxvlan off")
                listener_node.execute(f"sudo ethtool -G {listener_node_intf_name} rx 4096")
                # start tcpdump
                listener_node_thread = listener_node.execute_thread(listen_command)
                log.log(log.DEBUG, f"listener_node_thread: {listener_node_thread}")
                j = j + 1
            i = i + 1

    # Use delay_factor * total_experiment time as a timeout value for end_detect script
    total_experiment_time = (experiment_retries * max_iter_per_experiment * listen_time) + (
        wait_interval * (experiment_retries)
    )
    # delay_factor needed to account for runtime latency for the experiment
    if total_experiment_time < 500:
        delay_factor = 1.50
    elif total_experiment_time < 1000:
        delay_factor = 1.30
    elif total_experiment_time < 5000:
        delay_factor = 1.15
    elif total_experiment_time < 20000:
        delay_factor = 1.10
    else:
        delay_factor = 1.05
    total_experiment_time = int(delay_factor * total_experiment_time)
    for listener_site in listener_sites:
        i = 0
        for listener_node in listener_nodes[listener_site]:
            listener_node = slice.get_node(name=listener_node_name[listener_site][i])
            end_command = f"./{end_detector} {total_experiment_time}"
            with open(startup_log_file, "a") as slog:
                slog.write(f"end_command: {end_command}\n")
                slog.close()
            listener_node_thread = listener_node.execute_thread(end_command)
            i = i + 1

    return total_experiment_time
