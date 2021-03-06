import tasks, events, communications, interface, profiling
import machine, utime, struct, ntptime, ujson


class PowerService(tasks.Service):
    _sleep_time = 10
    """we use utime because it pauses when we sleep"""
    def __init__(self):
        super().__init__("PowerService", 4)
        self.last_dog = utime.time()
        self.shouldsleep = False
    
    def start(self):
        super().start()
    
    def process(self):
        super().process()
        if self.last_dog + self._sleep_time < utime.time():
            self.shouldsleep = True
        else:
            self.shouldsleep = False
      
    def watchdog(self, event):
        self.last_dog = utime.time()
        self.shouldsleep = False
    
    def shouldSleep(self):
        return self.shouldsleep
    
    def reset(self):
        self.last_dog = utime.time()
        self.shouldsleep = False

class BatteryService(tasks.Service):
    _current_BatteryService = None
    def __init__(self, pmu):
        super().__init__("BatteryService", 1)
        self.pmu = pmu
        self.percentage = 100

    def start(self):
        super().start()
        BatteryService._current_BatteryService = self

    def process(self):
        super().process()
        if self.percentage != self.pmu.getBattPercentage():
            events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
            self.percentage = self.pmu.getBattPercentage()
        if self.percentage > 100:
            # BAD
            print("BATTERY VALUE BAD REBOOTING PMU")
            #self.pmu.shutdown()
        
    
    def getBatteryPercentage(self): #returns bad stuffs?
        return str(self.percentage)
    
    def getBatteryVoltage(self): #doesnt return bad stuffs
        return str("%.2f" % (self.pmu.getBattVoltage() / 1000))
        

class OverlayProviderService(tasks.Service, interface.Interface):
    _current_OverlayProviderService = None
    def __init__(self, graphics):
        tasks.Service.__init__(self, "OverlayProviderService", 1)
        interface.Interface.__init__(self, graphics)
        self.overlayElement = {}

    def start(self):
        tasks.Service.start(self)
        OverlayProviderService._current_OverlayProviderService = self

    def process(self):
        super().process()
        
    
    def addOverlayElement(self, overlayID, element):
        if not overlayID in self.overlayElement:
            self.overlayElement[overlayID] = []
        self.overlayElement[overlayID].append(element)
    
    def enableOverlay(self, overlayID):
        for element in self.overlayElement[overlayID]:
            self.addElement(element)
        
    def disableOverlay(self, overlayID):
        for element in self.overlayElement[overlayID]:
            self.removeElement(element)
    
    def interjectInterface(self, interfacer):
        interfacer.addInterjectionInterface(self)
    
    def uninterjectInterface(self, interfacer):
        interfacer.removeInterjectionInterface(self)

class SettingsProviderService(tasks.Service):

    _current_SettingProviderSvc = None

    def __init__(self):
        super().__init__("SettingsProviderService", 0, suspend_is_stop = False)
        self.settings = {}
        self.changed = False

    def start(self):
        super().start()
        SettingsProviderService._current_SettingProviderSvc = self
        with open('/settings.json', 'r') as f:
            self.settings = ujson.load(f)
    
    def stop(self):
        super().stop()
        if self.changed:
            with open('/settings.json', 'w') as f:
                ujson.dump(self.settings, f)

    @staticmethod
    def get(key):
        if key in SettingsProviderService._current_SettingProviderSvc.settings:
            return SettingsProviderService._current_SettingProviderSvc.settings[key]
        return None

    @staticmethod
    def set(key, value):
        SettingsProviderService._current_SettingProviderSvc.settings["key"] = value
        SettingsProviderService._current_SettingProviderSvc.changed = True
        
class SettingsService(tasks.Service):

    _current_SettingsSvc = None
    maxBrightnessVoltage = 3300
    minBrightnessVoltage = 2500
    BrightnessSteps = 8
    
    
    def __init__(self, pmu):
        super().__init__("SettingsService", 4)
        self.brightness = 5
        self.pmu = pmu
    
    def start(self):
        super().start()
        SettingsService._current_SettingsSvc = self
        self.brightness = SettingsProviderService.get("Brightness")
        if self.brightness is None:
            self.setBrightness(5)
        else:
            self.setsetBrightness()
        
    def stop(self):
        super().stop()
    
    def process(self):
        pass
      
    def setsetBrightness(self):
        self.pmu.setLDO2Voltage(SettingsService.minBrightnessVoltage + ((SettingsService.maxBrightnessVoltage - SettingsService.minBrightnessVoltage) / SettingsService.BrightnessSteps) * self.brightness)
      
    def setBrightness(self, value):
        if value < 0:
            value = 0
        if value > SettingsService.BrightnessSteps - 1:
            value = SettingsService.BrightnessSteps - 1
        self.brightness = value
        SettingsProviderService.set("Brightness", self.brightness)
        self.setsetBrightness()
    
    def getBrightness(self):
        return self.brightness
   


