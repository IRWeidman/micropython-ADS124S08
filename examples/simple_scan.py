# -*- coding: utf-8 -*-
"""simple_scan.py

Demonstrates the use of ads124s08.py by continuously printing each channel of
the ADC unit to the screen.

Use hwconfig.py to define the pins used in your specific scenario.
"""
import machine
import time
import hwconfig as hw
import ads124s08

# Create SPI object
spi = machine.SPI(hw.SPI_ID, baudrate=10_000_000, polarity=0, phase=1,
                  firstbit=machine.SPI.MSB, sck=hw.ADS_SCLK,
                  mosi=hw.ADS_DIN, miso=hw.ADS_DOUT)
# Create ads object
ads = ads124s08.ADS124S08(spi=spi, cs=hw.ADS_CS, reset=hw.ADS_RESET,
                          sync=hw.ADS_SYNC, drdy=hw.ADS_DRDY)


if __name__ == '__main__':
    while True:
        # Print the readings on each channel
        for i in range(12):
            ads.channel = i
            time.sleep_ms(500)
            reading = ads.read_int()

            print(f'channel_{i:<4}|{reading:>7}')
        print()
