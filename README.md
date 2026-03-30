# OPNSpeedGuard
A tool that automatically makes an [OPNSense](https://opnsense.org/) firewall's WireGuard daemon
switch to another server(peer) with a good bandwidth, for use in a 
[road warrior setup](https://docs.opnsense.org/manual/how-tos/wireguard-client.html) in situations where WireGuard connectivity might be unstable.
<img width="2239" height="477" alt="image" src="https://github.com/user-attachments/assets/1c91ec88-6c5d-4be8-9e1d-7a9f732bdb35" />

This tool automatically makes OPNSense connect to a reachable peer with good internet bandwidth, similar to how "auto location" works in a consumer VPN app.
> Disclaimer: This tool will not and can not circumvent network restrictions. It's merely for managing the WireGuard daemon on an OPNSense firewall. Do with this information what you will.

# Demo

### Short demo of this tool: [Youtube Video](https://www.youtube.com/watch?v=QV3KI8_WcJI)
### Installation, setup, and a full manual run with debug mode turned on: [Youtube Video](https://www.youtube.com/watch?v=OmvgO1MNlaU)

# Install
Install it as a [python package on PyPI](https://pypi.org/project/opnspeedguard), via the CLI:

#### For pip:
Run `pip install opnspeedguard` or `python -m pip install opnspeedguard`
#### For pipx:
Run `pipx install opnspeedguard`

---
if pip is configured with PATH, just run `opnspeedguard [args]` like any other CLI tool. Please read below on how to configure and use it.

# Usage
## Setup
As stated, this only works for a road warrior setup. Specifically, this is designed for Mullvad, for
use in conjunction with my [OpnsenseMullvadPeerAdder](https://github.com/KipJM/OpnsenseMullvadPeerAdder).
However this tool will work with other wg setups as well, but some cosmetic features will be broken.

**You'll need two things:**
- api_key.txt: API key file
- config.json: tool config file

### api_key.txt
You can retrieve this from your OPNSense web UI.
1. Go to your web UI
2. Switch to System > Access > Users
3. It is recommended to create a dedicated app user for security, but you do you.
4. Make sure the user has at least the following permissions:
   - **VPN: WireGuard: Configuration**
   - **VPN: WireGuard: Status**
   - System: Gateways _(optional, for resetting gateway watcher)_ 
5. Generate the api_key.txt file by clicking the ticket button next to the user. It is recommended to rename the file "api_key.txt". Inside should be two lines, key=..., secret=... .
6. Either pass its path through the -api argument, or put it in the working directory and the tools will find it automatically (must be call "api_key.txt").

### config.json
This controls most behaviors of OPNSpeedGuard. A few optional controls are given through CLI prompts if `automatic=false`.

You can generate a template via the command `opnspeedguard --genconfig --config [path to generated config file]`.
Once generated, you'll have to edit some of its values. **Descriptions on what each variable controls can be found in
[config.py](https://github.com/KipJM/opnspeedguard/blob/master/config.py).**

**YOU MUST EDIT `instance_UUID` and `opnsense_api`:**
- `instance_UUID`: Can be found via devtools or this [script](https://github.com/KipJM/OpnsenseMullvadPeerAdder/blob/master/config_and_run_me_first.py).
- `opnsense_api`: URL to your firewall's web portal, include the /api location. The script has certificate verification turned off, so feel free to use self-signed HTTPS.  

### Pre-running
**The tool performs the speedtest from the computer the script is running on, instead of on the OPNSense firewall.** 
Therefore, ensure your computer's Internet access is routed through OPNSense's WireGuard instance before running the app.

## Running
Run `opnspeedguard  [...]` or `python -m opnspeedguard [...]`, like any other CLI tool.

**Run `opnspeedguard -h` for help information.**

_The tool itself should contain enough help info on what each step and argument does._

For automatic mode (`automatic=true` in config.json), user input will be automatically emulated with default values.
If automatic mode is off, you'll have to provide user input at multiple points in the execution process to dictate the tool's behavior.

### Behavior
Below demonstrates a typical long run of the tool. Based on your configuration, the tool may skip some of the mentioned steps.

1. Disconnect from all the peers (optional)
   - For preventing some random monitoring bugs within OPNSense
2. Connect to all peers
   - (optional) randomize the connected port of each peer. Your peers must support this feature. Port ranges are defined in `config.json`
3. Test basic connectivity to each peer
   - Done using OPNSense's builtin feature
4. Displays available peers with human-readable names.
   - Peers must be formated with [OpnsenseMullvadPeerAdder](https://github.com/KipJM/OpnsenseMullvadPeerAdder) for this feature to work.
5. User select the peer to connect to / tool randomly select a peer to connect to
6. (optional) Test download bandwidth of this peer
7. If bandwidth threshold is not reached, randomly try another peer.
   - Stop until either a satisfactory peer is found, or `maxtries` is reached.
8. Connect to the peer with the highest bandwidth.
9. Print results summary.

# Optimization
Compared to V1 found in [OpnsenseMullvadPeerAdder](https://github.com/KipJM/OpnsenseMullvadPeerAdder), this version is completely rewritten to reduce wait time caused
by unnecessary API calls. Information about peers is instead cached locally, and redundant peer enabling/disabling are removed.

This does increase the risk of desynchronization between the tool and OPNSense, but as long as no one touches the wg portion
of the web panel, this should theoretically run without risk.

# License
```
OPNSpeedGuard: A tool that automatically makes an OPNSense firewall's WireGuard daemon
switch to another server(peer) with a good bandwidth, for use in a road warrior setup.
Copyright (C) 2026 KIP

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

You can contact me, the author, via email at oss@kip.gay.
```
_OPNSense, WireGuard, and Mullvad are registered trademarks of their respective owners. This is an unofficial project not associated nor endorsed with/by these entities._
