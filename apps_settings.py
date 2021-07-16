import tasks, events, interface, communications, services

class App:
    def __init__(self):
        self.mainScreen = None

    def start(self, graphics):
        self.mainScreen = interface.Interface(graphics)
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0, 0, 0.5, 0.5, callback = self.start1, textSource = "Brightness-"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0, 0.5, 0.5, 0.5, callback = self.start2, textSource = "2"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0.5, 0, 0.5, 0.5, callback = self.start3, textSource = "Brightness+"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0.5, 0.5, 0.5, 0.5, callback = self.start4, textSource = "4"))
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
    
    def start1(self):
        b = services.SettingsService._current_SettingsSvc.getBrightness()
        services.SettingsService._current_SettingsSvc.setBrightness(b-1)
        
    def start2(self):
        return
        
    def start3(self):
        b = services.SettingsService._current_SettingsSvc.getBrightness()
        services.SettingsService._current_SettingsSvc.setBrightness(b+1)
    
    def start4(self):
        return
        services.AppService._current_AppSvc.startApp("")
        
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
