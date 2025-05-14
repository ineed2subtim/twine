# README for FPGA Listening Slice Setup Script

This script automates the setup and execution of an FPGA listening slice on the FABRIC testbed. It is designed to handle long execution times by implementing checkpoints, allowing the script to resume from the last successful point in case of failures.

The code in this section utilizes the Esnet FPGA workflow. The following sites support this workflow as of Nov 2024: <br>
```
STAR
TACC
MICH
UTAH
NCSA
WASH
DALL
SALT
UCSD
CLEM
LOSA
KANS
PRIN
SRI
```

## Prerequisites
- Python 3.10
- fabrictestbed-extensions 1.7.2
- FABRIC Testbed account with necessary permissions
- FABRIC `fabric_rc` configuration file
- Required artifacts and scripts:
  - `artifacts.au280.twine_alveo.0.zip`: This file is not provided. User has to copy artifacts file to this directory. <br>
To create the artifact, use the source twine_alveo.p4 present in p4/ directory. For more information on creating the artifact, please refer to [esnet-smartnic-fw](https://github.com/esnet/esnet-smartnic-hw)
  - `Dockerfile`
  - `dpdk_app_script`
  - `dpdk_stop_app`
  - `sn-cli-setup`
  - `cli_command.txt`

## Usage
```bash
python fpga_mirror_uplink.py [site] [--dry-run] [--extend] [--time TIME]
```

## Arguments
- `site` (required): The name of the site where the FPGA listening slice will be set up. The site name is case-insensitive and will be converted to uppercase in the script.

- `--dry-run` (optional): If provided, the script will query FABRIC resource and check whether a site has adequate resources to run the profiling operation.

- `--extend` (optional): If provided, the script will attempt to extend the lease time of the slice to 2 days. The default value is 1 day. This cannot be used together with `--dry-run. <br>
			 The extension allows the user to keep the slice active for a longer period. Combined with the checkpoint system mentioned below, it can save setup time for the user. 
This is because as long as the extension remains valid, the user doesn't need to resubmit the slice. However, the user also has to keep in mind not to lock resources such as the FPGA for too long as a matter of etiquette.  

- `--time TIME` (optional): Specifies the duration (in seconds) for which the sampling(data capture) should occur. The default is 60 seconds.

### Example
```bash
python fpga_mirror_uplink.py DALL --extend --time 300
```
Above command will create a slice on site `DALL` with a node with FPGA and capture mirrored packets for 5 minutes (300 seconds). Created slice will be extended.

## Check if program has terminated

Run the following command to see if the program has terminated:  <br>
```
fpga_site_strobe$ tree -L 2 .
```

The output will be of a structure like below: <br>
```
...
...
├── KANS
│   ├── fpga_mirror_uplink_cleanup.log
│   ├── fpga_mirror_uplink.log
│   └── latest_run				# No output directory
├── last_used_sites
├── LOSA
│   ├── fpga_mirror_uplink_cleanup.log
│   ├── fpga_mirror_uplink.log
│   └── latest_run				# NO output directory
├── MICH
│   ├── fpga_mirror_uplink_cleanup.log
│   ├── fpga_mirror_uplink.log
│   ├── latest_run
│   └── output					# Output directory created
├── NCSA
│   ├── fpga_mirror_uplink_cleanup.log
│   ├── fpga_mirror_uplink.log
│   ├── latest_run
│   └── output					# Output directory created
...
...
```

For the sites where no output directory is visible, run the below command to see the status of the program: <br>
```
fgpa_site_strobe$ tail -20 KANS/fpga_mirror_uplink.log

```

The output will display the status, some example outputs are:
```
Example 1:
2024-12-13 07:13:23,889 | INFO | Slice Exception: Slice Name: FPGA Listening Slice WASH, Slice ID: 0a4e16df-f11e-4e5f-8bc3-926fe52fae36: Slice Exception: Slice Name: FPGA Listening Slice WASH, Slice ID: 0a4e16df-f11e-4e5f-8bc3-926fe52fae36: Node: WASH_node0, Site: WASH, State: Closed, Insufficient resources : [core]#
Slice Exception: Slice Name: FPGA Listening Slice WASH, Slice ID: 0a4e16df-f11e-4e5f-8bc3-926fe52fae36: Slice Exception: Slice Name: FPGA Listening Slice WASH, Slice ID: 0a4e16df-f11e-4e5f-8bc3-926fe52fae36: Node: WASH_node0, Site: WASH, State: Closed, Insufficient resources : [core]#

Example 2:

2024-12-13 07:11:20,906 | INFO | ERROR: LOSA does not have any FPGA U280 cards available

Example 3:

2024-12-13 07:13:23,364 | INFO | Slice Exception: Slice Name: FPGA Listening Slice SRI, Slice ID: 3caee015-f3e0-42da-98da-3099e87a9074: Slice Exception: Slice Name: FPGA Listening Slice SRI, Slice ID: 3caee015-f3e0-42da-98da-3099e87a9074: Node: SRI_node0, Site: SRI, State: Closed, Insufficient resources : [disk]#
Slice Exception: Slice Name: FPGA Listening Slice SRI, Slice ID: 3caee015-f3e0-42da-98da-3099e87a9074: Slice Exception: Slice Name: FPGA Listening Slice SRI, Slice ID: 3caee015-f3e0-42da-98da-3099e87a9074: Node: SRI_node0, Site: SRI, State: Closed, Insufficient resources : [disk]#

```

## Ending the program
To bring down the docker container and delete the slice, please run 'fpga_mirror_uplink_cleanup.py' using the following structure: <br>
```
python fpga_mirror_uplink_cleanup.py [site]

e.g
python fpga_mirror_uplink_cleanup.py DALL

```

## Script Workflow and Checkpoints
The script is divided into several checkpoints. Each checkpoint represents a significant step in the setup process. If the script fails or is interrupted, it can resume from the last successful checkpoint. <br>

A user can change the checkpoint.json file to the checkpoint values shown below, and rerun the experiment without undergoing slice submission steps. <br>

For example, <br>
After running the fpga_mirror_uplink.py file once, if the user wants to run the experiment again after 4 hours, they can change the value in checkpoint.json to 'docker_compose_up', and rerun the python script again. <br>
In this case, only the steps after docker_compose_up will be executed, thus avoiding the slice submission wait period, the docker installation and docker build wait periods. <br>

## Checkpointing
- The script uses a `checkpoint.json` file to keep track of the last successful checkpoint.
- Before starting, the script checks if a checkpoint file exists and loads the last checkpoint.
- After completing each checkpoint, the script updates the `checkpoint.json` file.
- If the script is rerun, it will resume from the last saved checkpoint, skipping completed steps.

### Checkpoint: Config
- **Description**: Sets up the initial configuration, including creating the slice, adding nodes, and configuring interfaces.
- **Checkpoint Saved**: `"config"`

### Checkpoint: Grub
- **Description**: Configures GRUB settings on the listener nodes to enable IOMMU and hugepages.
- **Checkpoint Saved**: `"grub"`

### Checkpoint: Reboot
- **Description**: Reboots the listener nodes to apply GRUB changes and verifies IOMMU is enabled.
- **Checkpoint Saved**: `"reboot"`

### Checkpoint: IOMMU
- **Description**: Enables unsafe no-IOMMU mode for the VFIO module.
- **Checkpoint Saved**: `"iommu"`

### Checkpoint: Install Docker Compose
- **Description**: Installs Docker Compose and related plugins on the listener nodes.
- **Checkpoint Saved**: `"install_docker_compose"`

### Checkpoint: Build Docker Images
- **Description**: Builds the necessary Docker images for the FPGA applications.
- **Checkpoint Saved**: `"build_docker_images"`

### Checkpoint: Upload Artifact
- **Description**: Uploads the FPGA application artifact to the listener nodes.
- **Checkpoint Saved**: `"upload_artifact"`

### Checkpoint: Build esnet-smartnic-fw
- **Description**: Builds the `esnet-smartnic-fw` firmware and sets up the environment.
- **Checkpoint Saved**: `"build_esnet-smartnic-fw"`

### Checkpoint: Docker Compose Up
- **Description**: Launches the Docker Compose services required for the FPGA applications.
- **Checkpoint Saved**: `"docker_compose_up"`

### Checkpoint: Begin Packet Capture
- **Description**: Starts the packet capture process.
- **Checkpoint Saved**: `"start_dpdk_app"`

### Checkpoint: Stop Packet Capture
- **Description**: Stops the data capture process and retrieves the captured data.
- **Checkpoint Saved**: `"stop_dpdk_app"`

## Performance evaluation:
The performance evaluation is present in the performance_evaluation directory. It contains: <br>
1. Performance of the standalone Twine Alveo performance running on an FPGA.
2. Performance of the DPDK pcap writer program. Tested on FABRIC


