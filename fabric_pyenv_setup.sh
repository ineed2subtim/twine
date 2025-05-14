#!/bin/bash

if [ "$#" -ne 3 ]; then
	echo "Usage: ./fabric_pyenv_setup.sh </path/to/file> <bastion_login> <projectID>"
	echo "E.g : ./fabric_pyenv_setup.sh /home/user/work/fabric_config john_123456 eba55063-26d9-734a-826a-4f9a655c4cce "
	exit 1
fi

filepath=$1
userid=$2
projectid=$3
rc_name="fabric_rc"
sshconfig_name="ssh_config"

username=$(echo $userid | cut -d '_' -f 1)
# Create fabric_rc file and specify fabric backend hosts, as well as location of bastion key as well as slice key 
rc_file="$filepath/$rc_name"
sshconfig="$filepath/$sshconfig_name"

if [ -f $rc_file ]; then
	rm $rc_file
fi

if [ -f $sshconfig ]; then
	rm $sshconfig
fi

touch $rc_file
touch $sshconfig

script_dir=$(realpath .) # Get the dir of this script. 
echo "Script directory: $script_dir"
work_dir=$(realpath "$script_dir")/multi_site_strobe # Find the parent of the current dir. Currently that is '/multi_site_strobe'
echo "Work Directory $work_dir"
echo ""

echo "Writing configuration to $rc_file"
echo "export FABRIC_BASTION_USERNAME=$userid" >> $rc_file
echo "export FABRIC_ORCHESTRATOR_HOST=orchestrator.fabric-testbed.net" >> $rc_file
echo "export FABRIC_CREDMGR_HOST=cm.fabric-testbed.net" >> $rc_file
echo "export FABRIC_CORE_API_HOST=uis.fabric-testbed.net" >> $rc_file
echo "export FABRIC_TOKEN_LOCATION=$filepath/id_token.json" >> $rc_file
echo "export FABRIC_BASTION_HOST=bastion.fabric-testbed.net" >> $rc_file
echo "export FABRIC_BASTION_KEY_LOCATION=$filepath/${username}_bastion" >> $rc_file
echo "export FABRIC_SLICE_PUBLIC_KEY_FILE=$filepath/slice_key.pub" >> $rc_file
echo "export FABRIC_SLICE_PRIVATE_KEY_FILE=$filepath/slice_key" >> $rc_file
echo "export FABRIC_LOG_LEVEL=INFO" >> $rc_file
echo "export FABRIC_BASTION_SSH_CONFIG_FILE=$filepath/ssh_config" >> $rc_file
echo "export FABRIC_SSH_COMMAND_LINE=\"ssh -i {{ _self_.private_ssh_key_file }} -F $filepath/ssh_config {{ _self_.username }}@{{ _self_.management_ip }}\"" >> $rc_file
echo "export WORKDIR=$work_dir" >> $rc_file
echo "export PYTHONPATH=$work_dir:$work_dir/infrastructure_requests:$PYTHONPATH" >> $rc_file
echo "export PROJECT_ID=$projectid" >> $rc_file
echo "export FABRIC_RC=$rc_file" >> $rc_file

# Create the ssh config setting, that will be used to connect to the bastion host as a gateway to the fabric environment 

echo "Writing configuration to $sshconfig"
cat >> $sshconfig << _EOF
UserKnownHostsFile /dev/null
StrictHostKeyChecking no
ServerAliveInterval 120

Host bastion.fabric-testbed.net
	User $userid
	ForwardAgent yes
	Hostname %h
	IdentityFile $filepath/${username}_bastion
	IdentitiesOnly yes

Host * !bastion.fabric-testbed.net
	ProxyJump $userid@bastion.fabric-testbed.net:22
_EOF

#Once the above changes have been made, the fabric_rc file is sourced by running the below command. 
echo "Sourcing $rc_file"
source $rc_file
