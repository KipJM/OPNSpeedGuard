import random
import config
import name_translation

class WgPeer:

    def __init__(self, json):
        self.json = json

        self.uuid = json["uuid"]
        self.enabled = json["enabled"] == "1"
        self.online = json["peer-status"] == "online"
        self.ifname = json["ifname"]
        self.name = json["name"]
        self.pubkey = json["pubkey"]

        self.tunneladdress = json["tunneladdress"]
        self.serveraddress = json["serveraddress"]
        self.serverport = json["serverport"]

        self.rx = json["transfer-rx"]
        self.tx = json["transfer-tx"]

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

    def is_target(self, target: str) -> bool:
        return self.ifname == target


    def enable(self, session, randomize_port) -> bool:
        if self.enabled:
            return False

        if randomize_port:
            randomize_port(session, 1)
        else:
            session.post(f"{config.opnsense_api}/wireguard/client/toggleClient/{self.uuid}")

        self.enabled = True
        return True

    def disable(self, session) -> bool:
        if not self.enabled:
            return False

        session.post(f"{config.opnsense_api}/wireguard/client/toggleClient/{self.uuid}")

        self.enabled = False
        return True

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

        self.serverport = new_port
