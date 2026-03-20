# Packaged, to be called via opnspeedguard.py cli interface
def auto_connect() -> None:
    import random
    from logging import INFO
    from typing import List
    import config
    import wg_peer
    from wg_peer import WgPeer, connect_only_to

    # ==CODE==#
    import typing
    import requests

    import urllib3

    urllib3.disable_warnings()  # Suppress Insecure HTTPS warnings

    print("==API==")
    # print(f"key: {config.api_key}") # hidden for privacy
    # print(f"secret: {config.api_secret}") # hidden for privacy
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
            f"[ERR] Something went wrong testing the API. Check your network connection, then make sure the API key is correct and it has permissions to management wireguard. ({e})")
        exit(-1)

    ifname = ""  # ifname will be automatically found via searchClient

    print("=== === OPNSpeedGuard === ===")
    if config.automatic:
        print("[INFO] RUNNING IN AUTOMATIC MODE. ALL USER INPUT WILL BE EMULATED.")
    # == USER CONFIG ==
    print("== == ==")

    disable_first = config.get_do_disable_first()
    randomize = config.get_do_randomize()

    print("== == ==")
    if not config.wait_for_user_start():
        exit()

    print("=== START ===")
    peers: typing.Dict[str, WgPeer] = {}


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

    # TODO: This is not actually required anymore I think...
    if disable_first:
        print("=== DISABLING PEERS... ===")

        enabled_peers = [peer for peer in peers.values() if peer.enabled]
        for idx, peer in enumerate(enabled_peers):
            if config.verbose:
                print(f"Disabling {peer.name} ({int((idx + 1) / len(enabled_peers) * 100)}%)...")
            peer.disable(session)

        print("---")
        print("Applying...")
        wg_peer.wg_apply(session)


    # === ENABLE ===

    print("=== ENABLING PEERS... ===")

    for idx, peer in enumerate(peers.values()):
        if config.verbose:
            print(f"Enabling {peer.name} ({int((idx + 1) / len(peers) * 100)}%)...")
        peer.enable(session, randomize)


    print("---")
    print("Applying...")
    wg_peer.wg_apply(session)


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

    print(f"Selected [{selection_idx + 1}] {selected_peer.name}")

    # === CONNECT ===
    # Disconnect all but selection

    print(f"=== Disconnecting all but {selected_peer.name}... ===")

    connect_only_to(session, peers.values(), selected_peer)

    print("---")
    print("Applying...")
    wg_peer.wg_apply(session)


    # === SPEEDTEST ===

    print("=== Speedtest autoconnect? (Optional) ===")
    if config.get_do_speedtest():

        # == DO SPEEDTEST ==
        import speedtest_utils

        speed_satisfied = False
        speedtest_candidates: List[WgPeer] = []

        # Test original one first.
        speedtest_current_candidate = selected_peer

        print(f"Testing {speedtest_current_candidate.name}...")
        speed = speedtest_utils.speedtest()
        print(f"{speedtest_current_candidate.name} (Down): {speedtest_utils.format_bps(speed)}")
        speedtest_current_candidate.set_speed(speed)

        # Add candidate, remove from random selection
        speedtest_candidates.append(speedtest_current_candidate)
        candidates.remove(speedtest_current_candidate)

        if speed > config.get_speedtest_threshold():
            print("Speed threshold satisfied.")
            speed_satisfied = True
        else:
            print("Speed threshold not satisfied. Testing another peer...")

        random.shuffle(candidates)

        # The logic here is kind of messy as the first (user-selected) peer has to be handled manually, but it also has to
        # counted for candidate selection and best-effort connection if no peer can reach the threshold. Hopefully there are no bugs :/
        # Also the peer enable states are juggled around since I don't want to waste API latency on redundant disabling/enabling peers, but it's kind of dangerous.
        for i in range(1, config.speedtest_maxtries):
            print("---")
            if speed_satisfied: # Loop passthrough from selected peer above
                break

            if len(candidates) == 0:
                # No more to find
                print("[W] Out of peers to test.")
                break

            # New peer
            speedtest_current_candidate = candidates.pop(0)
            speedtest_candidates.append(speedtest_current_candidate)

            print(f"Speedtest candidate #{i}/{config.speedtest_maxtries}: {speedtest_current_candidate.name}")
            connect_only_to(session, peers.values(), speedtest_current_candidate)

            # Speedtest
            print(f"Testing {speedtest_current_candidate.name}...")
            speed = speedtest_utils.speedtest()
            print(f"{speedtest_current_candidate.name} (Down: {speedtest_utils.format_bps(speed)}, Ping: {speedtest_utils.sp_client.results.ping})")
            speedtest_current_candidate.set_speed(speed)

            if speed > config.get_speedtest_threshold():
                print("Speed threshold satisfied.")
                speed_satisfied = True
                break
            else:
                print("Speed threshold not satisfied. Testing another peer...")


        if not speed_satisfied:
            # All peers failed speed threshold. Go to fastest instead.
            print("Max tries reached / Out of peers. Connecting to best-effort fastest peer.")

        # Connect to the fastest peer.
        # Yes this is unnecessary for most situations, but I don't trust my coding enough plus code is cleaner this way sooo....
        fastest_peer = sorted(speedtest_candidates, key=lambda p1: p1.rx_speed, reverse=True)[0]

        print(f"Connecting to {fastest_peer.name} (Down: {speedtest_utils.format_bps(fastest_peer.rx_speed)})...")
        connect_only_to(session, peers.values(), fastest_peer)

        print("---")
        print("Applying...")
        wg_peer.wg_apply(session)


    # === FINAL APPLY ===
    print ("=== Final apply... ===")
    # These are probably unnecessary, but they seem to fix some monitoring bugs so I kept them.
    print("Restarting WireGuard...")
    output = session.post(f"{config.opnsense_api}/core/service/restart/wireguard/{config.instance_UUID}", verify=False)
    if config.debug:
        print(output.content)

    if config.get_gateway_name() != "":
        print("Resetting Gateway watcher...")
        output = session.post(f"{config.opnsense_api}/core/service/restart/dpinger/{config.get_gateway_name()}", verify=False)
        if config.debug:
            print(output.content)

    print()
    print("============")
    print("DONE!")
    print()
    print("-- SUMMARY ---------------------------------")
    print(f"AUTOMATIC:\t{config.automatic}")

    try:
        # noinspection PyStatementEffect
        speedtest_candidates # Test existence
        print("CONNECTION TYPE:\tSpeedtest")
        print("-------------------------------------------")
        print(f"SEL\tINFO\t\t\t\t\t\t\t\t\t\t\t\tBANDWIDTH")
        for o in speedtest_candidates:
            if o == fastest_peer:
                print(f"[*]\t{o.get_human_info()}\t{speedtest_utils.format_bps(o.rx_speed)}")
            else:
                print(f"[ ]\t{o.get_human_info()}\t{speedtest_utils.format_bps(o.rx_speed)}")
    except NameError:
        print("CONNECTION TYPE:\tManual")
        print(f"== CONNECTION INFO ==")
        print(selected_peer.get_human_info())