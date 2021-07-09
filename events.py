import uasyncio
import machine
import micropython
import struct
import focaltouch
import tasks


class EventType:
    TOUCH_NEW = 1
    TOUCH_HOLD = 2
    TOUCH_RELEASE = 4
    BUTTON = 8
    GRAPHIC_UPDATE = 16
    CLOCK_RESET = 32
    BUTTON_LONG = 64

class Event:
    def __init__(self, type, **data):
        self.type = type
        self.data = data

"""event handler is STOPPED at suspend and subscriptions are not recovered, subscriptions must take that into account"""

class EventHandler:
    _current_EventHandler = None
    
    def __init__(self):
        print("EventHandler Starting...")
        self.subscribed_async = []
        self.subscribed = []
        self.touch = None
        self.axp202 = None
        self.touchTable = []
        self.IRQ_TOUCH_DATA = bytearray(1)
        self.IRQ_TOUCH_DATA[0] = 0

    def init_handlers(self, axp202):
        EventHandler._current_EventHandler = self
        #touch init
        self.touchi2c = machine.I2C(1,scl=machine.Pin(32), sda=machine.Pin(23))
        self.touch = focaltouch.FocalTouch(self.touchi2c)
        machine.Pin(38, machine.Pin.IN).irq(handler = EventHandler.IRQ_TOUCH_ANY, trigger = machine.Pin.IRQ_RISING)
        # axp202
        self.axp202 = axp202
        machine.Pin(35, machine.Pin.IN).irq(handler = EventHandler.IRQ_AXP202, trigger = machine.Pin.IRQ_FALLING, wake = machine.SLEEP | machine.DEEPSLEEP)

    def processSubscritionForEvent(self, event):
        for function, filter, instance in self.subscribed_async:
            if event.type & filter: 
                uasyncio.create_task(function(event))
        for function, filter, instance in self.subscribed:
            if event.type & filter: 
                function(event)

    def handle_touch(self):
        toucheds = self.touch.touches
        for touch in toucheds:
            if touch["id"] not in self.touchTable:
                print("TOUCH NEW " + str(touch))
                self.processSubscritionForEvent(Event(EventType.TOUCH_NEW, x = touch["x"], y = touch["y"]))
                self.touchTable.append(touch["id"])
                
    def handle_axp202(self):
        self.axp202.readIRQ()
        tmpbuff = bytearray(5)
        for i in range(5):
            tmpbuff[i] = self.axp202.irqbuf[i]
        self.axp202.clearIRQ()
        if tmpbuff[2] & 1:
            print("BUTTON_LONG")
            self.processSubscritionForEvent(Event(EventType.BUTTON_LONG))
        if tmpbuff[2] & 2:
            print("BUTTON")
            self.processSubscritionForEvent(Event(EventType.BUTTON))
    
    @staticmethod
    def IRQ_TOUCH_ANY(pin):
        EventHandler._current_EventHandler.IRQ_TOUCH_DATA[0] = EventType.TOUCH_NEW
        micropython.schedule(EventHandler.handle_touch, EventHandler._current_EventHandler)

    @staticmethod
    def IRQ_AXP202(pin):
        micropython.schedule(EventHandler.handle_axp202, EventHandler._current_EventHandler)

    def process(self):
        toucheds = self.touch.touches
        ntouchTable = [x["id"] for x in toucheds]
        if EventHandler._current_EventHandler.IRQ_TOUCH_DATA[0] > 0:
            for touch in toucheds:
                if touch["id"] in self.touchTable:
                    print("TOUCH HOLD " + str(touch))
                    self.processSubscritionForEvent(Event(EventType.TOUCH_HOLD, x = touch["x"], y = touch["y"]))
            self.touchTable = ntouchTable
        elif len(self.touchTable) > 0:
            print("TOUCH RELEASE")
            self.processSubscritionForEvent(Event(EventType.TOUCH_RELEASE))
            self.touchTable = []
        EventHandler._current_EventHandler.IRQ_TOUCH_DATA[0] = 0

    def trigger_event(self, type):
        self.processSubscritionForEvent(Event(type))
    
    def subscribe_async(self, function, filter, classinstance = None):
        self.subscribed_async.append((function, filter, classinstance))

    def subscribe(self, function, filter, classinstance = None):
        self.subscribed.append((function, filter, classinstance))

    def unsubscribe_byClassInstance(self, classinstance):
        self.subscribed = [var for var in self.subscribed if var[1] != classinstance]
        self.subscribed_async = [var for var in self.subscribed if var[1] != classinstance]
