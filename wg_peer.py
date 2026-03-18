import random
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
        self.naturalifname = json["%servers"]
        self.name = json["name"]
        self.pubkey = json["pubkey"]

        self.tunneladdress = json["tunneladdress"]
        self.serveraddress = json["serveraddress"]
        self.serverport = json["serverport"]

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

    def add_connection_info(self, json):
        self.connection_json = json
        self.online = json["peer-status"] == "online" # ENABLED ONLY
        self.rx = json["transfer-rx"] # ENABLED ONLY
        self.tx = json["transfer-tx"] # ENABLED ONLY

    def is_target(self, target: str) -> bool:
        return self.uuid == target

    def get_human_info(self) -> str:
        rx = self.rx
        tx = self.tx
        if self.rx > 1000*1000:
            rx = f"{self.rx / 1000 / 1000}MB"
        elif self.rx > 1000:
            rx = f"{self.rx / 1000}KB"
        else:
            rx = f"{self.rx}B"

        if self.tx > 1000*1000:
            tx = f"{self.tx / 1000 / 1000}MB"
        elif self.tx > 1000:
            tx = f"{self.tx / 1000}KB"
        else:
            tx = f"{self.tx}B"

        return f"{self.name} ({self.country}, {self.city}) [{rx}/{tx}]"


    def randomize_port(self, session, enable: int):

        port_range = random.choice(config.randomize_port_range)
        new_port = random.randint(port_range[0], port_range[1])

        request_json = {"client":
            {
                "enabled": enable,
                "name": self.name,
                "pubkey": self.pubkey,
                "psk": "",
                "tunneladdress": self.tunneladdress,
                "serveraddress": self.serveraddress,
                "serverport": new_port,
                "servers": config.instance_UUID,
                "keepalive": str(config.keepalive_interval),
            }
        }

        output = session.post(f"{config.opnsense_api}/wireguard/client/setClient/{self.uuid}", json=request_json, verify=False)

        if config.debug:
            print(output.content)

        self.serverport = new_port


    def enable(self, session, random_port) -> bool:
        if self.enabled:
            print(f"[!] {self.name} is already enabled.")
            return False

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
            print(f"[!] {self.name} is already disabled.")
            return False

        output = session.post(f"{config.opnsense_api}/wireguard/client/toggleClient/{self.uuid}", verify=False)
        if config.debug:
            print(output.content)

        self.enabled = False
        return True