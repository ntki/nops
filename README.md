# nops - a bitbang framework

## Motivation
I wrote this framework to help me try out various programmable EEPROMs, microcontrollers, etc.. without purchasing any additional HW/SW.
The aim of this project is two-fold:
1. to use potentially anything with general purpose IO pins to emit the bitpatterns used for programming,
2. be able to handle new targets/ICs by writing a few dozen lines of python code based on its datasheet.

## Basic structure
The framework has 3 core parts:
- Loaders: classes implementing a simple interface driving the associated hardware to control the GPIO pins
- Targets: functions, using - through a proxy - a selected Loader to assemble the correct bitpatterns for programming, given a potential input, returning read data
- PinProxy: this is the object that connects the formentioned two parts. Translating target pins to loader provided pins. Eg.: SPI_MISO<->D1_MINI_D3, SPI_RESET<->RPi_GPIO37
This structure enables adding support for new hardware and target devices independently of each other.

###  Currently supported HW/Loader (lib/loader):
- rpi: locally run on an RPi, tested with Raspberry Pi 3B
- rpi_remote: requires the misc/rpi_tcplistener.py to run on a remote RPi (see examples)
- d1mini: for Arduino compatible D1 Mini clone (Esp8266) the firmware can be found under misc/fw_d1mini
  depends on pyserial

## Examples
Write ee93lc66 through d1mini with data from data.hexd:
    python3 -m venv venv
    . ./venv/bin/activate
    python3 -m pip install pyserial
    ./nops -l d1mini -t ee93lcx6.write --ta model=66 -p CS=D3,CLK=D5,DI=D7,DO=D0,ORG=D1 -f hexd -i data.hexd

Read an attiny2313 flash through rpi_remote loader and print intelhex32 dump to stdout:
- setup the server:
    scp misc/rpi_tcpserver.py rpi:/tmp/rpi_tcpserver.py
    ssh -L 30456:localhost:30456 -t rpi -- /tmp/rpi_tcpserver.py
- then locally:
    ./nops -l rpi_remote -p RESET=35,SCK=36,MISO=37,MOSI=38 -t avr_spi.read_flash -f inhx32

As is, no warranty, nor any responsibility.
