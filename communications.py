import events, tasks, services
import network, ubluetooth, ujson, uasyncio


class WLANService(tasks.Service):

    _current_WifiSvc = None
 
    def __init__(self):
        super().__init__("WLANService", 1, suspend_is_stop = False)
        self.requestQueue = []
        self.config_changed = False
        self.settings = []
        self.wifi = network.WLAN(network.STA_IF)
    
    def start(self):
        super().start()
        WLANService._current_WifiSvc = self
        with open('/wifi.json', 'r') as f:
            self.settings = ujson.load(f)
    
    def stop(self):
        super().stop()
        self.wifi.active(False)
        if self.config_changed:
            with open('/wifi.json', 'w') as f:
                ujson.dump(self.settings, f)
    
    def suspend(self):
        super().suspend()
        self.wifi.active(False)

    async def tryConnect(self, networkList):
        for thenetwork in networkList:
            print("trying to connect to " + str(thenetwork['essid']))
            self.wifi.connect(thenetwork['essid'], thenetwork['password'])
            status = self.wifi.status()
            while status == network.STAT_CONNECTING:
                await uasyncio.sleep_ms(100)
                status = self.wifi.status()
            if status == network.STAT_GOT_IP:
                print("connection succeeded")
                return True
            print("connection failed because " + str(status))
        return False
        
    async def process(self):
        super().process()
        if len(self.requestQueue) > 0:
            #machine.freq(240000000)
            services.OverlayProviderService._current_OverlayProviderService.enableOverlay("wifi")
            events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
            self.wifi.active(True)
            if await self.tryConnect(self.settings):
                while len(self.requestQueue) > 0:
                    (self.requestQueue.pop())(self.wifi)
                self.wifi.disconnect()
            self.wifi.active(False)
            print("done with wifi")
            services.OverlayProviderService._current_OverlayProviderService.disableOverlay("wifi")
            #machine.freq(80000000)
    
    """ callable must take one argument, the wlan object, and must be a async callable."""
    def queueRequest(self, callable):
        self.requestQueue.append(callable)
        
    @staticmethod
    def getWifiSvc():
        return WLANService._current_WifiSvc
    
    
class BLEService(tasks.Service):

    _current_BLESvc = None
 
    def __init__(self):
        super().__init__("BLEService", 1, suspend_is_stop = False)
        self.requestQueue = []
        self.config_changed = False
        self.settings = []
        self.BLE = ubluetooth.BLE
    
    def start(self):
        super().start()
        BLEService._current_BLESvc = self
        #with open('/bluetooth.json', 'r') as f:
        #    self.settings = ujson.load(f)
    
    def stop(self):
        super().stop()
        # uh ?
        #self.BLE.active(False)
        #if self.config_changed:
        #    with open('/bluetooth.json', 'w') as f:
        #        ujson.dump(self.settings, f)
    
    def suspend(self):
        super().suspend()
        # uh?
        #self.BLE.active(False)
        
    async def process(self):
        super().process()
        if len(self.requestQueue) > 0:
            #machine.freq(240000000)
            services.OverlayProviderService._current_OverlayProviderService.enableOverlay("BLE")
            events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
            self.BLE.active(True)
            while len(self.requestQueue) > 0:
                (self.requestQueue.pop())(self.BLE)
            self.BLE.active(False)
            print("done with BLE")
            services.OverlayProviderService._current_OverlayProviderService.disableOverlay("BLE")
            #machine.freq(80000000)
    
    def abort(self):
        return #do nothing becasue we cant actually interupt operations due to the magic of having no multithreading.
    
    """ callable must take one argument, the wlan object, and must be a async callable."""
    def queueRequest(self, callable):
        self.requestQueue.append(callable)
        
    @staticmethod
    def getBLESvc():
        return BLEService._current_BLESvc
