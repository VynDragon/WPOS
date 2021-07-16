import tasks, events, interface, communications, services

class App:
    def __init__(self):
        self.mainScreen = None

    def start(self, graphics):
        self.mainScreen = interface.Interface(graphics)
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0, 0, 0.5, 0.5, callback = self.start1, textSource = "1"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0, 0.5, 0.5, 0.5, callback = self.start2, textSource = "2"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0.5, 0, 0.5, 0.5, callback = self.start3, textSource = "3"))
        self.mainScreen.addElement(interface.Interface_Button(graphics, 0.5, 0.5, 0.5, 0.5, callback = self.startSettings, textSource = "Settings"))
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
        return
        services.AppService._current_AppSvc.startApp("")
        
    def start2(self):
        return
        services.AppService._current_AppSvc.startApp("")
        
    def start3(self):
        return
        services.AppService._current_AppSvc.startApp("")
    
    def startSettings(self):
        services.AppService._current_AppSvc.startApp("settings")
        
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
