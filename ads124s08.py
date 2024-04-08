# -*- coding: utf-8 -*-
"""
ads124s08.py

Description:
    A Micropython driver for the Texas Instruments ADS124S08 ADC module

Author:
    Isaak Weidman - isaak.w@quub.space

Date:
    Created:        2024-04-08
    Last Edited:    2024-04-08

The MIT License (MIT)
Copyright (c) 2024 Isaak Weidman, isaak.w@quub.space
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

__author__ = "Isaak Weidman"
__email__ = "isaak.w@quub.space"
__license__ = "MIT"
__status__ = "Prototype"

# Imports
from micropython import const
from machine import SPI, Pin, Signal

# Conversion constants
_VREF = const(2.5)
_RES = _VREF/(2**23)

# Registers
_ADS_ID = const(0x00)
_ADS_STATUS = const(0x01)
_ADS_INPMUX = const(0x02)
_ADS_PGA = const(0x03)
_ADS_DATARATE = const(0x04)
_ADS_REF = const(0x05)
_ADS_IDACMAG = const(0x06)
_ADS_IDACMUX = const(0x07)
_ADS_VBIAS = const(0x08)
_ADS_SYS = const(0x09)
_ADS_OFCAL_0 = const(0x0A)
_ADS_OFCAL_1 = const(0x0B)
_ADS_OFCAL_2 = const(0x0C)
_ADS_FSCAL_0 = const(0x0D)
_ADS_FSCAL_1 = const(0x0E)
_ADS_FSCAL_2 = const(0x0F)
_ADS_GPIODAT = const(0x10)
_ADS_GPIOCON = const(0x11)

# Control commands
_NOP = const(0x00)
_WAKEUP = const(0x02)  # or 0x03
_PWRDN = const(0x04)  # or 0x05
_RESET = const(0x06)  # or 0x07
_START = const(0x08)  # or 0x09
_STOP = const(0x0A)  # or 0x0B
# Calibration commands
_SYOCAL = const(0x16)
_SYGCAL = const(0x17)
_SFOCAL = const(0x19)
# Data read command
_RDATA = const(0x12)  # or 0x13
# Reg read/write commands
_RREG = const(0x20)
_WREG = const(0x40)


class ADS124S08():
    """Driver class for Texas Instruments ADS124S08

    Attributes:
        channel (int):
            current slected channel, between 0 and 11
        data_read (bool):
            Indicates the presence of conversion data from ADC unit

    Methods:
        read() -> int:
            returns the value on selected channel
    """
    def __init__(self,
                 spi: SPI,
                 cs: Pin,
                 reset: Pin,
                 sync: Pin,
                 drdy: Pin):
        """Constructs all attributes required to drive ADC unit, applies
        definded configuration, and begins the ADC

        Args:
            spi (SPI):
                SPI object used for communication
            cs (Pin):
                Chip select pin attched to ADC unit
            reset (Pin):
                Reset pin used to reset the ADC configuration
            sync (Pin):
                Sync/Start pin used to begin ADC conversion data
            drdy (Pin):
                Data ready pin indicating the presence of conversion data from
                ADC unit
        """
        # Declare properties
        self._spi = spi
        self._cs = cs
        self._rst = reset
        self._sync = sync
        self._drdy = Signal(drdy, inverted=True)  # pin is active high
        # Set pin directions
        self._cs.init(mode=Pin.OUT)
        self._rst.init(mode=Pin.OUT)
        self._sync.init(mode=Pin.OUT)
        self._drdy.init(mode=Pin.IN)

        # Default settings
        self._channel = 0

        # Startup ADS
        self._ads_init()

    def _ads_init(self) -> None:
        # Reset ads)
        self._ads_reset()
        self._send_cmd(_RESET)
        # Initialize basic settings
        self._write_reg(reg=_ADS_INPMUX, data=0x0C)
        self._write_reg(reg=_ADS_REF, data=0x1A)  # Reference voltage is 2.6v)
        # Start ads
        self._sync.value(1)
        self._sync.value(0)

        self._send_cmd(_START)

    def _ads_reset(self) -> None:
        self._rst.value(1)
        self._rst.value(0)
        self._rst.value(1)

    def _write_reg(self, reg: int, data: int):
        # Prepare data to send
        #   3 bytes: reg address, num bytes to write, data to write
        write_buf = bytearray([_WREG+reg, 0x00, data])
        self._cs.low()
        # Write data to reg
        self._spi.write(write_buf)
        self._cs.high()

    def _read_reg(self, reg: int):
        pass

    def _send_cmd(self, cmd: int) -> None:
        # Take cs low
        self._cs.low()
        # Write data
        self._spi.write(bytes([cmd]))
        # Take cs high
        self._cs.high()

    def _ads_read(self) -> int:
        # Prepare buffers
        write_buf = bytearray([_RDATA, _NOP, _NOP, _NOP])
        read_buf = bytearray(4)

        self._cs.low()
        # write _RDATA, then read 3 bytes
        self._spi.write_readinto(write_buf, read_buf)
        self._cs.high()

        # Combine 3 bytes in from ADS into a single int, big endian
        return int.from_bytes(read_buf[1:], "big")

    def _ads_read_direct(self) -> int:
        # Wait for drdy to transition low
        if self._drdy:
            self._cs.low()
            # Read 3 bytes
            data = self._spi.read(3, _NOP)
            self._cs.high()
            return int.from_bytes(data, "big")
        else:
            return -1

    def read(self) -> int:
        return self._ads_read_direct()

    @property
    def channel(self) -> int:
        return self._channel

    # Sets ain-positive to selected channel (channel << 4)
    #   and ain-negative to ain-common (0x0C, i.e. 12)
    #   Ex: to set channel to 5, write 0x5C to INPMUX channel
    @channel.setter
    def channel(self, channel: int):
        # Ensure channel is valid
        if channel not in range(12):
            raise ValueError("Channel invalid.",
                             "Channel must be between 0 and 11")
        self._channel = channel
        channel = (channel << 4) + 0x0C
        self._write_reg(_ADS_INPMUX, channel)

    @property
    def data_ready(self) -> bool:
        return not self._drdy.value()
# spi.write(bytes([0x12]))
# spi.read(3, 0x00)
