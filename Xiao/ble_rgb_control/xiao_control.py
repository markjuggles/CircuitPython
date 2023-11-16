# Author: Mark Johnson
# Purpose: Create a command line application to send commands to a BLE device.
#          The emulates Bluefruit Connect, Controller, Control Pad.
#          It controls a CircuitPython board running 'ble_rgb_button.py'.


"""
UART Service
-------------

An example showing how to write a simple program using the Nordic Semiconductor
(nRF) UART service.

"""

import asyncio
import sys
from itertools import count, takewhile
from typing import Iterator

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# from adafruit_bluefruit_connect.packet import Packet
# from adafruit_bluefruit_connect.button_packet import ButtonPacket
from button_packet import ButtonPacket

from time import sleep

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


# TIP: you can get this function and more from the ``more-itertools`` package.
def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """
    Slices *data* into chunks of size *n*. The last slice may be smaller than
    *n*.
    """
    return takewhile(len, (data[i : i + n] for i in count(0, n)))


async def uart_terminal():
    """This is a simple "terminal" program that uses the Nordic Semiconductor
    (nRF) UART service. It reads from stdin and sends each line of data to the
    remote device. Any data received from the device is printed to stdout.
    """

    def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
        # This assumes that the device includes the UART service UUID in the
        # advertising data. This test may need to be adjusted depending on the
        # actual advertising data supplied by the device.
        if UART_SERVICE_UUID.lower() in adv.service_uuids:
            return True

        return False

    device = await BleakScanner.find_device_by_filter(match_nus_uuid)

    if device is None:
        print("no matching device found, you may need to edit match_nus_uuid().")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print("received:", data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected, start typing and press ENTER...")

        loop = asyncio.get_running_loop()
        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        while True:
            # This waits until you type a line and press ENTER.
            # A real terminal program might put stdin in raw mode so that things
            # like CTRL+C get passed to the remote device.

            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)

            # data will be empty on EOF (e.g. CTRL+D on *nix)
            if len(data) == 0:
                break
            else:
                cmd = data.decode()
                cmd = cmd.strip()

            # Convert u, d, l, r to there numeric values per the Adafruit Packet specification.
            if cmd.startswith('u'):
                cmd = '5'
            elif cmd.startswith('d'):
                cmd = '6'
            elif cmd.startswith('l'):
                cmd = '7'
            elif cmd.startswith('r'):
                cmd = '8'

            # Press 'q' or 'quit' to quit.
            if cmd.startswith('q'):
                break
            
            # Only allow one character.
            if len(cmd) != 1:
                print('Single characters please.')
                continue
            
            # Create the packet.  Definitely put this in a try/except.
            try:
                pkt = ButtonPacket(cmd, True)
                # if alt:
                #     pkt = ButtonPacket('8', True)
                # else:
                #     pkt = ButtonPacket('6', True)
            except Exception as err:
                print(str(err))
                break

            pktbytes = pkt.to_bytes()

            # some devices, like devices running MicroPython, expect Windows
            # line endings (uncomment line below if needed)
            # data = data.replace(b"\n", b"\r\n")

            # Writing without response requires that the data can fit in a
            # single BLE packet. We can use the max_write_without_response_size
            # property to split the data into chunks that will fit. (Currenty 509 bytes.)

            for s in sliced(pktbytes, rx_char.max_write_without_response_size):
                await client.write_gatt_char(rx_char, s, response=False)

            print(f"sent: {cmd}")



if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        # task is cancelled on disconnect, so we ignore this error
        pass


