# -*- coding: utf-8 -*-
"""hwconfig.py

This script is used to initialize any board-specific hardware. Make sure to
edit all definitions to meet the requirements of your board, in this case a
Raspberry Pi Pico.
"""
import machine

SPI_ID = 0
ADS_RESET = machine.Pin(0)
ADS_CS = machine.Pin(1)
ADS_SCLK = machine.Pin(2)
ADS_DIN = machine.Pin(3)
ADS_DOUT = machine.Pin(4)
ADS_SYNC = machine.Pin(5)
ADS_DRDY = machine.Pin(6)
