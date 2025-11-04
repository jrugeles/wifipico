# Digital Communications - UMNG
# jose.rugeles@unimilitar.edu.co
#
# Description:
# Minimal MicroPython script that prints the Raspberry Pi Pico W Wi-Fi
# MAC address (Station/STA interface) in colon-separated hexadecimal.
# It enables the Wi-Fi interface, reads the 6-byte MAC, formats it,
# prints the result, and (optionally) disables the interface.

import network

# Create and enable the Wi-Fi station interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Read the 6-byte MAC address and format as colon-separated hex
mac_bytes = wlan.config('mac')
mac_str = ':'.join(f'{b:02X}' for b in mac_bytes)

print("Raspberry Pi Pico W MAC (STA):", mac_str)

# Turn Wi-Fi OFF to save power if no further Wi-Fi actions are needed
wlan.active(False)
