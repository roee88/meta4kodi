import json

from xbmcswift2 import xbmc

from meta import plugin, import_tvdb, create_tvdb, LANG
from meta.utils.properties import set_property
from meta.utils.text import to_unicode 
from meta.library.tvshows import get_player_plugin_from_library
from meta.info import get_tvshow_metadata_tvdb, get_season_metadata_tvdb, get_episode_metadata_tvdb
from meta.play.players import get_needed_langs, ADDON_SELECTOR
from meta.play.base import get_trakt_ids, active_players, action_cancel, action_activate, action_play, action_resolve, get_video_link

from settings import SETTING_USE_SIMPLE_SELECTOR, SETTING_TV_DEFAULT_PLAYER, SETTING_TV_DEFAULT_PLAYER_FROM_LIBRARY
from language import get_string as _

def play_episode(id, season, episode, mode):  
    import_tvdb()
    
    id = int(id)
    season = int(season)
    episode = int(episode)
    
    # Get database id
    dbid = xbmc.getInfoLabel("ListItem.DBID")
    try:
        dbid = int(dbid)
    except:
        dbid = None
        
    # Get show data from TVDB
    show = tvdb[id]
    show_info = get_tvshow_metadata_tvdb(show, banners=False)

    # Get active players
    players = active_players("tvshows", filters = {'network': show.get('network')})
    if not players:
        xbmc.executebuiltin( "Action(Info)")
        action_cancel()
        return

    # Get player to use
    if mode == 'select':
        play_plugin = ADDON_SELECTOR.id
    elif mode == 'library':
        play_plugin = get_player_plugin_from_library(id)
        if not play_plugin:
            play_plugin = plugin.get_setting(SETTING_TV_DEFAULT_PLAYER_FROM_LIBRARY)
    else:
        play_plugin = plugin.get_setting(SETTING_TV_DEFAULT_PLAYER)
        
    # Use just selected player if exists (selectors excluded)
    players = [p for p in players if p.id == play_plugin] or players

    # Get show ids from Trakt
    trakt_ids = get_trakt_ids("tvdb", id, show['seriesname'],
                    "show", show.get('year', 0))

    # Preload params
    params = {}
    for lang in get_needed_langs(players):
        if lang == LANG:
            tvdb_data = show
        else:
            tvdb_data = create_tvdb(lang)[id]
        if tvdb_data['seriesname'] is None:
            continue
        params[lang] = get_episode_parameters(tvdb_data, season, episode)
        params[lang].update(trakt_ids)
        params[lang]['info'] = show_info
        params[lang] = to_unicode(params[lang])
        
    # Get single video selection
    use_simple_selector = plugin.get_setting(SETTING_USE_SIMPLE_SELECTOR, converter=bool)
    selection = get_video_link(players, params, mode, use_simple_selector)
    if not selection:
        action_cancel()
        return
        
    # Get selection details
    link = selection['path']
    action = selection.get('action', '')
    
    plugin.log.info('Playing url: %s' % link.encode('utf-8'))

    # Activate link
    if action == "ACTIVATE":
        action_activate(link)
    else:
        # Build list item (needed just for playback from widgets)
        season_info = get_season_metadata_tvdb(show_info, show[season], banners=False)
        episode_info = get_episode_metadata_tvdb(season_info, show[season][episode])
        listitem = {
            'label': episode_info['title'],
            'path': link,
            'info': episode_info,
            'is_playable': True,
            'info_type': 'video',
            'thumbnail': episode_info['poster'],
            'poster': episode_info['poster'],
            'properties' : {'fanart_image' : episode_info['fanart']},
        }
    
        # set properties
        if trakt_ids:
            set_property('script.trakt.ids', json.dumps(trakt_ids))
        set_property("data", json.dumps({'dbid': dbid, 'tvdb': id, 
            'season': season, 'episode': episode}))
        
        # Play
        if action == "PLAY":
            action_play(listitem)
        else:
            action_resolve(listitem)

        
def get_episode_parameters(show, season, episode):
    id = show['id']
    
    # Get parameters
    parameters = {'id': id, 'season': season, 'episode': episode}
    parameters['network'] = show.get('network', '')
    parameters['showname'] = show['seriesname']
    parameters['clearname'], _ = xbmc.getCleanMovieTitle(parameters['showname'])
    parameters['name'] = u'{showname} S{season:02d}E{episode:02d}'.format(**parameters)
    parameters['title'] = show[season][episode].get('episodename', str(episode))
    parameters['absolute_number'] = show[season][episode].get('absolute_number')        
    parameters['firstaired'] = show[season][episode].get('firstaired')
    parameters['year'] = show.get('year', 0)
    parameters['imdb'] = show.get('imdb_id', '')    
    try:
        genre = [x for x in show['genre'].split('|') if not x == '']
    except:
        genre = []
    parameters['genre'] = " / ".join(genre)

    for key, value in parameters.items():
        if isinstance(value, basestring):
            parameters[key + "_+"] = value.replace(" ", "+")
            # Hack for really bad addons
            parameters[key + "_escaped"] = value.replace(" ", "%2520")

    """
    parameters = {'id': id, 'season': season, 'episode': episode}
    parameters['network'] = show.get('network')
    parameters['showname'] = show['seriesname'].replace(" ", "+")
    
    parameters['showname_clear'], _ = xbmc.getCleanMovieTitle(parameters['showname'])
    
    parameters['showname_escaped'] = show['seriesname'].replace(" ", "%2520")
    parameters['name'] = u'{showname}+S{season:02d}E{episode:02d}'.format(**parameters)
    try:
        parameters['title'] = show[season][episode]['episodename'].replace(" ", "+")
    except:
        parameters['title'] = ""
    
    try:
        parameters['absolute_number'] = show[season][episode].get('absolute_number')
    except:
        parameters['absolute_number'] = None
        
    parameters['year'] = show.get('year', 0)

    try:
        parameters['imdb'] = show['imdb_id'][2:]
    except:
        parameters['imdb'] = ""

    parameters['firstaired'] = show[season][episode]['firstaired']
    
    try:
        genre = [x for x in show['genre'].split('|') if not x == '']
    except:
        genre = []
    parameters['genre'] = " / ".join(genre).replace('/','%2F').replace(" ", "+")
        
    for key, value in parameters.items():
        if isinstance(value, basestring):
            parameters[key + "_p"] = value.replace(" ", "+")
            parameters[key + "_d"] = value.replace("+", " ").replace(" ", ".")
            parameters[key + "_e"] = value.replace("+", " ").replace(" ", "%20")
    """
    return parameters
