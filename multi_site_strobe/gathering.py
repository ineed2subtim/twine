import os
import re
import pw_logging as log


def replace_ssh_config(ssh_params, new_config_path):
    pattern = r"(-F\s+)(\S+)"
    new_ssh_params = re.sub(pattern, f"\\1{new_config_path}", ssh_params)
    return new_ssh_params


def pw_gather(
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
):
    listener_scp = {}
    file_name = "packet_trace.tgz"
    try:
        slice = fablib.get_slice(listener_slice_name)
        for listener_site in listener_sites:
            i = 0
            for listener_node in listener_nodes[listener_site]:
                node_name = listener_node_name[listener_site][i]

                # creating appropriate scp command for host listener
                listener_param = listener_ssh[node_name].split("ssh ")[1]
                if os.getenv("FABRIC_BASTION_SSH_CONFIG_FILE"):
                    listener_param = replace_ssh_config(
                        listener_param, os.getenv("FABRIC_BASTION_SSH_CONFIG_FILE")
                    )

                listener_scp[node_name] = "scp " + listener_param
                scp_addr = listener_scp[node_name].split("@")[1]
                scp_config = listener_scp[node_name].split("@")[0]
                scp_addr_brkted = "[" + scp_addr + "]"
                listener_scp[node_name] = scp_config + "@" + scp_addr_brkted
                listener_scp[node_name] = (
                    listener_scp[node_name]
                    + ":~/"
                    + file_name
                    + " "
                    + full_path_top_dir
                    + "/"
                    + f"{listener_site}_node{i}"
                    + "_"
                    + file_name
                )
                i = i + 1
        print(listener_scp)

        with open(out_file, "w") as out:
            out.write("#!/bin/bash" + "\n")
            out.write(f"mkdir {full_path_top_dir}\n")
            for listener_site in listener_sites:
                i = 0
                for listener_node in listener_nodes[listener_site]:
                    node_name = listener_node_name[listener_site][i]
                    out.write(listener_scp[node_name] + "\n")
                    i = i + 1
            workdir = os.environ.get("WORKDIR")
            out.write(f"cp {startup_log_file} {full_path_top_dir}/ \n")
            out.write(f"echo {top_dir} > {workdir}/top_dir_name_{cmdline_args.site}.txt\n")
            out.close()

    except Exception as e:
        with open(startup_log_file, "a") as slog:
            slog.write(f" {e}\n")
            slog.close()
        log.log(log.INFO, f"Exception: {e}")
