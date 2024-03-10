# Motion-Detect Media Player Kodi Addon

## Introduction

This Addon is a Media Player useful to play some video / audio in Kiosk mode only if a people is approaching the sensor.

This Addon is developed on Raspberry Pi (different version are tested, also RasPi WiFi Zero) and require a presence sensor:

* **Ultrasonic Sensor**: because it measure distance, is useful to stop media reproduction if there are no people around
* **PIR Sensor**: is useful to check if someone is approaching, but media is played until it ends (also if there are no people around)


## Configuration

In Setting Page some items help to customize behavior of Addon:

* **Sensor Type**: choose sensor between Ultrasonic (HC-SR04) or PIR (HC-SR501)
* **GPIO pin: Start measure**: Raspberry GPIO pin to start distance measure *(only Ultrasonic)*
* **GPIO pin: Sensor Input**: Raspberry GPIO pin to receive Sensor Input
* **Distance to Start Video**: minimum distance sensor-people to start video - max 400 cm *(only Ultrasonic)*
* **Distance to Stop Video**: maximum distance sensor-people to stop video - max 400 cm *(only Ultrasonic)*
* **Stop Time**: countdown time before stop video if people is too far from sensor; if user re-approach, countdown stop *(only Ultrasonic)*
* **Idle Media Blank**: if activated, in idle mode a black screen is shown
* **Idle Media Content**: if previuos setting is not activated, in idle mode a custom media file can be reproduced in loop
* **Media to Play**: choose media to reproduce when someone approach sensor
* **Start Test**: show a test dialog for snsor, useful to tune previous settings
* **Stop Addon**: useful to stop this addon during tests

To start this addon, use instead default *Open* button in Addon Page.

