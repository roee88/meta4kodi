import xbmc
from meta import plugin, LANG
from meta.play.base import active_players
from meta.play.players import ADDON_DEFAULT, ADDON_SELECTOR
from meta.play.live import play_channel
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_genres, get_tv_genres, caller_name, caller_args
from meta.utils.text import to_unicode, to_utf8
from language import get_string as _
from settings import CACHE_TTL

def get_channels():
    storage = plugin.get_storage("channels")
    channels = storage.get("list")
    if channels is None:
        channels = []
        storage["list"] = channels
    return channels

@plugin.route('/live/clear_channels')
def clear_channels():
    channels = get_channels()
    del channels[:]
    xbmc.executebuiltin("Container.Refresh")
    
@plugin.route('/live/remove_channel/<channel>')
def remove_channel(channel):
    channels = get_channels()
    try:
        channels.remove(channel)
    except:
        pass
    xbmc.executebuiltin("Container.Refresh")

@plugin.route('/live/move_channel_up/<channel>')
def move_channel_up(channel):
    channels = get_channels()
    old_index = channels.index(channel)
    new_index = old_index - 1
    if new_index >= 0:
        channels.insert(new_index, channels.pop(old_index))
    xbmc.executebuiltin("Container.Refresh")

@plugin.route('/live/move_channel_down/<channel>')
def move_channel_down(channel):
    channels = get_channels()
    old_index = channels.index(channel)
    new_index = old_index + 1
    if old_index >= 0:
        channels.insert(new_index, channels.pop(old_index))
    xbmc.executebuiltin("Container.Refresh")
    
@plugin.route('/live')
def live():
    """ Live TV directory """
    items = [
        {
            'label': _("Search"),
            'path': plugin.url_for(live_search),
            'icon': get_icon_path("search"),
        },
    ]
    

    channels = get_channels()
    
    if channels:
        items.append({
            'label': _("Clear channels"),
            'path': plugin.url_for(clear_channels),
            #'icon': TODO,
        })

    for (index, channel) in enumerate(channels):
        channel = to_utf8(channel)
        context_menu = [
            (
                _("Remove channel"),
                "RunPlugin({0})".format(plugin.url_for(remove_channel, channel=channel))
            )
        ]
        if index != 0:
            context_menu.append(
                (
                    _("Move up"),
                    "RunPlugin({0})".format(plugin.url_for(move_channel_up, channel=channel))
                )
            )
            
        if index != len(channels) - 1:
            context_menu.append(
                (
                    _("Move down"),
                    "RunPlugin({0})".format(plugin.url_for(move_channel_down, channel=channel))
                )
            )
            
        items.append({
            'label': channel,
            'path': plugin.url_for(live_play, channel=channel),
            'icon': "DefaultVideo.png",
            'context_menu': context_menu,
        })
        
    return items


@plugin.route('/live/search')
def live_search():
    """ Activate movie search """
    search(live_search_term)


@plugin.route('/live/search_term/<term>')
def live_search_term(term):
    """ Perform search of a specified <term>"""
    term = to_utf8(term)
    
    channels = get_channels()
    if term not in channels:
        channels.append(term)
        xbmc.executebuiltin("Container.Refresh")
    return live_play(term)



@plugin.route('/live/<channel>/<program>/<language>', options = {"program": "None", "language": "en"})
def live_play(channel, program, language):
    """ Activate movie search """
    play_channel(channel, program, language)
