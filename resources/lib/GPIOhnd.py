import sys
import time
from os.path import join
import xbmc
import xbmcgui
import xbmcaddon
import RPi.GPIO as GPIO


class GPIOSensor:
    #read cycle time (msec)
    READ_CYCLE = 60
    
    #set GPIO pins
    PIN_SIGNAL = 23
    PIN_SENSOR = 24
    
    #last read time (used 
    LastReadTime = 0.0
    
    @staticmethod
    def init(PIN_SENSOR = 24, PIN_SIGNAL = 23):
        """ init Sensor PINs and class variables """
        
        #GPIO Mode (BOARD / BCM)
        GPIO.setmode(GPIO.BCM)
        
        GPIOSensor.PIN_SIGNAL = PIN_SIGNAL
        GPIOSensor.PIN_SENSOR = PIN_SENSOR
        
        #set GPIO direction (IN / OUT)
        if GPIOSensor.PIN_SIGNAL >= 0:
            GPIO.setup(GPIOSensor.PIN_SIGNAL, GPIO.OUT)
        GPIO.setup(GPIOSensor.PIN_SENSOR, GPIO.IN)
    
    @staticmethod
    def getSRF04distance():
        """
        return SRF-04 sensor in centimeters
        it ensure that a minimum time passes between consecutive calls (to avoid echo signals)
        """
        
        #wait between consecutive reads
        GPIOSensor.setLevel(False)
        read_interval = time.time() - GPIOSensor.LastReadTime
        if read_interval < (GPIOSensor.READ_CYCLE * 0.001):
            time.sleep((GPIOSensor.READ_CYCLE * 0.001) - read_interval)
        
        # set Trigger to HIGH
        GPIOSensor.setLevel(True)
        
        # after 0.01ms set Trigger to LOW
        time.sleep(0.00001)
        GPIOSensor.setLevel(False)
        
        # save StartTime
        res = GPIOSensor.waitLevel(GPIO.RISING, 20)
        StartTime = time.time()
        if not res:
            GPIOSensor.LastReadTime = StartTime
            return -1; #if timeout
        
        # save time of arrival
        res = GPIOSensor.waitLevel(GPIO.FALLING, 40) # no response in 36 msec if object is too far
        StopTime = time.time()
        GPIOSensor.LastReadTime = StopTime
        if not res:
            return -1; #if timeout
        
        # time difference between start and arrival
        TimeElapsed = StopTime - StartTime
        
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because sensor measure round-trip time
        distance = round((TimeElapsed * 34300) / 2, 1)
        
        if distance < 2 or distance > 400:
            return -1 # out of range (valid range: 2-400 cm)
        else:
            return distance
    
    @staticmethod
    def setLevel(level):
        """
        set specified level for sensor signal
        """
        
        if GPIOSensor.PIN_SIGNAL >= 0:
            GPIO.output(GPIOSensor.PIN_SIGNAL, level)
    
    @staticmethod
    def checkLevel(level=GPIO.HIGH):
        """
        check level of sensor against that specified
        """
        
        return (GPIO.input(GPIOSensor.PIN_SENSOR) == level)
    
    @staticmethod
    def waitLevel(direction=GPIO.RISING, timeout = 0):
        """
        wait transition to specified level
        if timeout is specified (in msec) wait; if timeout occurs return False
        """
        channel = None
        try:
            if timeout > 0:
                channel = GPIO.wait_for_edge(GPIOSensor.PIN_SENSOR, direction, timeout=timeout)
            else:
                channel = GPIO.wait_for_edge(GPIOSensor.PIN_SENSOR, direction)
        except RuntimeError: #sometimes wait_for_edge() fail
            pass
        
        return (channel != None)

