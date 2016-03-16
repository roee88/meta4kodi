import re
import json
from xbmcswift2 import xbmc, xbmcgui, xbmcvfs
from meta import plugin
from meta.utils.text import to_unicode

EXTENSION = ".meta.json"
HTML_TAGS_REGEX = re.compile(r'\[/?(?:color|b|i|u).*?\]', re.I|re.UNICODE)

class AddonPlayer(object):
    def __init__(self, filename, media, meta):
        self.media = media
        self.title = meta["name"]
        self.id = meta.get("id", filename.replace(".meta.json", ""))
        self.clean_title = HTML_TAGS_REGEX.sub('', self.title)
        self.pluginid = meta.get("plugin")
        self.order = meta.get("priority") or 1000                    
        self.filters = meta.get("filters", {})
        self.commands = meta.get(media, [])
        self._postprocess = meta.get("postprocess")
    
    def postprocess(self, link):
        code = self._postprocess
        if not code or not isinstance(code, basestring) or "__" in code:
            return link
        link = eval(code, {"__builtins__": {}, "link": link})        
        return link
        
    def is_empty(self):
        if self.pluginid and \
         not xbmc.getCondVisibility('System.HasAddon(%s)' % self.pluginid):
            return True
        return not bool(self.commands)
    
def get_players(media, filters = {}):
    assert media in ("tvshows", "movies")
    
    players = []
    
    players_path = "special://profile/addon_data/{0}/players/".format(plugin.id)
    files = [x for x in xbmcvfs.listdir(players_path)[1] if x.endswith(EXTENSION)]
    for file in files:
        path = players_path + file
                    
        try:
            f = xbmcvfs.File(path)
            try:
                content = f.read()
                meta = json.loads(content)
            finally:
                f.close()
            player = AddonPlayer(file, media, meta)
            if not player.is_empty():
                players.append(player)
        except Exception, e:
            plugin.log.error(repr(e))
            msg = "player %s is invalid" % file
            xbmcgui.Dialog().ok('Invalid player', msg)
            raise

                
    return sort_players(players, filters)

def sort_players(players, filters = {}):
    result = []
    for player in players:
        filtered = False
        checked = False
        for filter_key, filter_value in filters.items():    
            value = player.filters.get(filter_key)
            if value:
                checked = True
                if to_unicode(value) != to_unicode(filter_value):
                    filtered = True
        
        if not filtered:
            needs_browsing = False
            for command_group in player.commands:
                for command in command_group:
                    if command.get('steps'):
                        needs_browsing = True
                        break
            
            result.append((not checked, needs_browsing, player.order, player.clean_title.lower(), player))
    
    result.sort()
    return [x[-1] for x in result]
    
def get_needed_langs(players):
    languages = set()
    for player in players:
        for command_group in player.commands:  
            for command in command_group:
                command_lang = command.get("language", "en")
                languages.add(command_lang)
    return languages
            

ADDON_SELECTOR = AddonPlayer("selector", "any", meta={"name": "Selector"})
ADDON_DEFAULT = AddonPlayer("default", "any", meta={"name": "Default"})
