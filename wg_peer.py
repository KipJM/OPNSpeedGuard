import random
import time
from typing import Iterable

import config
import name_translation

class WgPeer:

    def __init__(self, json):
        self.online = None
        self.rx = None
        self.tx = None
        self.connection_json = None

        self.json = json

        self.uuid = json["uuid"]
        self.enabled = json["enabled"] == "1"
        self.ifname = json["servers"]
        self.natural_ifname = json["%servers"]
        self.name = json["name"]
        self.pubkey = json["pubkey"]

        self.tunnel_address = json["tunneladdress"]
        self.server_address = json["serveraddress"]
        self.server_port = json["serverport"]

        self.rx_speed = 0.0 # bits
        self.tx_speed = 0.0 # bits

        try:
            country = self.name.split("-")[0]
            city = self.name.split("-")[1]
            self.server = self.name.split("-")[2]

            try:
                self.country = name_translation.country_codes[country.upper()]
                self.city = name_translation.city_codes[city.upper()]

            except KeyError:
                self.country = country.upper()
                self.city = city.upper()

        except IndexError:
            self.country = "Unknown"
            self.city = "Unknown"
            self.server = self.name

    def add_connection_info(self, json) -> None:
        self.connection_json = json
        self.online = json["peer-status"] == "online" # ENABLED ONLY
        self.rx = json["transfer-rx"] # ENABLED ONLY
        self.tx = json["transfer-tx"] # ENABLED ONLY

    def is_target(self, target: str) -> bool:
        return self.uuid == target

    def get_human_info(self) -> str:
        rx = self.rx
        tx = self.tx
        if self.rx > 1000*1000*1000:
            rx = f"{"%.2f" % (self.rx / 1000 / 1000 / 1000)}GB"
        elif self.rx > 1000*1000:
            rx = f"{"%.2f" % (self.rx / 1000 / 1000)}MB"
        elif self.rx > 1000:
            rx = f"{"%.2f" % (self.rx / 1000)}KB"
        else:
            rx = f"{self.rx}B"

        if self.tx > 1000*1000*1000:
            tx = f"{"%.2f" % (self.tx / 1000 / 1000 / 1000)}GB"
        elif self.tx > 1000*1000:
            tx = f"{"%.2f" % (self.tx / 1000 / 1000)}MB"
        elif self.tx > 1000:
            tx = f"{"%.2f" % (self.tx / 1000)}KB"
        else:
            tx = f"{self.tx}B"

        return f"{self.name}\t({self.country},\t{self.city})\t[{rx}/{tx}]"


    def randomize_port(self, session, enable: int) -> None:

        port_range = random.choice(config.randomize_port_range)
        new_port = random.randint(port_range[0], port_range[1])

        request_json = {"client":
            {
                "enabled": enable,
                "name": self.name,
                "pubkey": self.pubkey,
                "psk": "",
                "tunneladdress": self.tunnel_address,
                "serveraddress": self.server_address,
                "serverport": new_port,
                "servers": config.instance_UUID,
                "keepalive": str(config.keepalive_interval),
            }
        }

        output = session.post(f"{config.opnsense_api}/wireguard/client/setClient/{self.uuid}", json=request_json, verify=False)

        if config.debug:
            print(output.content)

        self.server_port = new_port


    def enable(self, session, random_port = False) -> bool:
        if self.enabled:
            if not random_port:
                if config.verbose:
                    print(f"[!] {self.name} is already enabled.")
                return False
            else:
                print(f"[i] {self.name} is already enabled, shuffling ports.")

        if random_port:
            self.randomize_port(session, 1)
        else:
            output = session.post(f"{config.opnsense_api}/wireguard/client/toggleClient/{self.uuid}", verify=False)
            if config.debug:
                print(output.content)

        self.enabled = True
        return True

    def disable(self, session) -> bool:
        if not self.enabled:
            if config.verbose:
                print(f"[!] {self.name} is already disabled.")
            return False

        output = session.post(f"{config.opnsense_api}/wireguard/client/toggleClient/{self.uuid}", verify=False)
        if config.debug:
            print(output.content)

        self.enabled = False
        return True

    def set_speed(self, rx:float = None, tx:float = None) -> None:
        """
        Add speedtest record.
        :param rx: Download. In bits.
        :param tx: Upload. In bits.
        :return: None :3
        """
        if rx is not None:
            self.rx_speed = rx
        if tx is not None:
            self.tx_speed = tx



def connect_only_to(session, all_peers: Iterable[WgPeer], target: WgPeer) -> None:
    """
    Ensure all other peers are disabled except target, which will be ensured enabled.
    This method ensures no unnecessary API calls are made, by utilizing locally-cached enabled info.
    Dangerous if this becomes desynced from OPNSense.
    """
    # WgPeer already skips API calls when enabling/disabling state is already reached, so this method only skip the
    # Enabled->Disable->Enable again API calls for the target peer.

    for idx, peer in enumerate(all_peers):
        if peer != target:
            if config.verbose:
                print(f"Disabling {peer.name} (#{int(idx + 1)})...")
            peer.disable(session)

    print(f"Enabling {target.name}...")
    target.enable(session)

def wg_apply(session) -> None:
    output = session.post(f"{config.opnsense_api}/wireguard/service/reconfigure", verify=False)
    if config.debug:
        print(output.content)

    print("Waiting 1 second before checking status...")
    time.sleep(1)