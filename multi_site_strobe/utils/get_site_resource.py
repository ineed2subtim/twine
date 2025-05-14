import sys
from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

exclude_list = (
    "EDC",
    "AWS",
    "AL2S",
    "AZURE",
    "GCP",
    "AZURE-GOV",
    "AZUREGOV",
    "OCI",
    "OCIGOV",
    "NONCLOUD",
)


def get_site_resource(fablib):
    site_resources = []
    for site_name, site in fablib.get_resources().sites.items():
        if site_name in exclude_list:
            continue
        site_dict = site.to_dict()
        site_resources.append(site_dict)
    return site_resources


fablib = fablib_manager(
    fabric_rc="~/.ssh/bastion/fabric_rc",
    project_id="abe55161-26d9-434a-826a-4f9a655d0dde",
    log_file="./fablib.log",
)
site_resources = get_site_resource(fablib)
# Create list of switch ports per site
with open("site_resources.csv", "a") as sres:
    print(
        f"Name, cores_capacity, ram_capacity, disk_capacity, nic_connectx_6_capacity, nic_connectx_6_capacity"
    )
    sres.write(
        f"Name, cores_capacity, ram_capacity, disk_capacity, nic_connectx_5_capacity, nic_connectx_6_capacity\n"
    )
    for site_resource in site_resources:
        print(
            f'{site_resource["name"]}, {site_resource["cores_capacity"]}, {site_resource["ram_capacity"]}, {site_resource["disk_capacity"]}, {site_resource["nic_connectx_5_capacity"]}, {site_resource["nic_connectx_6_capacity"]}'
        )
        sres.write(
            f'{site_resource["name"]}, {site_resource["cores_capacity"]}, {site_resource["ram_capacity"]}, {site_resource["disk_capacity"]}, {site_resource["nic_connectx_5_capacity"]}, {site_resource["nic_connectx_6_capacity"]}\n'
        )

sys.exit(0)