If you want to start this addon at Kodi boot, I suggest to use [Kodi Autoplay Addon](https://github.com/leo-c/service.autoexec.addon)
(check correct branch for your Kodi version)


## Hardware

### HC-SR04 / SRF05 / HY-SRF05 (Ultrasonic)

This Ultrasonic sensor require 5Vcc for powering, and produce output at 5V, then a simple voltage divider is needed:
![Voltage divider](docs/Vdiv.png)  
(also works with 2 resistances both of 5k ohm - 10 kohm because Raspberry inputs can be driven also with 2.5 V)

Luckily, sensor accept any trigger signal above 2.5V, then Raspbery can drive it directly with a 3.3V signal

Wiring follows:
| RasPi GPIO pin # | Raspi GPIO pin signal | Sensor pin |        Notes        |
| :--------------: | :-------------------: | :--------: | :------------------ |
|        2         |         +5V           |    Vcc     |                     |
|        6         |         GND           |    GND     |                     |
|       16         |       GPIO #23        |  Trigger   |                     |
|       18         |       GPIO #24        |    Echo    | use voltage divider |

**WARN**: some SRF05-compatible sensors have Echo-Trigger pins swapped


### HC-SR501 / HC-SR505 (PIR)

Those PIR sensors must be feeded with 5V, but produce output at 3.3 V, so they does not require other electronic components

Wiring follows:
| RasPi GPIO pin # | Raspi GPIO pin signal | Sensor pin |
| :--------------: | :-------------------: | :--------: |
|        2         |         +5V           |    Vcc     |
|        6         |         GND           |    GND     |
|       18         |       GPIO #24        |    OUT     |


## Compatibility

Addon is evolving using different technologies:
| Version | python version | GPIO library | Works | Notes |
| :------ | :------------- | :----------- | :---: | :---- |
| 0.9.x   | 2.x            | RPi.GPIO     |   N   | Standard distributions of oldest Kodi (LE < 18) do not contain RPi-Tools; manual installation of GPIO library cause restart |
| 1.0.x   | 2.x            | RPi.GPIO     |   Y   | direct use of RPi.GPIO |
| 1.1.x   | 3.x            | RPi.GPIO     |   Y   | direct use of RPi.GPIO |
| 1.2.x   | 3.x            | gpiozero     |   Y   | gpiozero internally use RPi.GPIO in version 1.6.x (LE 11.x); from gpiozero 2.x (LE 12+) lgpio is used |

Aside some changes for RasPi Tool Addon, major change was [HW change in RasPi5 for GPIO chip](https://www.raspberrypi.com/news/rp1-the-silicon-controlling-raspberry-pi-5-i-o-designed-here-at-raspberry-pi/), that caused a major re-design for v. 1.2.0 related with adoption of [gpiozero](https://gpiozero.readthedocs.io/en/latest/) in place of [RPi.GPIO](https://sourceforge.net/projects/raspberry-gpio-python/)

This Addon was tested on following platforms:
|   Kodi version   | Distribution                                 |            HW             | Works | Version | Branch  | Notes |
| :--------------: | :------------------------------------------: | :-----------------------: | :---: | :-----: | :-----: | :---- |
| Kripton - 17.6   | LibreELEC-RPi2.arm-8.2.5                     | RasPi v1.2 model B+       |   N   |  0.9.x  |  -      | It seems that this addon cannot run on Kripton (tested on LE v17.6) because required Rpi-tool module (v8.2, to be manually installed) cause restart of RasPi when GPIO is activated |
| Leia - 18.9      | LibreELEC-RPi2.arm-9.2.6                     | RasPi v1.2 model B+       |   Y   |  1.0.x  |  leia   | Rpi-Tools is installed (based on RPi.GPIO) - use python 2.x |
| Matrix - 19.5    | LibreELEC-RPi4.arm-10.0.4                    | RasPi v4 model B with 4GB |   Y   |  1.1.x  |  matrix | Rpi-Tools is installed (based on RPi.GPIO) - use python 3.x |
| Nexus - 20.3     | LibreELEC-RPi4.arm-11.0.6                    | RasPi v4 model B with 4GB |   Y   |  1.2.x  |  nexus  | Rpi-Tools is installed (based on gpiozero and RPi.GPIO) - use python 3.x |
| Nexus - 20.3     | LibreELEC-RPi5.arm-11.0.6                    | RasPi v5 with 4GB         |   N   |  1.2.x  |  nexus  | GPIO is deprecated and gpiozero doesn't use gpiod (v 1.5.1), adapted for RPi5 |
| Omega - 21.alpha | LibreELEC-RPi5.aarch64-12.0-nightly-20240205 | RasPi v5 with 4GB         |   Y   |  1.2.x  |  nexus  | Rpi-Tools is installed (based on gpiozero and lgpio) - use python 3.x |


## Installation

Unless this addon was not included in a Kodi repository, must be installed manually.
To do so:
1. download this github repository as .zip (see [releases](https://github.com/Leo-C/kodi.addon.motiondetect/releases))
2. transfer file on host with Kodi (via network, USB memory, etc.)
3. in addon section choose "Install from .zip file" and browse file location
   (remember - if not asked - to enable installation of .zip addon from Settings -> Addon -> unknown source)


## Localization

If you want to add other localizations, you're welcome!
(send me `string.po` file and Addon description in addon.xml or do a Pull Request)


## Acknowledgments

The use of this Addon is free also for Business use.
But, if You use it in a Museum, please send me a photo of location and context!


## References

1. [HC-SR04 datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
2. [SRF05 datasheet](https://www.robot-electronics.co.uk/htm/srf05tech.htm)
3. [HY-SRF05 datasheet](https://datasheetspdf.com/pdf-down/H/Y/-/HY-SRF05-ETC.pdf)
4. [HC-SR501 datasheet](https://cdn-learn.adafruit.com/downloads/pdf/pir-passive-infrared-proximity-motion-sensor.pdf)
5. [HC-SR505 datasheet](https://robu.in/wp-content/uploads/2017/04/datasheet-1.pdf)
