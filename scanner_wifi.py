# Digital Communications - UMNG
# jose.rugeles@unimilitar.edu.co

# Slightly improved Wi-Fi scanner for Raspberry Pi Pico 2W (MicroPython)
# - Reuses the station interface between scans (faster)
# - Prints SSID, BSSID (AP MAC), channel, and RSSI
# - Basic error handling and graceful cleanup

import network
import time

SCAN_INTERVAL_S = 10

def to_mac(b: bytes) -> str:
    """Format raw BSSID bytes as colon-separated uppercase hex (e.g., 12:34:56:AB:CD:EF)."""
    return ":".join(f"{x:02X}" for x in b)

def format_ap(ap_tuple):
    """
    Defensive unpacking across ports/drivers.
    Common order (ESP/Pico W):
    (ssid, bssid, channel, rssi, authmode [, hidden])
    """
    ssid    = ap_tuple[0].decode('utf-8', 'ignore') or "<hidden>"
    bssid   = to_mac(ap_tuple[1]) if len(ap_tuple) > 1 else "00:00:00:00:00:00"
    channel = ap_tuple[2] if len(ap_tuple) > 2 else "?"
    rssi    = ap_tuple[3] if len(ap_tuple) > 3 else "?"
    return ssid, bssid, channel, rssi

def main():
    wlan = network.WLAN(network.STA_IF)   # Station interface
    wlan.active(True)                     # Keep it active between scans

    # Optional: ensure we're not connected while scanning
    try:
        if wlan.isconnected():
            wlan.disconnect()
    except Exception:
        pass

    while True:
        try:
            print("Scanning for Wi-Fi access points...")
            aps = wlan.scan()  # May raise OSError if radio is busy
            if not aps:
                print("No APs found.")
            else:
                # Sort by RSSI (desc) for readability
                try:
                    aps.sort(key=lambda t: t[3], reverse=True)
                except Exception:
                    pass

                for ap in aps:
                    ssid, bssid, ch, rssi = format_ap(ap)
                    print(f"CH {ch:>2} | RSSI {rssi:>3} dBm | BSSID {bssid} | SSID: {ssid}")

        except OSError as e:
            print(f"Scan failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        print(f"Waiting {SCAN_INTERVAL_S} seconds before next scan...\n")
        time.sleep(SCAN_INTERVAL_S)

try:
    main()
finally:
    # Best-effort cleanup if the script is interrupted
    try:
        network.WLAN(network.STA_IF).active(False)
    except Exception:
        pass
