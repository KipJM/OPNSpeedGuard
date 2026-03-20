import config

print ("Creating speedtest client")
import speedtest
sp_client = speedtest.Speedtest(secure=True)
print("Getting speedtest servers...")
sp_client.get_servers()

def speedtest() -> float:
    print("Getting best server...")
    sp_client.get_best_server()
    if config.debug:
        print(f"Closest server: {sp_client.closest}")

    print("Starting download speedtest.")
    dl_speed = sp_client.download()

    return dl_speed

def format_bps(bps: float) -> str:
    if bps > 1000 * 1000 * 1000:
        return f"{"%.1f" % (bps/1000/1000/1000)}gbps"
    elif bps > 1000 * 1000:
        return f"{"%.1f" % (bps/1000/1000)}mbps"
    elif bps > 1000:
        return f"{"%.1f" % (bps/1000)}kbps"
    else:
        return f"{"%.1f" % bps}bits/s"