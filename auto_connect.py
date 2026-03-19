import config
import wg_peer

# ==CODE==#
import typing
import sys
import requests
import time

import urllib3

from wg_peer import WgPeer

urllib3.disable_warnings()  # Suppress Insecure HTTPS warnings

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
    print(
        f"[!] Something went wrong during API call. Make sure the API key is correct and it can access wireguard. ({e})")
    exit(-1)

ifname = ""  # ifname will be automatically found via searchClient

# == USER CONFIG ==
print("== == ==")

disable_first = config.get_do_disable_first()
randomize = config.get_do_randomize()

print("== == ==")
if not config.wait_for_user_input("Start"):
    exit()

print("=== START ===")
peers: typing.Dict[str, wg_peer.WgPeer] = {}

# === Find all peers ===

print("Finding all peers...")

request_json = {
    "current": 1,
    "rowCount": -1,
    "servers": [config.instance_UUID],
    "sort": {},
    "searchPhrase": ""
}

output = session.post(f"{config.opnsense_api}/wireguard/client/searchClient/", json=request_json, verify=False)
output_json = output.json()

for peer_js in output_json["rows"]:
    if peer_js["servers"] != config.instance_UUID:
        raise Exception("[!] OHNON!O!NO!NO!")
    peer = WgPeer(peer_js)
    peers[peer.pubkey] = peer

# === DISABLE ===

if disable_first:
    print("=== DISABLING PEERS... ===")

    enabled_peers = [peer for peer in peers.values() if peer.enabled]
    for idx, peer in enumerate(enabled_peers):
        print(f"Disabling {peer.name} ({int((idx + 1) / len(enabled_peers) * 100)}%)...")
        peer.disable(session)

    print("---")
    print("Applying...")
    output = session.post(f"{config.opnsense_api}/wireguard/service/reconfigure", verify=False)
    print(output.content)

    print("Waiting 1 second before checking status...")
    time.sleep(1)

# === ENABLE ===

print("=== ENABLING PEERS... ===")

disabled_peers = [peer for peer in peers.values() if not peer.enabled]

for idx, peer in enumerate(disabled_peers):
    print(f"Enabling {peer.name} ({int((idx + 1) / len(disabled_peers) * 100)}%)...")
    peer.enable(session, randomize)

print("---")
print("Applying...")
output = session.post(f"{config.opnsense_api}/wireguard/service/reconfigure", verify=False)
print(output.content)

print("Waiting 1 second before checking status...")
time.sleep(1)

# === INFO ===

print("=== STATUS ===")

request_json = {
    "current": 1,
    "rowCount": -1,
    "sort": {}
}
output = session.post(f"{config.opnsense_api}/wireguard/service/show", json=request_json, verify=False)
status_json = output.json()

idx = 1
candidates: typing.List[WgPeer] = []

for item in status_json["rows"]:
    if item["type"] == "peer":

        if item["public-key"] not in peers:  # probably other interfaces
            continue

        p = peers[item["public-key"]]
        p.add_connection_info(item)
        if p.online:
            print(f"{idx}: {p.get_human_info()}")
            idx += 1
            candidates.append(p)

# -- SELECTION --

selection_idx = config.get_peer_selection(len(candidates))
selected_peer = candidates[selection_idx]

print(f"Selected [{selection_idx + 1}]{selected_peer.name}")

# === CONNECT ===
# Disconnect all but selection

print(f"=== Disconnecting all but {selected_peer.name}... ===")

for peer in peers.values():
    peer.disable(session)

selected_peer.enable(session, False)

print("---")
print("Applying...")
output = session.post(f"{config.opnsense_api}/wireguard/service/reconfigure", verify=False)
print(output.content)

print("Waiting 1 second before checking status...")
time.sleep(1)

# === SPEEDTEST ===

print("=== Speedtest autoconnect? (Optional) ===")
if config.get_do_speedtest():
    # == DO SPEEDTEST ==
    pass # TODO


# === FINAL APPLY ===
print ("=== Final apply... ===")

print("Restarting WireGuard...")
output = session.post(f"{config.opnsense_api}/core/service/restart/wireguard/{config.instance_UUID}", verify=False)
print(output.content)

if config.get_gateway_name() != "":
    print("Resetting Gateway watcher...")
    output = session.post(f"{config.opnsense_api}/core/service/restart/dpinger/{config.get_gateway_name()}", verify=False)
    print(output.content)

print("============")
print("DONE!")