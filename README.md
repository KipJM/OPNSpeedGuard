# OPNSpeedGuard
A service that automatically makes an [OPNSense](https://opnsense.org/) firewall's
[WireGuard](https://docs.opnsense.org/manual/how-tos/wireguard-client.html) daemon
switch to another server(peer) when [Speedtest-tracker](https://github.com/alexjustesen/speedtest-tracker) reports the
network bandwidth is below threshold.
