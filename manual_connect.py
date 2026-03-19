import config
import wg_peer

#==CODE==#
import sys
import requests
import time

import urllib3
urllib3.disable_warnings() # Suppress Insecure HTTPS warnings

print("==API==")
print(f"key: {config.api_key}")
print(f"secret: {config.api_secret}")
print(f"Going to {config.opnsense_api}")

# API
session = requests.Session()
session.auth = (config.api_key, config.api_secret)

# API check
try:
    response = session.get(f"{config.opnsense_api}/wireguard/client/list_servers", verify=False)
    response_json = response.json()
    if response_json["status"] != "ok":
        raise Exception(f"JSON response is not OK! ({response_json})")
except Exception as e:
    print(f"Something went wrong during API call. Make sure the API key is correct and it can access wireguard. ({e})")
    exit(-1)

ifname = "" # ifname will be automatically found via searchClient

# == USER CONFIG ==
print("== == ==")

disable_first = config.get_do_disable_first()
randomize = config.get_do_randomize()

print("== == ==")
if not config.wait_for_user_input("Start"):
    exit()


print("==START==")

print("Disable all peers?")
if disable_first:
    # Disable all peers
    request_json = {
        "current": 1,
        "rowCount": -1,
        "servers": [config.instance_UUID],
        "sort": {},
        "searchPhrase": ""
    }

    output = session.post(f"{config.opnsense_api}/wireguard/client/searchClient/", json=request_json, verify=False)
    output_json = output.json()

    count = 0
    for peer in output_json["rows"]:
        uuid: str = peer['uuid']
        name: str = peer['name']
        enabled = peer['enabled'] == '1'

        if enabled:
            print(f"Disabling {name} ({int((count+1)/len(output_json['rows']) * 100)}%)...")
            # Enable it!
            output = session.post(f"{opnsense_api}/wireguard/client/toggleClient/{uuid}", verify=False)
            print(output.content)
            count += 1
            print()

    print(f"Disable All({count}) peers?")
    print("(Y) Apply Changes | (Other) Abort")
    if input() != "Y":
        sys.exit(-1)

    print("Applying...")
    output = session.post(f"{opnsense_api}/wireguard/service/reconfigure", verify=False)
    print(output.content)

    print("Waiting 3 seconds before checking status...")
    time.sleep(3)

if input("Activate all peers? (Y) Yes | (Other) Skip") == "Y":

    randomize_port = False
    if input("Randomize port for each peer? (Y/N): ") == "Y":
        randomize_port = True

    # Enable All + Randomize Port

    request_json = {
        "current" : 1,
        "rowCount" : -1,
        "servers": [instance_UUID],
        "sort" : {},
        "searchPhrase" : ""
    }

    output = session.post(f"{opnsense_api}/wireguard/client/searchClient/", json = request_json, verify=False)
    output_json = output.json()

    count = 0

    rows = output_json["rows"]
    for peer in rows:
        uuid: str = peer['uuid']

        name: str = peer['name']
        enabled = peer['enabled'] == '1'

        ifname = peer["%servers"]

        if not enabled:
            print(f"Now enabling {name} ({int((count+1)/len(rows) * 100)}%)...")

            if randomize_port:
                # Modify port
                port_range = random.choice(randomize_port_range)
                new_port = random.randint(port_range[0], port_range[1])
                print(f"Port: {peer['serverport']} -> {new_port}")
                request_json = { "client":
                    {
                        "enabled": 0,
                        "name": name,
                        "pubkey": peer["pubkey"],
                        "psk": "",
                        "tunneladdress": peer["tunneladdress"],
                        "serveraddress": peer["serveraddress"],
                        "serverport": new_port,
                        "servers": instance_UUID,
                        "keepalive": str(keepalive_interval),
                    }
                }
                output = session.post(f"{opnsense_api}/wireguard/client/setClient/{uuid}", json=request_json, verify=False)
                output_json = output.json()

            # Enable it!
            output = session.post(f"{opnsense_api}/wireguard/client/toggleClient/{uuid}", verify=False)
            print(output.content)
            count += 1

        print()

    print(f"Enable All({count}) peers?")
    print("(Y) Apply Changes | (Other) Abort")
    if input() != "Y":
        sys.exit(-1)

    print("Applying...")
    output = session.post(f"{opnsense_api}/wireguard/service/reconfigure", verify=False)
    print(output.content)

    print("Waiting 5 seconds before checking status...")
    time.sleep(5)

else:
    request_json = {
        "current": 1,
        "rowCount": -1,
        "servers": [instance_UUID],
        "sort": {},
        "searchPhrase": ""
    }

    output = session.post(f"{opnsense_api}/wireguard/client/searchClient/", json=request_json, verify=False)
    output_json = output.json()

    count = 0

    rows = output_json["rows"]
    ifname = rows[0]["%servers"]

# Find all available servers

request_json = {
    "current" : 1,
    "rowCount" : -1,
    "sort" : {}
}

output = session.post(f"{opnsense_api}/wireguard/service/show", json = request_json, verify=False)

output_json = output.json()

print("===================")
print("==Available Servers==")

i = 1

available_peers = []

# print(ifname)

for item in output_json["rows"]:
    if item["type"] == "peer":
        if item["ifname"] == ifname:
            if item["peer-status"] == "online":
                # Display info
                name: str = item['name']
                country = name.split("-")[0]
                city = name.split("-")[1]
                server = name.split("-")[2]

                available_peers.append(name)

                rx = item["transfer-rx"]
                tx = item["transfer-tx"]
                try:
                    print(f"{i}: {name} ({support_functions.name_translation.country_codes[country.upper()]}, {support_functions.name_translation.city_codes[city.upper()]}) [{tx}/{rx}]")
                except KeyError as e:
                    print(f"{i}: {name} ({country.upper()}, {city.upper()}) [{tx}/{rx}]")
                i += 1

print()
selected = available_peers[int(input("Select Server (NUMBER): "))-1]
print(f"Connect to \"{selected}\" (Y) | Abort (Other)")
if input() != "Y":
    sys.exit(-1)

# Disable everything but that

request_json = {
    "current" : 1,
    "rowCount" : -1,
    "servers": [instance_UUID],
    "sort" : {},
    "searchPhrase" : ""
}

output = session.post(f"{opnsense_api}/wireguard/client/searchClient/", json = request_json, verify=False)

output_json = output.json()

for peer in output_json["rows"]:
    name: str = peer['name']
    uuid: str = peer['uuid']
    enabled = peer['enabled'] == '1'


    if enabled and name != selected:
        print(f"Disabling {name}...")
        # Disable other
        output = session.post(f"{opnsense_api}/wireguard/client/toggleClient/{uuid}", verify=False)
        print(output.content)
        print()

print(f"Disable all peers but {selected}?")
print("(Y) Apply Changes | (Other) Abort")
if input() != "Y":
    sys.exit(-1)

print("Applying...")
output = session.post(f"{opnsense_api}/wireguard/service/reconfigure", verify=False)
print(output.content)

print("Restarting WireGuard...")
output = session.post(f"{opnsense_api}/core/service/restart/wireguard/{instance_UUID}", verify=False)
print(output.content)

# Optional: Restart Mullvad gateway watcher to reset gateway alerts. You need to modify the API call (MULLVAD part) yourself.
if True:
    print("Resetting Gateway watcher...")
    output = session.post(f"{opnsense_api}/core/service/restart/dpinger/MULLVAD", verify=False)
    print(output.content)

print("DONE.")