import st7789
import framebuf
import events
import vga1_8x8
import vga1_bold_16x32

class Interface_Graphics:
    def __init__(self, display, displaysizex = 240, displaysizey = 240):
        self.dsx = displaysizex
        self.dsy = displaysizey
        self.display = display
    
    def drawButtonOutline(self, x, y, sx, sy):
        """ahah"""
            
    def drawText(self, x, y, text):
        """ahah"""
        
    def drawTextHuge(self, x, y, text):
        """ahah"""
    
    def isInZone(self, x, y, x1, y1, x2, y2):
        if x > x1 * self.dsx and x < x2 * self.dsx and y > y1 * self.dsy and y < y2 * self.dsy:
            return True
        return False
    
    def update(self):
        """ahah"""
        
    def pre_update(self):
        """ahah"""
        
    def blit(self, fbuf, x, y):
        """ahah"""
    
    def jpg(self, x, y, filename):
        """ahah"""

class Interface_FramebufGraphics(Interface_Graphics):
    def __init__(self, display, displaysizex = 240, displaysizey = 240):
        super().__init__(display, displaysizex, displaysizey)
        self.buffArray = bytearray(displaysizex * displaysizey * 2)
        self.buff = framebuf.FrameBuffer(self.buffArray, displaysizex, displaysizey, framebuf.RGB565)
    
    def drawButtonOutline(self, x, y, sx, sy):
        self.buff.rect(int(x * self.dsx), int(y * self.dsy), int(sx * self.dsx), int(sy * self.dsy), 0xF800)
            
    def drawText(self, x, y, text):
        self.buff.text(text, int(x * self.dsx), int(y * self.dsy), 0xFFFF)
    
    """todo"""
    def drawTextHuge(self, x, y, text):
        self.buff.text(text, int(x * self.dsx), int(y * self.dsy), 0xFFFF)
    
    def blit(self, fbuf, x, y):
        self.buff.blit(fbuf, x, y)
    
    def pre_update(self):
        self.buff.fill(0)
    
    def update(self):
        bA_ref = self.buffArray
        disp_ref = self.display
        disp_ref.blit_buffer(bA_ref, 0, 0, 240, 240)

class Interface_SlowGraphics(Interface_Graphics):
    def __init__(self, display, displaysizex = 240, displaysizey = 240):
        super().__init__(display, displaysizex, displaysizey)
    
    def drawButtonOutline(self, x, y, sx, sy):
        self.display.rect(int(x * self.dsx), int(y * self.dsy), int(sx * self.dsx), int(sy * self.dsy), st7789.RED)
            
    def drawText(self, x, y, text):
        self.display.text(vga1_8x8, text, int(x * self.dsx), int(y * self.dsy))
        
    def drawTextHuge(self, x, y, text):
        self.display.text(vga1_bold_16x32, text, int(x * self.dsx), int(y * self.dsy))
        
    def pre_update(self):
        self.display.fill(st7789.BLACK)
        
    def jpg(self, x, y, filename):
        self.display.jpg(filename, x, y , st7789.SLOW)


class Interface_Element:
    def __init__(self, graphics, x, y):
        self.x = x
        self.y = y
        self.graphics = graphics
    def update(self):
        """ draw """
        
    def tick(self):
        """update nongraphic stuffs"""

    def event(self, event):
        """process event"""

class Interface_Bitmap(Interface_Element):
    def __init__(self, graphics, x, y, sx, sy, data):
        super().__init__(graphics, x, y)
        self.sx = sx
        self.sy = sy
        self.data = data

    def update(self):
        self.graphics.blit(self.data, x, y)
        
class Interface_JPG(Interface_Element):
    def __init__(self, graphics, x, y, jpgfilename):
        super().__init__(graphics, x, y)
        self.filename = jpgfilename

    def update(self):
        self.graphics.jpg(self.x, self.y, self.filename)

