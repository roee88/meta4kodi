import time
from threading import Thread, RLock
from xbmcswift2 import xbmc, xbmcgui, xbmcaddon
from meta import plugin
from settings import SETTING_ADVANCED_KEYBOARD_HACKS

def wait_for_dialog(dialog_id, timeout=None, interval=500):
    start = time.time()
    
    while not xbmc.getCondVisibility("Window.IsActive(%s)" % dialog_id):
        if xbmc.abortRequested or \
         (timeout and time.time() - start >= timeout):
            return False
        xbmc.sleep(interval)
        
    return True
    
def ok(title, msg):
    xbmcgui.Dialog().ok(title, msg)

def yesno(title, msg):
    return xbmcgui.Dialog().yesno(title, msg)
    
def select(title, items):
    return xbmcgui.Dialog().select(title, items)
    
def multiselect(title, items):
    return xbmcgui.Dialog().multiselect(title, items)

	
def select_ext(title, populator, tasks_count):
    with ExtendedDialogHacks():
        addonPath = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
        dlg = SelectorDialog("DialogSelect.xml", addonPath, title = title, 
                populator = populator, steps=tasks_count)
        dlg.doModal()
        selection = dlg.get_selection()
        del dlg
        
    return selection

class FanArtWindow(xbmcgui.WindowDialog):
    def __init__(self):
        fanart = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')

        background = xbmcgui.ControlImage(0, 0, 1280, 720, plugin.addon.getAddonInfo('fanart'))
        self.addControl(background)
        
        fanart = xbmcgui.ControlImage(0, 0, 1280, 720, fanart)
        self.addControl(fanart)

class ExtendedDialogHacks(object):
    def __enter__(self):
        self.fanart_window = FanArtWindow()
        
        self.numeric_keyboard = None         
        if plugin.get_setting(SETTING_ADVANCED_KEYBOARD_HACKS, converter=bool):
            self.numeric_keyboard = xbmcgui.Window(10109)
            Thread(target = lambda: self.numeric_keyboard.show()).start()
            wait_for_dialog('numericinput', interval=50)
            
        self.fanart_window.show()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.numeric_keyboard is not None:
            self.numeric_keyboard.close()
            del self.numeric_keyboard
            xbmc.executebuiltin("Dialog.Close(numericinput, true)")
        
        self.fanart_window.close()
        del self.fanart_window
            
class SelectorDialog(xbmcgui.WindowXMLDialog):    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.title = kwargs['title']
        self.populator = kwargs['populator']
        self.steps = kwargs['steps']
                
        self.items = []
        self.selection = None
        self.insideIndex = -1
        self.completed_steps = 0

        self.thread = None    
        self.lock = RLock()

    def get_selection(self):
        """ get final selection """
        return self.selection
        
    def __del__(self):
        pass
#        xbmcgui.WindowXMLDialog.__del__()
#        if self.thread:
#            self.thread.join()
        
    def onInit(self):
        # set title
        self.label = self.getControl(1)
        self.label.setLabel(self.title)

        # Hide ok button
        self.getControl(5).setVisible(False)
        
        # Get active list
        try:
            self.list = self.getControl(6)
            self.list.controlLeft(self.list)
            self.list.controlRight(self.list)
            self.getControl(3).setVisible(False)
        except:
            print_exc()
            self.list = self.getControl(3)
        self.setFocus(self.list)

        # populate list
        self.thread = Thread(target = self._populate)
        self.thread.start()
    
    def onAction(self, action):
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448,):
            if self.insideIndex == -1:
                self.close()
            else:
                self._inside_root(select=self.insideIndex)
        
    def onClick(self, controlID):
        if controlID == 6 or controlID == 3:
            num = self.list.getSelectedPosition()
            if num >= 0:
                if self.insideIndex == -1:
                    self._inside(num)
                else:
                    self.selection = self.items[self.insideIndex][1][num]
                    self.close()

    def onFocus(self, controlID):
        if controlID in (3,61):
            self.setFocus(self.list)
            
    def _inside_root(self, select=-1):
        with self.lock:
            self.list.reset()
            
            for source, links in self.items:
                if len(links) > 1:
                    source += " >>"
                listitem = xbmcgui.ListItem(source)
                try:
                    icon = xbmcaddon.Addon(id=links[0]['path'].split("/")[2]).getAddonInfo('icon')
                    listitem.setIconImage(icon)
                except:
                    pass
                self.list.addItem(listitem)

            if select >= 0:
                self.list.selectItem(select)
            self.insideIndex = -1
    
    def _inside(self, num):
        if num == -1:
            self._inside_root(select=self.insideIndex)
            return

        with self.lock:
            source, links = self.items[num]

            if len(links) == 1:
                self.selection = links[0]
                self.close()
                return
                
            self.list.reset()        
            for item in links:
                pluginid = item['path'].split("/")[2]
                icon = xbmcaddon.Addon(id=pluginid).getAddonInfo('icon')
                
                listitem = xbmcgui.ListItem(item['label'])
                listitem.setProperty("Path", item['path'])
                listitem.setIconImage(icon)
                
                self.list.addItem(listitem)

            self.insideIndex = num

    def step(self):
        self.completed_steps += 1
        progress = self.completed_steps * 100 / self.steps 
        self.label.setLabel(u"{0} - {1:d}%".format(self.title, progress))
        
    def _populate(self):
        #time.sleep(1)
        self.label.setLabel(self.title)
        for result in self.populator():
            self.step()
            
            if not result:
                continue
            
            with self.lock:
                # Remember selected item
                selectedItem = None
                if self.insideIndex == -1:
                    selectedIndex = self.list.getSelectedPosition()
                else:
                    selectedIndex = self.insideIndex   
                if selectedIndex >= 0:
                    selectedItem = self.items[selectedIndex]

                # Add new item
                self.items.append(result)
                self.items.sort()

                # Retrived new selection-index
                if selectedItem is not None:
                    selectedIndex = self.items.index(selectedItem)
                    if self.insideIndex != -1:
                        self.insideIndex = selectedIndex
                
                # Update only if in root
                if self.insideIndex == -1:
                    self._inside_root(select=selectedIndex)
                    self.setFocus(self.list)
        
        pass