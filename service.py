import sys
import xbmc
from resources.lib.monitor import EventMonitor


def stop_lgpio_thread():
    import lgpio #deferred loading
    lgpio._notify_thread.stop() #set stop flag
    lgpio._notify_close(lgpio._notify_thread._notify) #close handle with lgpio shlib
    lgpio._notify_thread._file.close() #unlock read file in loop


if __name__ == "__main__":
    xbmc.log("[service.media.motiondetect] Service Starting", xbmc.LOGINFO)
    monitor = EventMonitor()
    monitor.loop()
    xbmc.log("[service.media.motiondetect] Service Stopped", xbmc.LOGINFO)
    
    # workaround to stop thread that read data from lgpio library
    if "_lgpio" in sys.modules:
        stop_lgpio_thread()
