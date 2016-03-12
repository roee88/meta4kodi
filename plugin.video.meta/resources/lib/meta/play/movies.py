import json

from xbmcswift2 import xbmc

from meta import plugin, import_tmdb, LANG
from meta.utils.text import to_unicode, parse_year
from meta.utils.properties import set_property
from meta.info import get_movie_metadata
from meta.play.players import get_needed_langs, ADDON_SELECTOR
from meta.play.base import get_trakt_ids, active_players, action_cancel, action_activate, action_play, action_resolve, get_video_link

from settings import SETTING_USE_SIMPLE_SELECTOR, SETTING_MOVIES_DEFAULT_PLAYER, SETTING_MOVIES_DEFAULT_PLAYER_FROM_LIBRARY
from language import get_string as _

def play_movie(tmdb_id, mode):  
    import_tmdb()
        
    # Get active players
    players = active_players("movies")
    if not players:
        xbmc.executebuiltin( "Action(Info)")
        action_cancel()
        return

    # Get player to use
    if mode == 'select':
        play_plugin = ADDON_SELECTOR.id
    elif mode == 'library':
        play_plugin = plugin.get_setting(SETTING_MOVIES_DEFAULT_PLAYER_FROM_LIBRARY)
    else:
        play_plugin = plugin.get_setting(SETTING_MOVIES_DEFAULT_PLAYER)
    
    # Use just selected player if exists (selectors excluded)
    players = [p for p in players if p.id == play_plugin] or players

    # Get movie data from TMDB
    movie = tmdb.Movies(tmdb_id).info(language=LANG)
    movie_info = get_movie_metadata(movie)

    # Get movie ids from Trakt
    trakt_ids = get_trakt_ids("tmdb", tmdb_id, movie['original_title'],
                    "movie", parse_year(movie['release_date']))
    
    # Preload params
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
        
    # BETA
    action_cancel()
        
    # Get single video selection        
    use_simple_selector = plugin.get_setting(SETTING_USE_SIMPLE_SELECTOR, converter=bool)
    selection = get_video_link(players, params, mode, use_simple_selector)
    if not selection:
        #action_cancel()
        return
        
    # Get selection details
    link = selection['path']
    action = selection.get('action', '')
    
    plugin.log.info('Playing url: %s' % link.encode('utf-8'))

    # Activate link
    if action == "ACTIVATE":
        action_activate(link)
    else:
        movie = tmdb.Movies(tmdb_id).info(language=LANG)
        listitem = {
            'label': movie_info['title'],
            'path': link,
            'info': movie_info,
            'is_playable': True,
            'info_type': 'video',
            'thumbnail': movie_info['poster'],
            'poster': movie_info['poster'],
            'properties' : {'fanart_image' : movie_info['fanart']},
        }
        
        if trakt_ids:
            set_property('script.trakt.ids', json.dumps(trakt_ids))

        if action == "PLAY":
            action_play(listitem)
        else:
            action_resolve(listitem)

def get_movie_parameters(movie):
    parameters = {}

    parameters['id'] = movie['id']
    parameters['imdb'] = movie['imdb_id']
    parameters['title'] = movie['title']
    parameters['original_title'] = movie['original_title']
    parameters['year'] = parse_year(movie['release_date'])
    parameters['name'] = u'%s (%s)' % (parameters['title'], parameters['year'])

    for key, value in parameters.items():
        if isinstance(value, basestring):
            parameters[key + "_+"] = value.replace(" ", "+")
            parameters[key + "_-"] = value.replace(" ", "-")            
            # Hack for really bad addons
            parameters[key + "_escaped"] = value.replace(" ", "%2520")

    """
    for key, value in parameters.items():
        if isinstance(value, basestring):
            parameters[key + "_+"] = value.replace(" ", "+")
            parameters[key + "_dot"] = value.replace(" ", ".")
            parameters[key + "_%20"] = value.replace(" ", "%20")
            parameters[key + "_%2520"] = value.replace(" ", "%2520")
    
    parameters['title'] = parameters['title'].replace(' ','%20')
    parameters['title_escaped'] = parameters['title'].replace('%20','%2520')
    """
    
    return parameters
