import sys
import xbmc
import xbmcaddon
from os.path import join

# import GPIO library
rpi_tools_libs = join(xbmcaddon.Addon().getAddonInfo('path'), "..", "virtual.rpi-tools", "lib")
sys.path.append(rpi_tools_libs)
from resources.lib.GPIOhnd import GPIOSensor, DistanceInteraction, PresenceInteraction


# get all Settings
this_addon = xbmcaddon.Addon()
sensor_type:int = int(this_addon.getSetting("sensor_type"))
pin_trigger:int = -1
if sensor_type == 0: # Ultrasonic
    pin_trigger = int(this_addon.getSetting("pin_trigger"))
pin_sensor:int = int(this_addon.getSetting("pin_sensor"))
play_dist:int = int(this_addon.getSetting("play_dist"))
stop_dist:int = int(this_addon.getSetting("stop_dist"))
stop_dist = max(play_dist, stop_dist) #to ensure that stop_dist >= play_dist
stop_time:int = int(this_addon.getSetting("stop_time"))
idle_media_blank:str =this_addon.getSetting("idle_media_blank")
idle_media_filepath:str = "" # blank screen
if idle_media_blank == "false":
    idle_media_filepath = this_addon.getSetting("idle_media")
video_filepath:str = this_addon.getSetting("media")

# init GPIO pins for sensor
GPIOSensor.init(pin_sensor, pin_trigger)

#choose correct interaction (depends on sensor)
interaction = None
if sensor_type == 0: #ultrasonic sensor
    interaction = DistanceInteraction(play_dist, stop_dist, idle_media_filepath, video_filepath, stop_time)
elif sensor_type == 1: #PIR sensor
    interaction = PresenceInteraction(idle_media_filepath, video_filepath)

if interaction != None:
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        xbmc.log("[script.media.motiondetect] Starting Test", xbmc.LOGDEBUG)
        interaction.test()
    else:
        xbmc.log("[script.media.motiondetect] Starting Addon", xbmc.LOGDEBUG)
        interaction.run()
