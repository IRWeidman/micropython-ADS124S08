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
from machine import SPI, Pin, Signal, freq
import utime
import ustruct

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

# Calculate cycles per ns, then divide by 5 because min sleep time is 5 cycles
_NS = (freq()/1e9)/5


# @micropython.asm_thumb
# def _asm_sleep(r0):
#     """Function used to sleep for precice amount of time. Each iteration
#     of this loop takes 5*r0 clock cycles to execute. Minimum sleep time
#     is 5 clock cycles.

#     Args:
#         r0 (int): num cycles to delay
#     """
#     label(delay_loop)
#     sub(r0, r0, 1)      # 1clk
#     cmp(r0, 0)          # 1clk
#     bgt(delay_loop)     # 3clk


class ADS124S08(object):

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
                 drdy: Pin,
                 ref: float = 2.5):
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
        self._drdy = Signal(drdy, invert=True)  # pin is active high
        self.ref = ref
        # Set pin directions
        self._cs.init(mode=Pin.OUT)
        self._rst.init(mode=Pin.OUT)
        self._sync.init(mode=Pin.OUT)

        # Default settings
        self.channel = 0

        # Startup ADS
        self._ads_init()

    def __setattr__(self, name, value):
        if name == 'channel':
            self._set_channel(value)
        if name == 'ref':
            self._set_ref(value)
        super(ADS124S08, self).__setattr__(name, value)

    @property
    def data_ready(self) -> bool:
        return bool(self._drdy())

    def read_int(self) -> int:
        # Append 0-byte to right side to convert to 32-bit while
        #   retaining sign
        reading = self._read_direct()
        # Unpack result into int, big-ending, and right-shift out buffer byte
        return ustruct.unpack('>i', reading + b'\x00')[0] >> 8

    def read_volt(self) -> float:
        reading = self.read_int()
        # Apply conversion
        return reading * (self.ref/(2**23))

    def read_raw(self) -> bytes:
        return self._read_direct()

    def _ads_init(self) -> None:
        # Pin values
        self._cs.high()
        self._rst.high()
        self._sync.high()
        # Sleep for min 4 ads clock cycles, or 97ns @4.096MHz
        #   Round up to 120ns for headroom
        # _asm_sleep(120*_NS)
        utime.sleep_us(20)

        # Reset ads
        self._hard_reset()
        self._soft_reset()

        # Initialize basic settings
        self._set_ref(2.5)
        self._set_channel(1)

        # Start ads
        self._hard_start()
        self._soft_start()

        utime.sleep_us(20)

    def _send_cmd(self, cmd: int) -> None:
        # Take cs low
        self._cs.low()
        # _asm_sleep(120*_NS)
        utime.sleep_us(20)
        # Write data
        self._spi.write(bytes([cmd]))
        # Take cs high
        self._cs.high()
        # _asm_sleep(120*_NS)
        utime.sleep_us(20)

    def _set_channel(self, channel: int) -> None:
        if channel not in range(12):
            raise ValueError("Channel must be between 0 and 11")
        channel = (channel << 4) + 0x00
        self._write_reg(_ADS_INPMUX, channel)

    def _set_ref(self, ref: float) -> None:
        if ref == 2.5:
            # Reference voltage settings
            # 00: ref monitor disabled (default)
            # 0:  positive ref buffer bypass enabled (default)
            # 1:  negative ref buffer bypass disabled (default)
            # 10: internal 2.5v ref
            # 10: internal reference always on
            # 0011 1010 -> 0x3A
            self._write_reg(reg=_ADS_REF, data=0x1A)
        else:
            # Reference voltage settings
            # 00: ref monitor disabled (default)
            # 0:  positive ref buffer bypass enabled (default)
            # 1:  negative ref buffer bypass disabled (default)
            # 00: REFP0, REFN0 (default)
            # 00: internal reference off (default)
            # 0001 0000 -> 0x10
            self._write_reg(reg=_ADS_REF, data=0x10)

    def _read(self) -> bytes:
        # Prepare buffers
        write_buf = bytearray([_RDATA, _NOP, _NOP, _NOP])
        read_buf = bytearray(4)

        self._cs.low()
        utime.sleep_us(20)
        # write _RDATA, then read 3 bytes
        self._spi.write_readinto(write_buf, read_buf)
        self._cs.high()

        # Combine 3 bytes in from ADS into a single int, big endian
        return read_buf[1:]

    def _read_direct(self) -> bytearray:
        # Prepare buffer
        read_buf = bytearray(3)

        self._cs.low()
        utime.sleep_us(20)
        # Read 3 bytes
        self._spi.readinto(read_buf, _NOP)
        self._cs.high()
        return read_buf

    def _soft_reset(self) -> None:
        self._send_cmd(_RESET)
        # Delay for minimum of 4096tclk
        # _asm_sleep(397312*_NS)
        utime.sleep_ms(20)

    def _soft_start(self) -> None:
        self._send_cmd(_START)
        # Delay for a minimum of 20ns (td(sccs))
        # _asm_sleep(40*_NS)
        utime.sleep_us(20)

    def _hard_reset(self) -> None:
        self._rst.low()
        # Delay for minimum of 4tclk (tw(RSL))
        # _asm_sleep(120*_NS)
        utime.sleep_us(20)
        self._rst.high()

    def _hard_start(self) -> None:
        self._sync.low()
        # Delay for minimum of 4tckl (tw(STH)/tw(STL))
        # _asm_sleep(120*_NS)
        utime.sleep_us(20)

    def _write_reg(self, reg: int, data: int):
        # Prepare data to send
        #   3 bytes: reg address, num bytes to write, data to write
        write_buf = bytearray([_WREG+reg, 0x00, data])
        self._cs.low()
        utime.sleep_us(20)
        # Write data to reg
        self._spi.write(write_buf)
        utime.sleep_us(20)
        self._cs.high()

    def _read_reg(self, reg: int):
        pass
# spi.write(bytes([0x12]))
# spi.read(3, 0x00)
