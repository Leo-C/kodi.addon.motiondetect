import os
#import sys
import xbmcaddon


### add path to import GPIO library
### (already made by kodi because addon is declared as xbmc.python.module)
#rpi_tools_libs:str = os.path.join(xbmcaddon.Addon().getAddonInfo('path'), "..", "virtual.rpi-tools", "lib")
#sys.path.append(rpi_tools_libs)

# set current dir to a writable one for pipe file used by lgpio
os.chdir(xbmcaddon.Addon().getAddonInfo('path'))
