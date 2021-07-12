import tasks, events, interface, communications, services
import utime, machine, micropython, usys, uio
import axp202, constants_axp202, st7789, pcf8563, esp32, esp

"""Important:
ESP32 RTC memory usage (python 'struct' format):
starts at index 0
section 1 for esp32 rtc: HBBBBB
year, month, day, weekday, hour, minute, second
7 bytes



Timer 0 reserved for main loop
"""

""" deepsleep after ... ms"""
_deepsleepTime = 1800000 # half a hour
#_deepsleepTime = 5000
_mainPeriod = 300

class Main:
    _main = None

    def __init__(self):
        # Init Power Management Unit
        self.pmu = None
        self.display = None
        self.tm = None
        self.serviceHandler = None
        self.eventHandler = None
        self.graphics = None
        self.powerSvc = None
        self.mainTimer = None
        self.overlaySvc = None
        self.settingsSvc = None
        self.appSvc = None
    
    def start_display(self):
        display_spi = machine.SPI(1,baudrate=32000000,sck=machine.Pin(18, machine.Pin.OUT),mosi=machine.Pin(19, machine.Pin.OUT))
        #self.display = st7789.ST7789(screen_spi,240,240,cs=machine.Pin(5, machine.Pin.OUT),dc=machine.Pin(27, machine.Pin.OUT),backlight=machine.Pin(12, machine.Pin.OUT),rotation=2,buffer_size=16*32*2)
        # not very clean we have 2x100 kb buffers :/ one for the framebuf and one for the lib
        self.display = st7789.ST7789(display_spi, 240,240,cs=machine.Pin(5, machine.Pin.OUT),dc=machine.Pin(27, machine.Pin.OUT),backlight=machine.Pin(12, machine.Pin.OUT),rotation=2,buffer_size=240*240*2)
        self.display.init()
        # BackLight Power
        self.pmu.enablePower(axp202.AXP202_LDO2)
        self.pmu.setLDO2Voltage(2600)
        self.pmu.clearIRQ()
        self.pmu.disableIRQ(constants_axp202.AXP202_ALL_IRQ)
        self.pmu.write_byte(constants_axp202.AXP202_POK_SET, 0x25)
        self.pmu.enableIRQ(constants_axp202.AXP202_PEK_SHORTPRESS_IRQ)
        self.pmu.enableIRQ(constants_axp202.AXP202_PEK_LONGPRESS_IRQ)
        self.pmu.setShutdownTime(constants_axp202.AXP_POWER_OFF_TIME_65)
        self.pmu.setlongPressTime(constants_axp202.AXP_LONGPRESS_TIME_2S)
        self.pmu.setTimeOutShutdown(True)
        #self.pmu.enableIRQ(constants_axp202.AXP202_ALL_IRQ)
        self.display.on()
        self.display.fill(st7789.BLACK)
    
    def services_full(self):
        testsvc = services.TestService()
        self.serviceHandler.addService(testsvc)
        self.settingsSvc = services.SettingsProviderService()
        self.serviceHandler.addService(self.settingsSvc)
        #self.eventHandler.subscribe_async(testsvc.buzz, events.EventType.TOUCH_RELEASE | events.EventType.TOUCH_HOLD, testsvc)
        self.powerSvc = services.PowerService()
        self.serviceHandler.addService(self.powerSvc)
        self.eventHandler.subscribe_async(self.powerSvc.watchdog, events.EventType.TOUCH_RELEASE | events.EventType.TOUCH_NEW, self.powerSvc)
        self.batterySvc = services.BatteryService(self.pmu)
        self.serviceHandler.addService(self.batterySvc)
        self.timeSvc = services.TimeService()
        self.serviceHandler.addService(self.timeSvc)
        self.wifiSvc = communications.WLANService()
        self.serviceHandler.addService(self.wifiSvc)
        self.BLESvc = communications.BLEService()
        self.serviceHandler.addService(self.BLESvc)
        self.overlaySvc = services.OverlayProviderService(self.graphics)
        self.serviceHandler.addService(self.overlaySvc)
        self.appSvc = services.AppService(self.graphics)
        
    
    def defineOverlays(self):
        self.overlaySvc.addOverlayElement("wifi", interface.Interface_Button(self.overlaySvc.getGraphics(), 0.65,0.85, 0.35, 0.15, textSource = "Wifi ABORT"))
        self.overlaySvc.addOverlayElement("wait", interface.Interface_Button(self.overlaySvc.getGraphics(), 0.2,0.2, 0.6, 0.6, textSource = "BLS WAIT"))
        self.overlaySvc.addOverlayElement("BLE", interface.Interface_Button(self.overlaySvc.getGraphics(), 0.65,0.85, 0.35, 0.15, textSource = "BLE ABORT", callback = self.overlays_abortBLE))
        
    def overlays_abortBLE(self):
        self.BLESvc.abort()
    
    def start_full(self):
        esp32.wake_on_touch(False)
        self.pmu = axp202.PMU()
        self.start_display()
        self.tm = interface.TextMode_st7789(self.display)
        self.tm.print("Power and Screen initialized")
        machine.freq(80000000)
        self.tm.print("CPU frequ: " + str(machine.freq()))
        self.tm.print("Flash Size: " + str(esp.flash_size()))
        self.tm.print("Unique ID: " + str(machine.unique_id()))
        self.tm.print("Reset Cause: " + str(machine.reset_cause()))
        self.tm.print("Wake Cause: " + str(machine.wake_reason()))
        micropython.alloc_emergency_exception_buf(100)
        self.tm.print("Allocated emergency buffer")
        self.serviceHandler = tasks.ServiceHandler()
        self.tm.print("ServiceHandler Created")
        self.eventHandler = events.EventHandler()
        self.tm.print("EventHandler Created")
        self.eventHandler.init_handlers(self.pmu)
        self.tm.print("EventHandler Initialized")
        self.tm.print("Creating and Initializing Graphics Mode")
        self.graphics = interface.Interface_FramebufGraphics(self.display)
        #self.graphics = interface.Interface_SlowGraphics(self.display)
        self.tm.print("Adding and Subscribing Services...")
        self.services_full()
        self.tm.print("Done")
        self.tm.print("Starting Services")
        self.serviceHandler.start()
        self.defineOverlays()
        self.tm.print("Done")
        self.tm.print("Starting App Handler")
        self.serviceHandler.addService(self.appSvc)
        self.eventHandler.subscribe_async(self.appSvc.event, events.EventType.TOUCH_RELEASE | events.EventType.TOUCH_HOLD | events.EventType.TOUCH_NEW | events.EventType.BUTTON | events.EventType.GRAPHIC_UPDATE | events.EventType.BUTTON_LONG, self.appSvc)
        self.appSvc.start()
        self.tm.print("Done")
        self.tm.print("Now entering Main Loop and Graphic Mode...")
    
    def event_long_button(self, event):
        ##self.main_deepSleep()
        return

    @staticmethod
    def IRQ_mainloop(what):
        micropython.schedule(Main.main_loop, Main._main)
    
    def main_loop(self):
        '''self.eventHandler.process()
        self.serviceHandler.process()
        self.mainScreen.tick()
        if self.powerSvc.shouldSleep():
            self.main_lightSleep()'''
        try:
            self.eventHandler.process()
            self.serviceHandler.process()
            if self.powerSvc.shouldSleep():
                self.main_lightSleep()
        except Exception as exception:
            self.mainTimer.deinit()
            self.eventHandler.stop()
            self.eventHandler.unsubscribe_byClassInstance(self)
            outstring = uio.StringIO()
            usys.print_exception(exception, outstring)
            self.tm.print(str(outstring.getvalue()))
    
    def main_full(self):
        Main._main = self
        """try:
            self.start_full()
            self.eventHandler.subscribe_async(self.powerSvc.watchdog, events.EventType.CLOCK_RESET, self.powerSvc)
            self.eventHandler.subscribe_async(self.serviceHandler.forceProcessAll_eventHandler, events.EventType.CLOCK_RESET, self.serviceHandler)
            self.eventHandler.subscribe_async(self.event_long_button, events.EventType.BUTTON_LONG, self)
            #raise RuntimeError("testException")
            mainScreen = interface.Interface(self.graphics)
            mainScreen.addElement(interface.Interface_JPG(self.graphics, 0,0, "twatch.jpg"))
            mainScreen.addElement(interface.Interface_Text(self.graphics, 0.9,0, self.batterySvc.getBatteryPercentage))
            mainScreen.addElement(interface.Interface_TextHuge(self.graphics, 0.25, 0.25, self.timeSvc.getHours))
            mainScreen.addElement(interface.Interface_TextHuge(self.graphics, 0.3833, 0.25, ":"))
            mainScreen.addElement(interface.Interface_TextHuge(self.graphics, 0.45, 0.25, self.timeSvc.getMinutes))
            mainScreen.addElement(interface.Interface_TextHuge(self.graphics, 0.5833, 0.25, ":"))
            mainScreen.addElement(interface.Interface_TextHuge(self.graphics, 0.65, 0.25, self.timeSvc.getSeconds))
            self.mainScreen = mainScreen
            self.overlaySvc.interjectInterface(self.mainScreen)
            self.display.fill(st7789.BLACK)
            self.mainScreen.update()
            self.eventHandler.subscribe_async(self.event_event_screen, events.EventType.GRAPHIC_UPDATE, self)
            self.powerSvc.reset()
            # use timer for service and events
            self.mainTimer = machine.Timer(0)
            self.mainTimer.init(period=100, mode=machine.Timer.PERIODIC, callback=Main.IRQ_mainloop)
            while True:
                machine.idle()
        except Exception as exception:
            self.eventHandler.unsubscribe_byClassInstance(self)
            outstring = uio.StringIO()
            usys.print_exception(exception, outstring)
            self.tm.print(str(outstring.getvalue()))"""
        self.start_full()
        self.eventHandler.subscribe_async(self.powerSvc.watchdog, events.EventType.CLOCK_RESET, self.powerSvc)
        self.eventHandler.subscribe_async(self.serviceHandler.forceProcessAll_eventHandler, events.EventType.CLOCK_RESET, self.serviceHandler)
        self.eventHandler.subscribe_async(self.event_long_button, events.EventType.BUTTON_LONG, self)
        #raise RuntimeError("testException")
        self.display.fill(st7789.BLACK)
        self.powerSvc.reset()
        # use timer for service and events
        self.mainTimer = machine.Timer(0)
        self.mainTimer.init(period=globals()["_mainPeriod"], mode=machine.Timer.PERIODIC, callback=Main.IRQ_mainloop)
        while True:
            machine.idle()

    def main_deepSleep(self):
        self.mainTimer.deinit()
        self.serviceHandler.stop()
        self.pmu.disablePower(axp202.AXP202_LDO2)
        self.display.sleep_mode(True)
        esp32.wake_on_ext0(machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP), esp32.WAKEUP_ALL_LOW)
        #esp32.wake_on_ext1((machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP), ), esp32.WAKEUP_ALL_LOW)
        machine.idle()
        """after waking up from lightsleep micropython doesnt disable timer wakeup.... so we set wakeuptime to 24 hours"""
        machine.deepsleep(86400000)
        
    def sleep_deepSleep(self):
        self.main_deepSleep()

    def main_lightSleep(self):
        self.mainTimer.deinit()
        self.serviceHandler.suspend()
        self.pmu.disablePower(axp202.AXP202_LDO2)
        self.display.sleep_mode(True)
        esp32.wake_on_ext0(machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP), esp32.WAKEUP_ALL_LOW)
        #esp32.wake_on_ext1((machine.Pin(35, machine.Pin.IN, machine.Pin.PULL_UP), ), esp32.WAKEUP_ALL_LOW)
        machine.lightsleep(globals()["_deepsleepTime"])
        self.powerSvc.reset()
        self.serviceHandler.unsuspend()
        if machine.wake_reason() == machine.TIMER_WAKE:
            self.sleep_deepSleep()
        self.display.sleep_mode(False)
        self.pmu.enablePower(axp202.AXP202_LDO2)
        self.mainTimer.init(period=globals()["_mainPeriod"], mode=machine.Timer.PERIODIC, callback=Main.IRQ_mainloop)

main = Main()
main.main_full()


"""graphics = interface.Interface_Graphics(tft)
interfacee = interface.Interface(graphics)
handler.subscribe_async(interfacee.event, interface)
interfacee.addElement(interface.Interface_Button(graphics, 0.25,0.25,0.25,0.25, lambda: print("button pressed"), "button"))

while True:
    handler.process()
    services.process()
    interfacee.update()
    interfacee.tick()
    utime.sleep_ms(10)"""

