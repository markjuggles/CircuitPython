# File: RGB_Buttons.py
#       This is a modified versions of 'ble_button_press.py' from Adafruit.
#       The Left, Up, Right keys now turn on the RGB LEDs.
#       The Down key turns of the LEDs.
#       LEDs are Active Low so a False=on and True=off.
#
# SPDX-FileCopyrightText: 2019 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.button_packet import ButtonPacket

import board
import digitalio

led_r = digitalio.DigitalInOut(board.LED_RED)
led_r.direction = digitalio.Direction.OUTPUT
led_g = digitalio.DigitalInOut(board.LED_GREEN)
led_g.direction = digitalio.Direction.OUTPUT
led_b = digitalio.DigitalInOut(board.LED_BLUE)
led_b.direction = digitalio.Direction.OUTPUT

led_r.value = True
led_g.value = True
led_b.value = True

ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)


while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass

    # Now we're connected

    while ble.connected:
        if uart.in_waiting:
            packet = Packet.from_stream(uart)
            if isinstance(packet, ButtonPacket):
                if packet.pressed:
                    if packet.button == ButtonPacket.BUTTON_1:
                        # The 1 button was pressed.
                        led_r.value = True
                        led_g.value = True
                        led_b.value = True
                        print("1 button pressed!")
                    elif packet.button == ButtonPacket.LEFT:
                        led_r.value = False
                    elif packet.button == ButtonPacket.UP:
                        led_g.value = False
                    elif packet.button == ButtonPacket.RIGHT:
                        led_b.value = False
                    elif packet.button == ButtonPacket.DOWN:
                        led_r.value = True
                        led_g.value = True
                        led_b.value = True

                    print(packet)

    # If we got here, we lost the connection. Go up to the top and start
    # advertising again and waiting for a connection.