class MotionPlayer(xbmc.Player):
    """
    Subclass of xbmc.Player customized to play an Idle Media and a Media when sensor triggers
    """
    STOPPED = 0
    PLAYING_IDLE = 1
    PLAYING_MEDIA = 2
    WAITING_STOP = 3
    
    STOP_TIME = 0
    
    
    def init(self, idle_media, media, stop_time = 0): # weird error if constructor is redefined
        self.STOP_TIME = stop_time
        self._start_countdown = 0
        self._countdown = False
        self._repeat = False
        
        if idle_media != "":
            self._idle = idle_media
        else:
            path_addon = xbmcaddon.Addon().getAddonInfo('path')
            self._idle = join(path_addon, "resources", "black.mp4")
        self._media = media
        
        self._setState(MotionPlayer.STOPPED)
        #self.playIdleScreen()
    
    def setRepeat(self, on):
        self._repeat = on
    
    def playIdleScreen(self):
        xbmc.log("[script.media.motiondetect] Starting Idle Media '%s'" % self._idle, xbmc.LOGINFO)
        self._countdown = False
        self.play(self._idle)
        xbmc.executebuiltin("PlayerControl(RepeatAll)")
        self._setState(MotionPlayer.PLAYING_IDLE)
        while True: # wait media start
            xbmc.log("[script.media.motiondetect] TP10", xbmc.LOGDEBUG)
            if self.isPlaying():
                break
            else:
                xbmc.sleep(500)
    
    def playMedia(self):
        if self._media == "": # otherwise ignore
            msg = xbmcaddon.Addon().getLocalizedString(32702)
            xbmcgui.Dialog().notification("", msg, xbmcgui.NOTIFICATION_WARNING, 5000)
            return
        
        xbmc.log("[script.media.motiondetect] Starting Media '%s'" % self._media, xbmc.LOGINFO)
        self._countdown = False
        if not self._repeat:
            xbmc.executebuiltin("PlayerControl(RepeatOff)")
        self.play(self._media)
        if self._repeat:
            xbmc.executebuiltin("PlayerControl(RepeatAll)")
        self._setState(MotionPlayer.PLAYING_MEDIA)
        while True: # wait media start
            xbmc.log("[script.media.motiondetect] TP11", xbmc.LOGDEBUG)
            if self.isPlaying():
                break
            else:
                xbmc.sleep(500)
    
    def notifyIdle(self):
        xbmc.log("[script.media.motiondetect] Notifying stop", xbmc.LOGINFO)
        if (self.getState() == MotionPlayer.PLAYING_MEDIA) and (not self._countdown):
            self._start_countdown = time.time()
            self._countdown = True
        
        time_left = self.STOP_TIME - int(time.time() - self._start_countdown)
        if time_left > 0:
            msg = xbmcaddon.Addon().getLocalizedString(32701)
            xbmcgui.Dialog().notification("", msg % time_left, icon=xbmcgui.NOTIFICATION_INFO)
            #xbmc.executebuiltin('Notification("", "Stop in %s seconds", 0)' % str(time_left))
            xbmc.sleep(500)
        else:
            self.playIdleScreen()
    
    def stop(self):
        self._setState(MotionPlayer.STOPPED)
        super().stop()
    
    def cancelIdle(self):
        self._countdown = False
    
    def onPlayBackEnded(self):
        if ((self.getState() == MotionPlayer.PLAYING_MEDIA) and not self._repeat) or (self-getState() == MotionPlayer.WAITING_STOP):
            self.playIdleScreen() #anyway, if Media or Idle Screen is finished, restart Idle Media with no countdown
    
    def onPlayBackError(self):
        self.playIdleScreen()
    
    def _setState(self, state):
        self._state = state
    
    def getState(self):
        if self._state == MotionPlayer.PLAYING_MEDIA and self._countdown:
            return MotionPlayer.WAITING_STOP
        else:
            return self._state


class DistanceInteraction:
    """
    handle Sensor that measure distance, with 2 thresholds (and hysteresis) to start / stop video
    """
    def __init__(self, start_threshold, stop_threshold, idle_screen, media, stop_time = 0):
        """
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
        self.TH_START = start_threshold
        self.TH_STOP = stop_threshold
        self._player = MotionPlayer()
        self._player.init(idle_screen, media, stop_time)
        self._player.setRepeat(True)
    
    def run(self):
        self._player.playIdleScreen()
        while True:
            distance = GPIOSensor.getSRF04distance()
            xbmc.log("[script.media.motiondetect] Distance = %d cm" % distance, xbmc.LOGDEBUG)
            state = self._player.getState()
            if state == MotionPlayer.PLAYING_IDLE:
                if distance > 0 and distance < self.TH_START:
                    self._player.playMedia()
            elif state == MotionPlayer.PLAYING_MEDIA:
                if distance > self.TH_STOP:
                    self._player.notifyIdle()
            elif state == MotionPlayer.WAITING_STOP:
                if distance > 0 and distance < self.TH_START:
                    self._player.cancelIdle()
                else:
                    self._player.notifyIdle()
            
            xbmc.sleep(500)
    
    def test(self):
        dialog = xbmcgui.DialogProgress()
        dialog.create("Motion")
        while True:
            if dialog.iscanceled():
                dialog.close()
                del dialog
                break
            
            distance = GPIOSensor.getSRF04distance()
            if (distance > 0):
                msg = xbmcaddon.Addon().getLocalizedString(32703)
                dialog.update(min(int(distance / 4.00), 100), msg % int(distance)) # max 400 cm
            
            xbmc.sleep(1000)

class PresenceInteraction:
    """
    it reacts to trigger of sensor activation, then start media, and wait for finish
    """
    LEVEL = GPIO.HIGH
    
    def __init__(self, idle_screen, media):
        """
        :param idle_screen: is filepath for idle screen (image, media)
        :type idle_screen: str
        :param media: is filepath for video to play
        :type video: str
        """
        self._player = MotionPlayer()
        self._player.init(idle_screen, media)
        self._player.setRepeat(False)
    
    def run(self):
        self._player.playIdleScreen()
        while True:
            state = self._player.getState()
            if state == MotionPlayer.PLAYING_IDLE:
                sensor = GPIOSensor.checkLevel(level = PresenceInteraction.LEVEL)
                if sensor:
                    self._player.playMedia()
            
            xbmc.sleep(1000)
    
    def test(self):
        dialog = xbmcgui.DialogProgress()
        dialog.create("Motion")
        while True:
            if dialog.iscanceled():
                dialog.close()
                del dialog
                break
            
            sensor = GPIOSensor.checkLevel(level = PresenceInteraction.LEVEL)
            if sensor:
                msg = xbmcaddon.Addon().getLocalizedString(32704)
                dialog.update(100, msg)
            else:
                msg = xbmcaddon.Addon().getLocalizedString(32705)
                dialog.update(0, msg)
            
            xbmc.sleep(1000)
