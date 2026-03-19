import json
import random
from operator import truediv


def wait_for_user_input(name: str):
    while True:
        user_input = input(f"[?] {name}? (Y/N): ")
        if user_input.lower() == "y":
            print(f"{name} [ENABLED]")
            return True
        elif user_input.lower() == "n":
            print(f"{name} [DISABLED]")
            return False

def get_do_disable_first() -> bool:
    return wait_for_user_input("Disable all peers first")

def get_do_randomize() -> bool:
    return wait_for_user_input("Randomize ports")

def get_peer_selection(length: int) -> int:
    # Manual
    if automatic:
        return random.randint(0, length - 1)
    else:
        return int(input("Select the target server [index]: ")) - 1  # Index starts at 1

def get_do_speedtest() -> bool:
    if automatic:
        return True
    else:
        return wait_for_user_input("Use speedtest to automatically select server")


def get_speedtest_threshold() -> int:
    """
    :returns in mbps.
    """
    return speedtest_threshold

def get_gateway_name() -> str:
    return gateway_name


with open("config.json", "r+") as f:
    data = json.load(f)
    if data == {}:
        print("CONFIG FILE DOES NOT EXIST/EMPTY. YOU NEED TO MODIFY SOME VALUES IN config.json")
        data = {
            "keepalive_interval": 25,
            "randomize_port_range": [[53, 53], [123, 123], [443, 443], [4000, 33433], [33565, 51820], [52001,60000]],
            "instance_UUID": "[CHANGE ME]",
            "opnsense_api": "[CHANGE ME] https://192.168.1.1/api",
            "api_file": "api_key.txt",
            "debug": False,
            "automatic": False,
            "speedtest_threshold": 25,
            "speedtest_maxtries": 5,
            "gateway_name": "", #OPTIONAL
        }
        with open("config.json", "w+") as f2:
            # load default values
            json.dump(data, f2)
        exit(-1)


keepalive_interval = data["keepalive_interval"]  # Default: 25
randomize_port_range = data["randomize_port_range"]  # Mullvad allowed port ranges. You can remove any undesired port range here.
instance_UUID = data["instance_UUID"]
opnsense_api = data["opnsense_api"]
api_file = data["api_file"]
speedtest_threshold = data["speedtest_threshold"]  # MB
speedtest_maxtries = data["speedtest_maxtries"]

try:
    debug = data["debug"]
    automatic = data["automatic"]
    gateway_name = data["gateway_name"]
except KeyError:
    debug = False
    automatic = False
    gateway_name = ""

# Read api key
try:
    with open(api_file) as f:
        api_key = f.readline().strip().removeprefix("key=")
        api_secret = f.readline().strip().removeprefix("secret=")
except FileNotFoundError:
    print("API KEY FILE NOT FOUND!")