class Interface_Button(Interface_Element):
    def __init__(self, graphics, x, y, sx, sy, callback = None, textSource = None):
        super().__init__(graphics, x, y)
        self.text = Interface_Text(graphics, x, y + sy / 2, textSource)
        self.sx = sx
        self.sy = sy
        self.callback = callback
        self.pressing = False
        self.held = False
    
    def update(self):
        super().update()
        self.graphics.drawButtonOutline(self.x, self.y, self.sx, self.sy)
        self.text.update()
        if self.held:
            self.graphics.drawButtonOutline(self.x + 0.05, self.y + 0.05, self.sx - 0.1, self.sy - 0.1)
        
    def event(self, event):
        super().event(event)
        if self.graphics.isInZone(float(event.data["x"]), float(event.data["y"]), self.x, self.y, self.x + self.sx, self.y + self.sy):
            self.held = True
            if event.type & events.EventType.TOUCH_RELEASE:
                (self.callback)()
        if event.type & events.EventType.TOUCH_RELEASE:
            self.held = False

class Interface_Text(Interface_Element):
    def __init__(self, graphics, x, y, textSource):
        super().__init__(graphics, x, y)
        self.textSource = textSource
    
    def update(self):
        super().update()
        if callable(self.textSource):
            self.graphics.drawText(self.x, self.y, (self.textSource)())
        else:
            self.graphics.drawText(self.x, self.y, self.textSource)
      
      
class Interface_TextHuge(Interface_Element):
    def __init__(self, graphics, x, y, textSource):
        super().__init__(graphics, x, y)
        self.textSource = textSource
    
    def update(self):
        super().update()
        if callable(self.textSource):
            self.graphics.drawTextHuge(self.x, self.y, (self.textSource)())
        else:
            self.graphics.drawTextHuge(self.x, self.y, self.textSource)
      


class Interface:
    def __init__(self, graphics):
        self.elements = []
        self.InterjectionInterfaces = []
        self.graphics = graphics
     
    def update(self):
        self.graphics.pre_update()
        for element in self.elements:
            element.update()
        for inter in self.InterjectionInterfaces:
            for element in inter.elements:
                element.update()
        self.graphics.update()
    
    def tick(self):
        for element in self.elements:
            element.tick()
        for inter in self.InterjectionInterfaces:
            for element in inter.elements:
                element.tick()

    def event(self, event):
        for element in self.elements:
            element.event(event)
        events.EventHandler._current_EventHandler.trigger_event(events.EventType.GRAPHIC_UPDATE)
    
    def getGraphics(self):
        return self.graphics
    
    def addElement(self, element):
        self.elements.append(element)
        
    def removeElement(self, element):
        self.elements.remove(element)
        
    def addInterjectionInterface(self, element):
        self.InterjectionInterfaces.append(element)
    
    def removeInterjectionInterface(self, element):
        self.InterjectionInterfaces.remove(element)

class TextMode_st7789:
    _lines = 30
    _line_offset = 8
    _rows = 30
    _rows_offset = 8
    
    def __init__(self, display):
        self.display = display
        self.lines = []
    
    def print(self, text):
        texts = text.split("\n")
        for tex in texts:
            self.print_noreturns(tex)
    
    def print_noreturns(self, text):
        while len(text) > self._rows:
            text2 = text[:self._rows]
            self.lines.append(text2)
            if len(self.lines) > self._lines:
                self.force_redraw()
            else:
                self.display.text(vga1_8x8, text2, 0, (len(self.lines) - 1) * self._line_offset)
            text = text[self._rows:]
        self.lines.append(text)
        if len(self.lines) > self._lines:
            self.force_redraw()
        else:
            self.display.text(vga1_8x8, text, 0, (len(self.lines) - 1) * self._line_offset)

    def force_redraw(self):
        self.display.fill(st7789.BLACK)
        if len(self.lines) > self._lines:
            self.lines = self.lines[-self._lines:]
        for id, line in enumerate(self.lines):
            self.display.text(vga1_8x8, line, 0, id * self._line_offset)
    
