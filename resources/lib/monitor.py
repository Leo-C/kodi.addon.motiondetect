import xbmc
import xbmcaddon

from .settings import Settings
from .sensors import DistanceInteraction, PresenceInteraction


class EventMonitor(xbmc.Monitor):
    """
    This class monitor Settings change and implement Service loop
    """
    
    def __init__(self):
        self._settings = Settings()
        self._sensor = None
        self._pause_state:bool = None
        super().__init__(self)
        
        self._create_sensor()
        self._change_pause()
        
        xbmc.log("[service.media.motiondetect] EventMonitor started", xbmc.LOGINFO)
    
    def _del_sensor(self):
        if self._sensor != None:
            self._sensor.close()
            self._sensor = None
    
    def _create_sensor(self):
        self._del_sensor()
        settings = self._settings
        if settings.getSensorType() == Settings.SENSOR_ULTRASONIC:
            pins = settings.getPins()
            media = settings.getMediaPaths()
            thresholds = settings.getThreshDistances()
            stop_time = settings.getStopTime()
            self._sensor = DistanceInteraction(pins[1], pins[0], thresholds[0], thresholds[1], media[0], media[1], stop_time)
        elif settings.getSensorType() == Settings.SENSOR_PIR:
            pins = settings.getPins()
            media = settings.getMediaPaths()
            self._sensor = PresenceInteraction(pins[1], media[0], media[1])
        else:
            raise ValueError("Unknown Sensor Type")
    
    def _change_pause(self):
        paused:bool = self._settings.is_paused()
        if self._sensor != None:
            self._sensor.pause(paused)
    
    def onSettingsChanged(self):
        xbmc.log("[service.media.motiondetect] Settings changed", xbmc.LOGDEBUG)
        settings = Settings()
        if settings != self._settings:
            xbmc.log("[service.media.motiondetect] Settings Changed", xbmc.LOGINFO)
            self._settings = settings # store actual settings
            self._create_sensor()
        
        self._change_pause()
    
    def onNotification(self, sender, method, data):
        if method == "System.OnQuit" or method == "System.OnRestart":
            xbmc.log("[service.media.motiondetect] Destroy Sensor", xbmc.LOGINFO)
            self._del_sensor()
        elif method == "System.OnSleep" or method == "GUI.OnScreensaverActivated":
            xbmc.log("[service.media.motiondetect] Pause Sensor", xbmc.LOGINFO)
            if self._sensor == None:
                self._pause_state = None
            else:
                self._pause_state = self._sensor.paused()
                self._sensor.pause(True)
        elif method == "System.OnWake" or method == "GUI.OnScreensaverDeactivated":
            xbmc.log("[service.media.motiondetect] Reactivate Sensor", xbmc.LOGINFO)
            if self._sensor != None and self._pause_state != None:
                self._sensor.pause(self._pause_state)
    
    def loop(self):
        while not self.waitForAbort(1.0):
            if self._sensor != None:
                self._sensor.handle_sensing()
        
        xbmc.log("[service.media.motiondetect] Stop Requested", xbmc.LOGINFO)
        self._del_sensor()
