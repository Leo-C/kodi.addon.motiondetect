import time
import xbmc
import xbmcgui
import xbmcaddon
from gpiozero import DistanceSensor, MotionSensor


class MotionPlayer(xbmc.Player):
    """
    Subclass of xbmc.Player customized to play an Idle Media and a Media when sensor triggers
    """
    STOPPED = 0
    PLAYING_IDLE = 1
    PLAYING_MEDIA = 2
    WAITING_STOP = 3
    
    
    def init(self, idle_media:str, media:str, stop_time:int = 0): # weird error if constructor is redefined
        """
        :param idle_media: path of media reproduced when system is idle
        :type idle_media: str
        :param media: path of media reproduced when system is triggered
        :type media: str
        :param stop_time: is time before stop media in seconds (default 0)
        :type stop_time: int
        """
        self._idle = idle_media
        self._media:str = media
        self.stop_time = stop_time
        self._start_countdown:float = 0.0
        self._countdown:bool = False
        self._repeat:bool = False
        self._setState(MotionPlayer.STOPPED)
    
    def setRepeat(self, on:bool):
        self._repeat = on
    
    def playIdleScreen(self):
        xbmc.log(f"[service.media.motiondetect] Starting Idle Media '{self._idle}'", xbmc.LOGDEBUG)
        self._countdown = False
        self.play(self._idle)
        xbmc.executebuiltin("PlayerControl(RepeatAll)")
        self._setState(MotionPlayer.PLAYING_IDLE)
        while True: # wait media start
            if self.isPlaying():
                break
            else:
                xbmc.sleep(500)
    
    def playMedia(self):
        if self._media == "": # otherwise ignore
            msg = xbmcaddon.Addon().getLocalizedString(32702)
            xbmcgui.Dialog().notification("", msg, xbmcgui.NOTIFICATION_WARNING, 5000)
            return
        
        xbmc.log(f"[service.media.motiondetect] Starting Media '{self._media}'", xbmc.LOGDEBUG)
        self._countdown = False
        if not self._repeat:
            xbmc.executebuiltin("PlayerControl(RepeatOff)")
        self.play(self._media)
        if self._repeat:
            xbmc.executebuiltin("PlayerControl(RepeatAll)")
        self._setState(MotionPlayer.PLAYING_MEDIA)
        while True: # wait media start
            if self.isPlaying():
                break
            else:
                xbmc.sleep(500)
    
    def notifyIdle(self):
        xbmc.log("[service.media.motiondetect] Notifying stop", xbmc.LOGDEBUG)
        if (self.getState() == MotionPlayer.PLAYING_MEDIA) and (not self._countdown):
            self._start_countdown = time.time()
            self._countdown = True
        
        time_left = self.stop_time - int(time.time() - self._start_countdown)
        if time_left > 0:
            msg = xbmcaddon.Addon().getLocalizedString(32701)
            xbmcgui.Dialog().notification("", msg % time_left, icon=xbmcgui.NOTIFICATION_INFO)
            xbmc.sleep(500)
        else:
            self.playIdleScreen()
    
    def stop(self):
        self._setState(MotionPlayer.STOPPED)
        self._countdown = False
        #workaround because stop() method hang when Service is disabled
        #super().stop()
        xbmc.executebuiltin("PlayerControl(Stop)")
    
    def cancelIdle(self):
        self._countdown = False
    
    def onPlayBackEnded(self):
        if ((self.getState() == MotionPlayer.PLAYING_MEDIA) and not self._repeat) or (self.getState() == MotionPlayer.WAITING_STOP):
            self.playIdleScreen() #anyway, if Media or Idle Screen is finished, restart Idle Media with no countdown
        else:
            self._setState(MotionPlayer.STOPPED)
    
    def onPlayBackError(self):
        if self.getState() != MotionPlayer.STOPPED:
            self.playIdleScreen()
    
    def _setState(self, state):
        self._state = state
    
    def getState(self):
        if self._state == MotionPlayer.PLAYING_MEDIA and self._countdown:
            return MotionPlayer.WAITING_STOP
        else:
            return self._state


