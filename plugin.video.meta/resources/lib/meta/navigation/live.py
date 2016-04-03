from meta import plugin, LANG
from meta.play.base import active_players
from meta.play.players import ADDON_DEFAULT, ADDON_SELECTOR
from meta.play.live import play_channel
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_genres, get_tv_genres, caller_name, \
    caller_args
from language import get_string as _
from settings import CACHE_TTL


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

    return items


@plugin.route('/live/search')
def live_search():
    """ Activate movie search """
    search(live_search_term)


@plugin.route('/live/search_term/<term>')
def live_search_term(term):
    """ Perform search of a specified <term>"""
    return live_play(term)


@plugin.route('/live/<channel>')
def live_play(channel):
    """ Activate movie search """
    play_channel(channel)
