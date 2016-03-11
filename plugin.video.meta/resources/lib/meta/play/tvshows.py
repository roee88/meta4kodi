import re
import json
from xbmcswift2 import xbmc

from meta import plugin, import_tmdb, import_tvdb, create_tvdb, LANG
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
    import_tmdb()
    
    episode_obj = show[season][episode]
    
    # Get parameters
    parameters = {'id': show['id'], 'season': season, 'episode': episode}
    
    network = show.get('network', '')
    
    parameters['network'] = network
    parameters['network_clean'] = re.sub("(\(.*?\))", "", network).strip()
    
    parameters['showname'] = show['seriesname']
    #parameters['clearname'], _ = xbmc.getCleanMovieTitle(parameters['showname'])
    parameters['clearname'] = re.sub("(\(.*?\))", "", network).strip()

    parameters['absolute_number'] = episode_obj.get('absolute_number')
    parameters['title'] = episode_obj.get('episodename', str(episode))
    parameters['firstaired'] = episode_obj.get('firstaired')
    parameters['year'] = show.get('year', 0)
    parameters['imdb'] = show.get('imdb_id', '')    

    try:
        genre = [x for x in show['genre'].split('|') if not x == '']
    except:
        genre = []
    parameters['genre'] = " / ".join(genre)

    is_anime = False
    if parameters['absolute_number'] and \
     parameters['absolute_number'] != '0' and \
     "animation" in parameters['genre'].lower():
        tmdb_results = tmdb.Find(show['id']).info(external_source="tvdb_id") or {}
        for tmdb_show in tmdb_results.get("tv_results", []):
            if "JP" in tmdb_show['origin_country']:
                is_anime = True
        
    if is_anime:
        parameters['name'] = u'{showname} {absolute_number}'.format(**parameters)
    else:
        parameters['name'] = u'{showname} S{season:02d}E{episode:02d}'.format(**parameters)

    for key, value in parameters.items():
        if isinstance(value, basestring):
            parameters[key + "_+"] = value.replace(" ", "+")
            # Hack for really bad addons
            parameters[key + "_escaped"] = value.replace(" ", "%2520")

    return parameters
