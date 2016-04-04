import json

from xbmcswift2 import xbmc

from meta import plugin, import_tmdb, LANG
from meta.utils.text import to_unicode, parse_year
from meta.utils.properties import set_property
from meta.info import get_movie_metadata
from meta.play.players import get_needed_langs, ADDON_SELECTOR
from meta.play.base import get_trakt_ids, active_players, action_cancel, action_play, on_play_video

from settings import SETTING_USE_SIMPLE_SELECTOR, SETTING_MOVIES_DEFAULT_PLAYER, SETTING_MOVIES_DEFAULT_PLAYER_FROM_LIBRARY
from language import get_string as _

def play_movie(tmdb_id, mode):  
    import_tmdb()
        
    # Get players to use
    if mode == 'select':
        play_plugin = ADDON_SELECTOR.id
    elif mode == 'library':
        play_plugin = plugin.get_setting(SETTING_MOVIES_DEFAULT_PLAYER_FROM_LIBRARY)
    else:
        play_plugin = plugin.get_setting(SETTING_MOVIES_DEFAULT_PLAYER)
    players = active_players("movies")
    players = [p for p in players if p.id == play_plugin] or players
    if not players:
        xbmc.executebuiltin( "Action(Info)")
        action_cancel()
        return
    
    # Get movie data from TMDB
    movie = tmdb.Movies(tmdb_id).info(language=LANG)
    movie_info = get_movie_metadata(movie)

    # Get movie ids from Trakt
    trakt_ids = get_trakt_ids("tmdb", tmdb_id, movie['original_title'],
                    "movie", parse_year(movie['release_date']))
    
    # Get parameters
    params = {}
    for lang in get_needed_langs(players):
        if lang == LANG:
            tmdb_data = movie
        else:
            tmdb_data = tmdb.Movies(tmdb_id).info(language=lang)
        params[lang] = get_movie_parameters(tmdb_data)
        params[lang].update(trakt_ids)
        params[lang]['info'] = movie_info
        params[lang] = to_unicode(params[lang])

    # Go for it
    link = on_play_video(mode, players, params, trakt_ids)
    if link:
        movie = tmdb.Movies(tmdb_id).info(language=LANG)
        action_play({
            'label': movie_info['title'],
            'path': link,
            'info': movie_info,
            'is_playable': True,
            'info_type': 'video',
            'thumbnail': movie_info['poster'],
            'poster': movie_info['poster'],
            'properties' : {'fanart_image' : movie_info['fanart']},
        })
        
def get_movie_parameters(movie):
    parameters = {}

    parameters['id'] = movie['id']
    parameters['imdb'] = movie['imdb_id']
    parameters['title'] = movie['title']
    parameters['original_title'] = movie['original_title']
    parameters['year'] = parse_year(movie['release_date'])
    parameters['name'] = u'%s (%s)' % (parameters['title'], parameters['year'])
    
    return parameters
