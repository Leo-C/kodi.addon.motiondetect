from os.path import join
import xbmcaddon


class Settings:
    """
    Represent Settings of Addon
    
    Has methods to check if Settings are changed
    """
    
    SENSOR_ULTRASONIC:int = 0
    SENSOR_PIR:int = 1
    
    def __init__(self):
        self.this_addon = xbmcaddon.Addon()
        self._sensor_type:int = int(self.this_addon.getSetting("sensor_type")) #0: Ultrasonic; 1: PIR
        self._pin_trigger = int(self.this_addon.getSetting("pin_trigger"))
        self._pin_sensor = int(self.this_addon.getSetting("pin_sensor"))
        self._play_dist:int = int(self.this_addon.getSetting("play_dist"))
        stop_dist:int = int(self.this_addon.getSetting("stop_dist"))
        self._stop_dist:int = max(self._play_dist, stop_dist) #to ensure that stop_dist >= play_dist
        self._stop_time:int = int(self.this_addon.getSetting("stop_time"))
        self._idle_media_blank:bool = (self.this_addon.getSetting("idle_media_blank") == "true")
        path_addon = self.this_addon.getAddonInfo('path')
        self._idle_media_filepath:str = join(path_addon, "resources", "black.mp4")
        if not self._idle_media_blank:
            self._idle_media_filepath:str = self.this_addon.getSetting("idle_media")
        self._video_filepath:str = self.this_addon.getSetting("media")
    
    def getSensorType(self) -> int:
        """ 0: Ultrasonic; 1: PIR """
        return self._sensor_type
    
    def getPins(self) -> [int,int]:
        """ (pin_trigger:int, pin_sensor:int) """
        return (self._pin_trigger, self._pin_sensor)
    
    def getThreshDistances(self) -> [float,float]:
        """ (start_distance:float, stop_distance:float) """
        return (self._play_dist, self._stop_dist)
    
    def getStopTime(self) -> int:
        return self._stop_time
    
    def getMediaPaths(self) -> [str,str]:
        """ (idle_media:str, media:str) """
        return (self._idle_media_filepath, self._video_filepath)
    
    def is_paused(self) -> bool:
        return (self.this_addon.getSetting("pause") == "true")
    
    def __eq__(self, other) -> bool:
        """
        Check if actual configuration is changed respect to stored data
        """
        if other == None:
            return False
        
        assert type(other) == Settings
        
        if self.getSensorType() != other.getSensorType():
            return False
        
        equal:bool = True
        if self.getSensorType() == Settings.SENSOR_ULTRASONIC:
            equal = equal and (self.getPins() == other.getPins())
            equal = equal and (self.getThreshDistances() == other.getThreshDistances())
            equal = equal and (self.getMediaPaths() == other.getMediaPaths())
        elif self.getSensorType() == Settings.SENSOR_PIR:
            equal = equal and (self.getPins()[1] == other.getPins()[1])
            equal = equal and (self.getMediaPaths() == other.getMediaPaths())
        else:
            return False
        #note that pause is not checked
        
        return equal
