# micropython-ADS124S08

A micropython driver for the ADS124S08 ADC module from Texas Instruments

## Description

This repository contains a MicroPython driver for interfacing with the ADS124S08 ADC module from Texas Instruments. The driver aims to provide an easy-to-use interface for configuring the ADC, reading conversion data, and controlling various settings.

⚠️ ***Warning***: This driver is a work in progress and may not work in its current state. ⚠️

## Installation

1. Clone the repository:

```
git clone https://github.com/your_username/ADS124S08-MicroPython-Driver.git
```

2. Copy `ads124s08.py` onto your microcontroller

## Usage

``` python
import machine
import time
import ads124s08

# Initialize pins and spi according to your wiring
spi = SPI(baudrate=10_000_000, polarity=0, phase=1, firstbit=SPI.MSB,
          sck=machine.Pin(2), mosi=machine.Pin(3), miso=machine.Pin(4))
cs_pin = machine.Pin(1)
rst_pin = machine.Pin(0)
sync_pin = machine.Pin(5)
drdy_pin = machine.Pin(6)

# Create ads object
ads = ads124s08.ADS124S08(spi=spi, cs=cs_pin, reset=rst_pin,
                          sync=sync_pin, drdy=drdy_pin)


while True:
    # Wait for data availability
    print('waiting for data', end='')
    while not ads.data_ready:
        print('.', end='')
        utime.sleep_ms(250)
    print(ads.data_ready)

    print('--------------------')

    # Print the readings on each channel
    for i in range(12):
        ads.channel = i
        reading = ads.read()

        print(f'channel_{i : <4}|{reading : >7}')

        time.sleep_ms(250)
    print()