""" THIS IS FOR THE ESP32 RTC, WE DONT USE THE PCF YET.
apparently it's really shit at keeping time tho"""
class TimeService(tasks.Service):

    _current_TimeSvc = None

    def __init__(self):
        super().__init__("TimeService", 0, suspend_is_stop = False)
        self.rtc = None
        self.synced = False
        self.syncing = False
        self.lastsynced = 0
        self.currentDate = None

    def start(self):
        super().start()
        self.rtc = machine.RTC()
        TimeService._current_TimeSvc = self
        year, month, day, weekday, hour, minute, second = struct.unpack("HBBBBBB", self.readRtcData(0, struct.calcsize("HBBBBBB")))
        self.rtc.init((year, month, day, weekday, hour, minute, second, 0))
        self.currentDate = self.rtc.datetime()
        
    def stop(self):
        super().stop()
        self.writeRtcData(0, struct.pack("HBBBBBB", self.currentDate[0], self.currentDate[1], self.currentDate[2], self.currentDate[3], self.currentDate[4], self.currentDate[5], self.currentDate[6]))
        
    
    """ data is bytes encoded"""
    def writeRtcData(self, offset, data):
        if self.rtc.memory() == b'':
            tow = bytearray(offset)
            tow = tow + data
            self.rtc.memory(tow)
        else:
            previous = bytearray(self.rtc.memory())
            previous[offset : offset+len(data)] = data
    
    def readRtcData(self, offset, length):
        mem = self.rtc.memory()
        if mem == b'':
            return bytearray(length)
        return mem[offset : offset+length]

    def process(self):
        super().process()
        if self.synced == False and self.syncing == False:
            communications.WLANService.getWifiSvc().queueRequest(self.wifiSetTimeCallBack)
            self.syncing = True
        self.currentDate = self.rtc.datetime()
        events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
        
    def getHours(self):
        return str(self.currentDate[4])
    
    def getMinutes(self):
        return str(self.currentDate[5])
        
    def getSeconds(self):
        return str(self.currentDate[6])
        
    def wifiSetTimeCallBack(self, wifi):
        ntptimeepoch = ntptime.time()
        print("epoch time: " + str(ntptimeepoch))
        year, month, monthday, hour, minute, second, weekday, yearday = utime.gmtime(ntptimeepoch)
        self.rtc.datetime((year, month, monthday, weekday, hour + SettingsProviderService.get("TimeZone"), minute, second, 0))
        self.currentDate = self.rtc.datetime()
        self.writeRtcData(0, struct.pack("HBBBBBB", self.currentDate[0], self.currentDate[1], self.currentDate[2], self.currentDate[3], self.currentDate[4], self.currentDate[5], self.currentDate[6]))
        events.EventHandler._current_EventHandler.trigger_event(events.EventType.CLOCK_RESET)
        self.synced = True
        self.syncing = False
        
    #@staticmethod
    #def getTimeSvc():
    #    return TimeService._current_TimeSvc


class TestService(tasks.Service):
    def __init__(self):
        super().__init__("TestService", 10)
        self.cycle_hold = 0
    
    def buzz(self, event):
        if event.type == events.EventType.TOUCH_HOLD:
            self.cycle_hold += 1
            if self.cycle_hold > 5:
                buzz = machine.Pin(4, machine.Pin.OUT)
                buzz.on()
                await utime.sleep_ms(50)
                buzz.off()
                self.cycle_hold = 0
        if event.type == events.EventType.TOUCH_RELEASE:
            self.cycle_hold = 0
    
    def process(self):
        super().process()
        print("every 10 seconds in africa, a 6th of a minute passes")


class AppService(tasks.Service):
    
    _current_AppSvc = None

    def __init__(self, graphics):
        super().__init__("AppService", 0, suspend_is_stop = False)
        self.appslist = []
        self.graphics = graphics
    
    def startApp(self, name):
        app = __import__("apps_" + name, globals(), locals(), ['*'], 0)
        app.start(self.graphics)
        self.appslist.append(app)
        print("started: " + str(app))
        return app
        
    def stopLastApp(self):
        self.appslist[-1].stop()
        stopped = self.appslist.pop()
        print("stopped: " + str(stopped))
    
    def start(self):
        super().start()
        AppService._current_AppSvc = self
        self.startApp("main")
        
    def stop(self):
        super().stop()
        while len(self.appslist) > 0:
            self.stopLastApp()
            
    def event(self, event):
        if event.type == events.EventType.BUTTON:
            if len(self.appslist) > 1:
                self.stopLastApp()
        elif event.type == events.EventType.GRAPHIC_UPDATE:
            self.appslist[-1].update()
        else:
            self.appslist[-1].event(event)
        
        
    def suspend(self):
        """ do something before sleeping
        derived must call parent's"""
        

    def unsuspend(self):
        """ do something after sleeping
        derived must call parent's"""
    def process(self):
        if len(self.appslist) < 1:
            raise RuntimeError("Bad AppHandler Status")
        if self.appslist[-1].process() != 0:
            self.stopLastApp()
        return None