class Interaction:
    """
    Base class for Sensor, with common methods
    """
    
    WINDOW_DIALOG_ADDON_SETTINGS:int = 10140
    
    def __init__(self):
        self._player = MotionPlayer()
        self._paused:bool = True
    
    def pause(self, state:bool = True) -> None:
        if state != self._paused: # act only if pause state is changed
            if state:
                self._player.stop()
            else:
                self._player.playIdleScreen()
            
            self._paused = state
    
    def paused(self) -> bool:
        return self._paused
    
    def isSettingsDialogOpen(self) -> bool:
        return xbmc.getCondVisibility(f"Window.IsVisible({Interaction.WINDOW_DIALOG_ADDON_SETTINGS})")

class DistanceInteraction(Interaction):
    """
    handle Sensor that measure distance, with 2 thresholds (and hysteresis) to start / stop video
    """
    # maximum distance (cm)
    MAX_DISTANCE = 400
    
    def __init__(self, pin_sensor:int, pin_trigger:int, start_threshold:float, stop_threshold:float, idle_screen:str, media:str, stop_time:int = 0):
        """
        :param pin_sensor: BCM pin of sensing (IN)
        :type pin_sensor: int
        :param pin_trigger: BCM pin of trigger (OUT)
        :type pin_trigger: int
        :param start_threshold: is minimum distance (in cm) to start media
        :type start_threshold: float
        :param stop_threshold: is maximum distance (in cm) to stop media
        :type stop_threshold: float
        :param idle_screen: is filepath for idle screen (image, video)
        :type idle_screen: str
        :param media: is filepath for video to play
        :type media: str
        :param stop_time: is time before stop media in seconds (default 0)
        :type stop_time: int
        """
        super().__init__()
        
        self.th_start:float = start_threshold
        self.th_stop:float = stop_threshold
        self._paused = True
        
        # init player
        self._player.init(idle_screen, media, stop_time)
        self._player.setRepeat(False)
        
        # init sensor
        self._sensor = DistanceSensor(pin_sensor, pin_trigger, max_distance=DistanceInteraction.MAX_DISTANCE / 100)
    
    def handle_sensing(self) -> None:
        distance:int = int(self._sensor.distance * 100)
        xbmc.log(f"[service.media.motiondetect] Distance = {distance} cm", xbmc.LOGDEBUG)
        if not self._paused:
            state:bool = self._player.getState()
            if state == MotionPlayer.PLAYING_IDLE:
                if distance > 0 and distance < self.th_start:
                    self._player.playMedia()
            elif state == MotionPlayer.PLAYING_MEDIA:
                if self.th_stop > 0 and distance > self.th_stop:
                    self._player.notifyIdle()
            elif state == MotionPlayer.WAITING_STOP:
                if distance > 0 and distance < self.th_start:
                    self._player.cancelIdle()
                else:
                    self._player.notifyIdle()
        
        if self.isSettingsDialogOpen():
            # update value in Settings panel
            perc:int = int(min(distance / DistanceInteraction.MAX_DISTANCE, 1) * 100)
            xbmcaddon.Addon().setSettingInt("distance", distance)
            xbmcaddon.Addon().setSettingInt("percentage", perc)
    
    def close(self):
        self._player.stop()
        self._sensor.close()

class PresenceInteraction(Interaction):
    """
    it reacts to trigger of sensor activation, then start media, and wait for finish
    """
    def __init__(self, pin_sensor:int, idle_screen:str, media:str):
        """
        :param pin_sensor: BCM pin of sensing (IN)
        :type pin_sensor: int
        :param idle_screen: is filepath for idle screen (image, media)
        :type idle_screen: str
        :param media: is filepath for video to play
        :type media: str
        """
        super().__init__()
        
        # init player
        self._player = MotionPlayer()
        self._player.init(idle_screen, media)
        self._player.setRepeat(False)
        
        # init sensor
        self._sensor = MotionSensor(pin_sensor)
    
    def handle_sensing(self) -> None:
        motion:bool = self._sensor.motion_detected
        xbmc.log(f"[service.media.motiondetect] Motion = {motion}", xbmc.LOGDEBUG)
        if not self._paused:
            state:bool = self._player.getState()
            if state == MotionPlayer.PLAYING_IDLE:
                if motion:
                    self._player.playMedia()
        
        if self.isSettingsDialogOpen():
            # update value in Settings panel
            perc:int = 0
            if motion:
                perc = 100
            xbmcaddon.Addon().setSettingInt("distance", 0)
            xbmcaddon.Addon().setSettingInt("percentage", perc)
    
    def close(self):
        self._player.stop()
        self._sensor.close()
