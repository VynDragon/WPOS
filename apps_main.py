import tasks, events, interface, communications, services

class App:
    def __init__(self):
        self.mainScreen = None

    def start(self, graphics):
        self.mainScreen = interface.Interface(graphics)
        self.mainScreen.addElement(interface.Interface_JPG(graphics, 0,0, "twatch.jpg"))
        self.mainScreen.addElement(interface.Interface_Text(graphics, 0.9,0, services.BatteryService._current_BatteryService.getBatteryPercentage))
        self.mainScreen.addElement(interface.Interface_Text(graphics, 0.7,0, services.BatteryService._current_BatteryService.getBatteryVoltage))
        self.mainScreen.addElement(interface.Interface_TextHuge(graphics, 0.25, 0.25, services.TimeService._current_TimeSvc.getHours))
        self.mainScreen.addElement(interface.Interface_TextHuge(graphics, 0.3833, 0.25, ":"))
        self.mainScreen.addElement(interface.Interface_TextHuge(graphics, 0.45, 0.25, services.TimeService._current_TimeSvc.getMinutes))
        self.mainScreen.addElement(interface.Interface_TextHuge(graphics, 0.5833, 0.25, ":"))
        self.mainScreen.addElement(interface.Interface_TextHuge(graphics, 0.65, 0.25, services.TimeService._current_TimeSvc.getSeconds))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0, 0.75, 0.5, 0.25, callback = self.startMenu, textSource = "Menu"))
        self.mainScreen.addInterjectionInterface(services.OverlayProviderService._current_OverlayProviderService)
    
    def stop(self):
        pass
    
    def process(self):
        self.mainScreen.tick()
        return 0

    def event(self, event):
        if event.type in [events.EventType.TOUCH_NEW, events.EventType.TOUCH_HOLD, events.EventType.TOUCH_RELEASE]:
            self.mainScreen.event(event)
    
    def update(self):
        self.mainScreen.update()
    
    def test_scanBLE(self):
        communications.BLEService._current_BLESvc.queueRequest(self.test_scanBLE_callback)
    
    def test_scanBLE_callback(self, ble):
        ble.gap_scan(10000)
        
    def startMenu(self):
        services.AppService._current_AppSvc.startApp("menu")
        
        
app = App()

def start(graphics):
    return globals()["app"].start(graphics)

def stop():
    return globals()["app"].stop()

def process():
    return globals()["app"].process()

def event(event):
    return globals()["app"].event(event)

def update():
    return globals()["app"].update()
