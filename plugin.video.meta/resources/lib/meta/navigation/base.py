import sys
import os

from xbmcswift2 import xbmc

from meta import plugin, import_tmdb, LANG
from meta.utils.text import equals

from language import get_string as _


def caller_name():
    return sys._getframe(2).f_code.co_name
    
def caller_args():
    import inspect
    caller = inspect.stack()[2][0]
    args, _, _, values = inspect.getargvalues(caller)
    return dict([(i, values[i]) for i in args])

def search(search_func):
    """ Search wrapper """
    external = False
    if plugin.id == xbmc.getInfoLabel('Container.PluginName'):
        # Skip if search item isn't currently selected    
        label = xbmc.getInfoLabel('ListItem.label')
        if label and not equals(label, _("Search")):
            return
    else:
        external = True

    # Get search keyword
    search_entered = plugin.keyboard(heading=_("search for"))
    if not search_entered:
        return
    
    # Perform search
    url = plugin.url_for(search_func, term=search_entered, page='1')
    if external:
        xbmc.executebuiltin('ActivateWindow(10025,"plugin://%s/",return)' % plugin.id)
        xbmc.executebuiltin('Container.Update("%s")' % url)
    else:
        plugin.redirect(url)

def get_icon_path(icon_name):
    addon_path = plugin.addon.getAddonInfo("path")    
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")

def get_genre_icon(genre_id):
    genre_id = int(genre_id)
    icons = {
        12: "genre_adventure",
        14: "genre_fantasy",
        16: "genre_animation",
        18: "genre_drama",
        27: "genre_horror",
        28: "genre_action",
        35: "genre_comedy",
        36: "genre_history",
        37: "genre_western",
        53: "genre_thriller",
        80: "genre_crime",
        99: "genre_documentary",
        878: "genre_scifi",
        9648: "genre_mystery",
        10402: "genre_music",
        10749: "genre_romance",
        10751: "genre_family",
        10752: "genre_war",
        10759: "genre_action",
        10762: "genre_kids",
        10763: "genre_news",
        10764: "genre_reality",
        10765: "genre_scifi",
        10766: "genre_soap",
        10767: "genre_talk",
        10768: "genre_war",
        10769: "genre_foreign",
        10770: "genre_tv",
    }
    
    if genre_id in icons:
        return get_icon_path(icons[genre_id])
    return "DefaultVideo.png"

def get_genres():
    result = get_base_genres()
    result.update(get_tv_genres())
    return result

@plugin.cached(TTL=None, cache="genres")
def get_tv_genres():
    import_tmdb()
    result = tmdb.Genres().list_tv(language=LANG)
    return dict([(i['id'], i['name']) for i in result['genres']])

@plugin.cached(TTL=None, cache="genres")
def get_base_genres():
    import_tmdb()
    result = tmdb.Genres().list(language=LANG)
    return dict([(i['id'], i['name']) for i in result['genres']])

