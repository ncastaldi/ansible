#!/usr/bin/env python3

import requests
import json
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)

# Proxmox API credentials and URL
api_url = "https://10.0.0.250:8006/api2/json"
username = "root@pam"
password = "Procmi*1"

def get_auth_token():
    response = requests.post(f"{api_url}/access/ticket", data={
        "username": username,
        "password": password
    }, verify=False)
    response.raise_for_status()
    data = response.json()["data"]
    return data["ticket"], data["CSRFPreventionToken"]

def get_container_list(ticket, csrf_token):
    headers = {
        "Authorization": f"PVEAuthCookie={ticket}",
        "CSRFPreventionToken": csrf_token
    }
    response = requests.get(f"{api_url}/nodes/pve01/lxc", headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["data"]

def get_container_ip(container_id, ticket, csrf_token):
    headers = {
        "Authorization": f"PVEAuthCookie={ticket}",
        "CSRFPreventionToken": csrf_token
    }
    response = requests.get(f"{api_url}/nodes/pve01/lxc/{container_id}/config", headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()["data"]
    net0 = data["net0"]
    ip_address = None
    if "ip=" in net0:
        ip_address = net0.split("ip=")[1].split("/")[0]
    return ip_address

def main():
    ticket, csrf_token = get_auth_token()
    containers = get_container_list(ticket, csrf_token)

    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "vars": {
                "ansible_user": "root"
            }
        }
    }

    # # Add Proxmox host itself
    # inventory["all"]["hosts"].append("proxmox")
    # inventory["_meta"]["hostvars"]["proxmox"] = {
    #     "ansible_host": "10.0.0.250",  # Update with your Proxmox host IP
    #     "ansible_user": "root"
    # }

    # for container in containers:
    #     container_id = container["vmid"]
    #     container_name = container["name"]
    #     ip = get_container_ip(container_id, ticket, csrf_token)
    #     if ip:
    #         inventory["all"]["hosts"].append(container_name)
    #         inventory["_meta"]["hostvars"][container_name] = {
    #             "ansible_host": ip
    #         }

    for container in containers:
        container_id = container["vmid"]
        container_name = container["name"]
        ip = get_container_ip(container_id, ticket, csrf_token)
        if ip and ip.startswith("10.0.0.") and 200 <= int(ip.split(".")[-1]) <= 249:
            inventory["all"]["hosts"].append(container_name)
            inventory["_meta"]["hostvars"][container_name] = {
                "ansible_host": ip
            }

    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
