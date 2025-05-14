# TWINE (Anonymized repo)

Repository containing the Python scripts and support files needed to conduct testbed profiling using port mirroring primitive on the FABRIC testbed.   

# Steps to setup Python environment

If your local system operating system is Linux, run the steps mentioned here: [Linux_setup](Linux_setup.md) <br>

If your local system operating system is MACos, run the steps mentioned here: [MACos_setup](MACos_setup.md) <br>

## Setup environment for FABRIC experiments

Download the following files from your FABRIC Jupyter environment to your local system in a directory /path/to/file: <br>
```
/fabric_config/slice_key.pub
/fabric_config/slice_key
/fabric_config/<user>_bastion
/fabric_config/<user>_bastion.pub

```
Change the permissions of the private keys <br>
```
$ chmod 600 /path/to/file/slice_key
$ chmod 600 /path/to/file/<user>_bastion
```

Generate a short lived token in FABRIC for your specific experiment, and download that to your local system in directory /path/to/file as 'id_token.json': <br>
See [Generate_tokens](https://learn.fabric-testbed.net/knowledge-base/obtaining-and-using-fabric-api-tokens/) for information on creating FABRIC tokens. <br>
```
$ cp <download_dir>/id_token.json /path/to/file/id_token.json
```

On your local system, clone this repo: <br>
```
$ git clone https://gitlab.com/d-r-r/fabric-profiling/uplink_swport_mirroring.git 
# Run the below script and pass the path where the slice_key and bastion key are stored. Also pass the BastionLogin as the 2nd parameter
$ ./fabric_pyenv_setup.sh </path/to/file/> <BastionLogin> <projectID> ( Example: ./fabric_pyenv_setup.sh /home/john/work/fabric_config john_123456 eba55063-26d9-734a-826a-4f9a655c4cce )
$ cd multi_site_strobe/
```
Check if the script ran successfully <br>
```
$ printenv | grep FABRIC		# Should produce an output
```
## Create virtual environment for FABRIC codebase

```
bash-3.2$ pip3 install virtualenv virtualenvwrapper
bash-3.2$ virtualenv fabric-jupyter
bash-3.2$ source fabric-jupyter/bin/activate
(fabric-jupyter) bash-3.2$
```

#### Mac Homebrew version for creating virtual environment:

```
bash-3.2$ pip3.10 install virtualenv virtualenvwrapper
bash-3.2$ virtualenv fabric-jupyter
bash-3.2$ source fabric-jupyter/bin/activate
(fabric-jupyter) bash-3.2$
```


## Install FABRIC codebase

```
(fabric-jupyter) bash-3.2$ pip3 install fabrictestbed-extensions
(fabric-jupyter) bash-3.2$ pip3 list | grep fab         # Check that FABRIC packages have been installed
(fabric-jupyter) bash-3.2$ source /path/to/file/fabric_rc         # Source fabric_rc file inside virtual environment
```
This document was created while testing with *fabrictestbed-extensions 1.8.1* <br>

## Known Issues
When attempting a pip install of the FABRIC packages, <br>
```
ERROR: Could not find a version that satisfies the requirement neo4j>=5.3.0 (from fabric-fim) (from versions: 1.7.0b1, 1.7.0b2, 1.7.0b3, 1.7.0b4, 1.7.0rc1, 1.7.0rc2, 1.7.0, 1.7.1, 1.7.2, 1.7.3, 1.7.4, 1.7.5, 1.7.6, 4.0.0a1, 4.0.0a2, 4.0.0a3, 4.0.0a4, 4.0.0b1, 4.0.0b2, 4.0.0rc1, 4.0.0, 4.0.1, 4.0.2, 4.0.3, 4.1.0rc1, 4.1.0rc2, 4.1.0, 4.1.1, 4.1.2, 4.1.3, 4.2.0a1, 4.2.0, 4.2.1, 4.3.0a1, 4.3.0b1, 4.3.0rc1, 4.3.0, 4.3.1, 4.3.2, 4.3.3, 4.3.4, 4.3.5, 4.3.6, 4.3.7, 4.3.8, 4.3.9, 4.4.0a1, 4.4.0b1, 4.4.0, 4.4.1, 4.4.2, 4.4.3, 4.4.4, 4.4.5, 4.4.6, 4.4.7, 4.4.8, 4.4.9, 4.4.10, 4.4.11, 5.0.0a1, 5.0.0a2, 5.0.0, 5.0.1, 5.1.0, 5.2.0, 5.2.1, 5.3.0, 5.4.0, 5.5.0, 5.6.0, 5.7.0, 5.8.0, 5.8.1, 5.9.0, 5.10.0, 5.11.0, 5.12.0, 5.13.0, 5.14.0, 5.14.1, 5.15.0, 5.16.0, 5.17.0, 5.18.0, 5.19.0)
ERROR: No matching distribution found for neo4j>=5.3.0

Solution: 
(fabric-jupyter) bash-3.2$ python3 -m pip install --upgrade pip setuptools wheel
```
After installing Python3.10, if this version does not show up in the alternatives, do this outside the virtual environment: <br>
```
sudo update-alternatives --config python3			--> 	update-alternatives: error: no alternatives for python3

Solution:
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 2			
sudo update-alternatives --config python3			# update-alternatives: --install needs <link> <name> <path> <priority>
```



## Getting started
```
-
|
| -multi_site_strobe/      # Contains python scripts and files for mirroring all switch ports
                             across multiple sites, running entirely on CPU

| -fpga_site_strobe/       # Contains python scripts and files for mirroring upstream switch ports 
                             across FABRIC sites, running on FPGA and with a DPDK pcap writer program
```
