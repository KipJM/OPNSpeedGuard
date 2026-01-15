import json
with open("config.json", "r+") as f:
    l = len(f.read())
    f.seek(0)
    if l == 0 or json.load(f) == {}:
        print("CONFIG FILE DOES NOT EXIST/EMPTY. YOU NEED TO MODIFY SOME VALUES IN config.json")
        data = {
            "keepalive_interval": 25,
            "randomize_port_range": [[53, 53], [123, 123], [443, 443], [4000, 33433], [33565, 51820], [52001,60000]],
            "instance_UUID": "[CHANGE ME]",
            "opnsense_api": "[CHANGE ME] https://192.168.1.1/api",
            "api_file": "api_key.txt"
        }
        with open("config.json", "w+") as f2:
            # load default values
            json.dump(data, f2)
    else:
        data = json.load(f)


keepalive_interval = data["keepalive_interval"]  # Default: 25
randomize_port_range = data["randomize_port_range"]  # Mullvad allowed port ranges. You can remove any undesired port range here.
instance_UUID = data["instance_UUID"]
opnsense_api = data["opnsense_api"]
api_file = data["api_file"]


# Read api key
try:
    with open(api_file) as f:
        api_key = f.readline().strip().removeprefix("key=")
        api_secret = f.readline().strip().removeprefix("secret=")
except FileNotFoundError:
    print("API KEY FILE NOT FOUND!")