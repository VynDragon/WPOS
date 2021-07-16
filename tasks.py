import utime
import profiling

"""milliseconds"""
SERVICEFREQUENCY = 10

class Service:
    """"interval in seconds, must be > 1"""
    def __init__(self, name, interval, suspend_is_stop = True):
        self.name = name
        self.suspend_is_stop = bool(suspend_is_stop)
        self.last_ran = 0
        self.interval = interval

    def start(self):
        """ do something at start
        derived must call parent's
        must must recover relevant data"""
        

    def stop(self):
        """ do something at stop
        derived must call parent's
        must save relevant data and setup IRQs"""
        

    def suspend(self):
        """ do something before sleeping
        derived must call parent's"""
        

    def unsuspend(self):
        """ do something after sleeping
        derived must call parent's"""
        

    def process(self):
        """ do something at interval """

class Foreground:
    def __init__(self, name, **args):
        self.name = name
        self.args = args

    def update(self):
        """ do something every draw"""

    def tick(self):
        """ do something every actable unit """

    def event(self, event):
        """ bruh bruh bruh """

class ServiceHandler:
    def __init__(self):
        print("ServiceHandler Starting...")
        self.services = []
        """self.countercheck = 0
        self.last_counter = 0 
        self.averagetickbetweenrun = 0"""

    def start(self):
        for service in self.services:
            service.start()


    def stop(self):
        for service in self.services:
            service.stop()


    def process(self):
    # todo: use RTC time because utime.time doesnt go up when we sleep
        currenttime = utime.time()
        for service in self.services:
            if service.last_ran + service.interval < currenttime:
                service.process()
                service.last_ran = currenttime
            if currenttime < service.last_ran:
                service.process()
                service.last_ran = currenttime
        """if self.countercheck > 30:
            print(self.averagetickbetweenrun)
            self.countercheck = 0
        self.averagetickbetweenrun = ((utime.ticks_ms() - self.last_counter) + self.averagetickbetweenrun) / 2
        self.last_counter = utime.ticks_ms()
        self.countercheck += 1"""
    
    
    """ to unfuck when we reset the clock!"""
    def forceProcessAll(self):
        currenttime = utime.time()
        for service in self.services:
            service.process()
            service.last_ran = currenttime
            
    def forceProcessAll_eventHandler(self, event):
        self.forceProcessAll()

    def suspend(self):
        for service in self.services:
            if service.suspend_is_stop:
                service.stop()
            else:
                service.suspend()
        
    def unsuspend(self):
        for service in self.services:
            if service.suspend_is_stop:
                service.start()
            else:
                service.unsuspend()
            

    def addService(self, service):
        if service not in self.services:
            self.services.append(service)

    def getFirstService(self, name):
        for service in self.services:
            if service.name == name:
                return service
        return None


    def removeFirstService(self, name):
        for id, service in enumerate(self.services):
            if service.name == name:
                self.services.pop(id)
                return True
        return False
