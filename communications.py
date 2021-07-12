import events, tasks, services
import network, ubluetooth, ujson, utime

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)


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

    def tryConnect(self, networkList):
        for thenetwork in networkList:
            print("trying to connect to " + str(thenetwork['essid']))
            self.wifi.connect(thenetwork['essid'], thenetwork['password'])
            status = self.wifi.status()
            while status == network.STAT_CONNECTING:
                utime.sleep_ms(100)
                status = self.wifi.status()
            if status == network.STAT_GOT_IP:
                print("connection succeeded")
                return True
            print("connection failed because " + str(status))
        return False
        
    def process(self):
        super().process()
        if len(self.requestQueue) > 0:
            #machine.freq(240000000)
            services.OverlayProviderService._current_OverlayProviderService.enableOverlay("wifi")
            events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
            self.wifi.active(True)
            if self.tryConnect(self.settings):
                while len(self.requestQueue) > 0:
                    (self.requestQueue.pop())(self.wifi)
                utime.sleep_ms(1000)
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
        self.BLE = ubluetooth.BLE()
    
    def start(self):
        super().start()
        BLEService._current_BLESvc = self
        self.BLE.irq(self.bt_irq)
        #with open('/bluetooth.json', 'r') as f:
        #    self.settings = ujson.load(f)
    
    def stop(self):
        super().stop()
        self.BLE.active(False)
        #if self.config_changed:
        #    with open('/bluetooth.json', 'w') as f:
        #        ujson.dump(self.settings, f)
    
    def suspend(self):
        super().suspend()
        self.BLE.active(False)
        
    def process(self):
        super().process()
        if len(self.requestQueue) > 0:
            #machine.freq(240000000)
            services.OverlayProviderService._current_OverlayProviderService.enableOverlay("BLE")
            events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
            self.BLE.active(True)
            while len(self.requestQueue) > 0:
                (self.requestQueue.pop())(self.BLE)
            #self.BLE.active(False)
            print("done with BLE")
            services.OverlayProviderService._current_OverlayProviderService.disableOverlay("BLE")
            #machine.freq(80000000)
    
    def abort(self):
        return #do nothing becasue we cant actually interupt operations due to the magic of having no multithreading.
        
    def bt_irq(self, event, data):
        print("BLE Event:" + str(event))
        if event == _IRQ_CENTRAL_CONNECT:
            # A central has connected to this peripheral.
            conn_handle, addr_type, addr = data
        elif event == _IRQ_CENTRAL_DISCONNECT:
            # A central has disconnected from this peripheral.
            conn_handle, addr_type, addr = data
        elif event == _IRQ_GATTS_WRITE:
            # A client has written to this characteristic or descriptor.
            conn_handle, attr_handle = data
        elif event == _IRQ_GATTS_READ_REQUEST:
            # A client has issued a read. Note: this is only supported on STM32.
            # Return a non-zero integer to deny the read (see below), or zero (or None)
            # to accept the read.
            conn_handle, attr_handle = data
        elif event == _IRQ_SCAN_RESULT:
            # A single scan result.
            addr_type, addr, adv_type, rssi, adv_data = data
            print("BLE Result:")
            print("addr_type:" + str(addr_type))
            print("addr:" + str(bytes(addr).decode()))
            print("adv_type:" + str(adv_type))
            print("rssi:" + str(rssi))
            print("adv_data:" + str(bytes(adv_data).decode()))
        elif event == _IRQ_SCAN_DONE:
            # Scan duration finished or manually stopped.
            pass
        elif event == _IRQ_PERIPHERAL_CONNECT:
            # A successful gap_connect().
            conn_handle, addr_type, addr = data
        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Connected peripheral has disconnected.
            conn_handle, addr_type, addr = data
        elif event == _IRQ_GATTC_SERVICE_RESULT:
            # Called for each service found by gattc_discover_services().
            conn_handle, start_handle, end_handle, uuid = data
        elif event == _IRQ_GATTC_SERVICE_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Called for each characteristic found by gattc_discover_services().
            conn_handle, def_handle, value_handle, properties, uuid = data
        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
        elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
            # Called for each descriptor found by gattc_discover_descriptors().
            conn_handle, dsc_handle, uuid = data
        elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
            # Called once service discovery is complete.
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, status = data
        elif event == _IRQ_GATTC_READ_RESULT:
            # A gattc_read() has completed.
            conn_handle, value_handle, char_data = data
        elif event == _IRQ_GATTC_READ_DONE:
            # A gattc_read() has completed.
            # Note: The value_handle will be zero on btstack (but present on NimBLE).
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
        elif event == _IRQ_GATTC_WRITE_DONE:
            # A gattc_write() has completed.
            # Note: The value_handle will be zero on btstack (but present on NimBLE).
            # Note: Status will be zero on success, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
        elif event == _IRQ_GATTC_NOTIFY:
            # A server has sent a notify request.
            conn_handle, value_handle, notify_data = data
        elif event == _IRQ_GATTC_INDICATE:
            # A server has sent an indicate request.
            conn_handle, value_handle, notify_data = data
        elif event == _IRQ_GATTS_INDICATE_DONE:
            # A client has acknowledged the indication.
            # Note: Status will be zero on successful acknowledgment, implementation-specific value otherwise.
            conn_handle, value_handle, status = data
        elif event == _IRQ_MTU_EXCHANGED:
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data
        elif event == _IRQ_L2CAP_ACCEPT:
            # A new channel has been accepted.
            # Return a non-zero integer to reject the connection, or zero (or None) to accept.
            conn_handle, cid, psm, our_mtu, peer_mtu = data
        elif event == _IRQ_L2CAP_CONNECT:
            # A new channel is now connected (either as a result of connecting or accepting).
            conn_handle, cid, psm, our_mtu, peer_mtu = data
        elif event == _IRQ_L2CAP_DISCONNECT:
            # Existing channel has disconnected (status is zero), or a connection attempt failed (non-zero status).
            conn_handle, cid, psm, status = data
        elif event == _IRQ_L2CAP_RECV:
            # New data is available on the channel. Use l2cap_recvinto to read.
            conn_handle, cid = data
        elif event == _IRQ_L2CAP_SEND_READY:
            # A previous l2cap_send that returned False has now completed and the channel is ready to send again.
            # If status is non-zero, then the transmit buffer overflowed and the application should re-send the data.
            conn_handle, cid, status = data
        elif event == _IRQ_CONNECTION_UPDATE:
            # The remote device has updated connection parameters.
            conn_handle, conn_interval, conn_latency, supervision_timeout, status = data
        elif event == _IRQ_ENCRYPTION_UPDATE:
            # The encryption state has changed (likely as a result of pairing or bonding).
            conn_handle, encrypted, authenticated, bonded, key_size = data
        elif event == _IRQ_GET_SECRET:
            # Return a stored secret.
            # If key is None, return the index'th value of this sec_type.
            # Otherwise return the corresponding value for this sec_type and key.
            sec_type, index, key = data
            return value
        elif event == _IRQ_SET_SECRET:
            # Save a secret to the store for this sec_type and key.
            sec_type, key, value = data
            return True
        elif event == _IRQ_PASSKEY_ACTION:
            # Respond to a passkey request during pairing.
            # See gap_passkey() for details.
            # action will be an action that is compatible with the configured "io" config.
            # passkey will be non-zero if action is "numeric comparison".
            conn_handle, action, passkey = data
    
    """ callable must take one argument, the wlan object, and must be a async callable."""
    def queueRequest(self, callable):
        self.requestQueue.append(callable)
        
    @staticmethod
    def getBLESvc():
        return BLEService._current_BLESvc
