import os
import copy
import time
from xbmcswift2 import xbmc, xbmcvfs

from meta import plugin, import_tmdb, import_tvdb, LANG
from meta.gui import dialogs
from meta.info import get_tvshow_metadata_tvdb, get_season_metadata_tvdb, get_episode_metadata_tvdb, \
    get_tvshow_metadata_trakt, get_season_metadata_trakt, get_episode_metadata_trakt
from meta.utils.text import parse_year, is_ascii, to_utf8
from meta.utils.executor import execute
from meta.utils.properties import set_property
from meta.library.tvshows import setup_library, add_tvshow_to_library
from meta.library.tools import scan_library
from meta.play.base import active_players
from meta.play.tvshows import play_episode
from meta.play.players import ADDON_DEFAULT, ADDON_SELECTOR
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_genres, get_tv_genres,\
    caller_name, caller_args
from language import get_string as _
from settings import CACHE_TTL, SETTING_TV_LIBRARY_FOLDER


@plugin.route('/tv')
def tv():
    """ TV directory """
    items = [
        {
            'label': _("Search"),
            'path': plugin.url_for(tv_search),
            'icon': get_icon_path("search"),
        },
        {
            'label': _("Genres"),
            'path': plugin.url_for(tv_genres),
            'icon': get_icon_path("genres"),
        },
        {
            'label': _("Popular"),
            'path': plugin.url_for(tv_most_popular, page='1'),
            'icon': get_icon_path("popular"),
        },
        {
            'label': _("On the air"),
            'path': plugin.url_for(tv_now_playing, page='1'),
            'icon': get_icon_path("ontheair"),
        },
        {
            'label': _("Top rated"),
            'path': plugin.url_for(tv_top_rated, page='1'),
            'icon': get_icon_path("top_rated"),
        },
        {
            'label': _("Trakt collection"),
            'path': plugin.url_for(tv_trakt_collection),
            'icon': get_icon_path("traktcollection"),
            'context_menu': [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for(tv_trakt_collection_to_library))
                )
            ],
        },
        {
            'label': _("Trakt watchlist"),
            'path': plugin.url_for(tv_trakt_watchlist),
            'icon': get_icon_path("traktwatchlist"),
            'context_menu': [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for(tv_trakt_watchlist_to_library))
                )
            ],
        },
        {
            'label': _("Next episodes"),
            'path': plugin.url_for(tv_trakt_next_episodes),
            'icon': get_icon_path("traktnextepisodes"),
        },
        {
            'label': _("My calendar"),
            'path': plugin.url_for(tv_trakt_calendar),
            'icon': get_icon_path("traktcalendar"),
        },
        {
            'label': _("Trakt recommendations"),
            'path': plugin.url_for(tv_trakt_recommendations),
            'icon': get_icon_path("traktrecommendations"),
        },
    ]
    
    fanart = plugin.addon.getAddonInfo('fanart')
    for item in items:
        item['properties'] = {'fanart_image' : fanart}

    return items

@plugin.route('/tv/search')
def tv_search():
    """ Activate movie search """
    search(tv_search_term)

@plugin.route('/tv/play_by_name/<name>/<season>/<episode>/<lang>', options = {"lang": "en"})
def tv_play_by_name(name, season, episode, lang):
    """ Activate tv search """
    tvdb_id = get_tvdb_id_from_name(name, lang)
    if tvdb_id:
        tv_play(tvdb_id, season, episode, "default")

@plugin.route('/tv/play_by_name_only/<name>/<lang>', options = {"lang": "en"})
def tv_play_by_name_only(name, lang):
    tvdb_id = get_tvdb_id_from_name(name, lang)
    if tvdb_id:
        season = None
        episode = None
        show = tv_tvshow(tvdb_id)

        while season is None or episode is None:  # don't exit completely if pressing back from episode selector
            selection = dialogs.select(_("Choose season"), [item["label"] for item in show])
            if selection != -1:
                season = show[selection]["info"]["season"]
                season = int(season)
            else:
                return
            items = []
            episodes = tv_season(tvdb_id, season)
            for item in episodes:
                label = "S{0}E{1} - {2}".format(item["info"]["season"], item["info"]["episode"],
                                                to_utf8(item["info"]["title"]))
                if item["info"]["plot"] is not None:
                    label += " - {0}".format(to_utf8(item["info"]["plot"]))
                items.append(label)
            selection = dialogs.select(_("Choose episode"), items)
            if selection != -1:
                episode = episodes[selection]["info"]["episode"]
                episode = int(episode)
                tv_play(tvdb_id, season, episode, "default")

def get_tvdb_id_from_name(name, lang):
    import_tvdb()

    search_results = tvdb.search(name, language=lang)

    if search_results == []:
        dialogs.ok(_("Show not found"), "{0} {1} in tvdb".format(_("no show information found for"), to_utf8(name)))
        return

    items = []
    for show in search_results:
        if "firstaired" in show:
            show["year"] = int(show['firstaired'].split("-")[0].strip())
        else:
            show["year"] = 0
        items.append(show)

    if len(items) > 1:
        selection = dialogs.select(_("Choose Show"), ["{0} ({1})".format(
            to_utf8(s["seriesname"]), s["year"]) for s in items])
    else:
        selection = 0
    if selection != -1:
        return items[selection]["id"]


@plugin.route('/tv/search_term/<term>/<page>')
def tv_search_term(term, page):
    """ Perform search of a specified <term>"""
#    import_tmdb()
#    result = tmdb.Search().tv(query=term, language=LANG, page=page)
#    return list_tvshows(result)

    import_tvdb()
    
    search_results = tvdb.search(term, language=LANG)

    items = []
    load_full_tvshow = lambda tvshow : tvdb.get_show(tvshow['id'], full=True)
    for tvdb_show in execute(load_full_tvshow, search_results, workers=10):
        info = build_tvshow_info(tvdb_show)
        items.append(make_tvshow_item(info))
    
    return items

@plugin.cached_route('/tv/most_popular/<page>', TTL=CACHE_TTL)
def tv_most_popular(page):
    """ Most popular shows """
    import_tmdb()
    result = tmdb.TV().popular(page=page, language=LANG)
    return list_tvshows(result)
    
@plugin.cached_route('/tv/now_playing/<page>', TTL=CACHE_TTL)
def tv_now_playing(page):
    """ On the air shows """
    import_tmdb()
    result = tmdb.TV().on_the_air(page=page, language=LANG)
    return list_tvshows(result)

@plugin.cached_route('/tv/top_rated/<page>', TTL=CACHE_TTL)
def tv_top_rated(page):
    """ Top rated shows """
    import_tmdb()
    result = tmdb.TV().top_rated(page=page, language=LANG)
    return list_tvshows(result)

@plugin.route('/tv/trakt/collection')
def tv_trakt_collection():
    from trakt import trakt
    result = trakt.trakt_get_collection("shows")
    return list_trakt_tvshows(result)
    
@plugin.route('/tv/trakt/watchlist')
def tv_trakt_watchlist():
    from trakt import trakt
    result = trakt.trakt_get_watchlist("shows")
    return list_trakt_tvshows(result)

@plugin.route('/tv/trakt/collection_to_library')
def tv_trakt_collection_to_library():
    from trakt import trakt
    if dialogs.yesno(_("Add all to library"), _("Are you sure you want to add your entire Trakt collection to Kodi library?")):
        tv_add_all_to_library(trakt.trakt_get_collection("shows"))

@plugin.route('/tv/trakt/watchlist_to_library')
def tv_trakt_watchlist_to_library():
    from trakt import trakt
    if dialogs.yesno(_("Add all to library"), _("Are you sure you want to add your entire Trakt watchlist to Kodi library?")):
        tv_add_all_to_library(trakt.trakt_get_watchlist("shows"))
    
@plugin.route('/tv/trakt/next_episodes')
def tv_trakt_next_episodes():
    from trakt import trakt
    list = []
    result = trakt.trakt_get_next_episodes()
    for episode in result:
        trakt_id = episode["show"]["ids"]["trakt"]
        episode_info = trakt.get_episode(trakt_id, episode["season"], episode["number"])
        first_aired_string = episode_info["first_aired"]
        if first_aired_string:
            first_aired = time.mktime(time.strptime(first_aired_string[:19], "%Y-%m-%dT%H:%M:%S"))
            if first_aired < time.time():
                list.append(episode)
    return list_trakt_episodes(list)
    
@plugin.route('/tv/trakt/calendar')
def tv_trakt_calendar():
    from trakt import trakt
    result = trakt.trakt_get_calendar()
    return list_trakt_episodes(result, with_time=True)

@plugin.route('/tv/trakt/recommendations')
def tv_trakt_recommendations():
    from trakt import trakt
    genres_dict = trakt.trakt_get_genres("tv")
    shows = trakt.get_recommendations("shows")
    items = []
    for show in shows:
        items.append(make_tvshow_item(get_tvshow_metadata_trakt(show, genres_dict)))
    return items
    
@plugin.cached_route('/tv/genre/<id>/<page>', TTL=CACHE_TTL)
def tv_genre(id, page):
    """ Shows by genre """
    import_tmdb()
    result = tmdb.Discover().tv(with_genres=id, page=page, language=LANG)
    return list_tvshows(result)

@plugin.cached_route('/tv/genres', cache="genres")
def tv_genres():
    """ TV genres list """
    genres = get_tv_genres()
    return sorted([{ 'label': name,
              'icon': get_genre_icon(id),
              'path': plugin.url_for(tv_genre, id=id, page='1') } 
            for id, name in genres.items()], key=lambda k: k['label'])

@plugin.route('/tv/tvdb/<id>')
def tv_tvshow(id):
    """ All seasons of a TV show """
    plugin.set_content('seasons')
    return list_seasons_tvdb(id)

@plugin.route('/tv/tvdb/<id>/<season_num>')
def tv_season(id, season_num):
    """ All episodes of a TV season """
    plugin.set_content('episodes')
    return list_episodes_tvdb(id, season_num)

@plugin.route('/tv/set_library_player/<path>')
def set_library_player(path):
    # get active players
    players = active_players("tvshows")
    players.insert(0, ADDON_SELECTOR)
    players.insert(0, ADDON_DEFAULT)
    # let the user select one player
    selection = dialogs.select(_("Select default player"), [p.title for p in players])
    if selection == -1:
        return
    # get selected player
    player = players[selection]
    
    # Create play with file
    player_filepath = os.path.join(path, 'player.info')
    player_file = xbmcvfs.File(player_filepath, 'w')
    content = "{0}".format(player.id)
    player_file.write(content)
    player_file.close()
          
def tv_add_all_to_library(items):
    import_tvdb()    
    
    # setup library folder
    library_folder = setup_library(plugin.get_setting(SETTING_TV_LIBRARY_FOLDER))

    # add to library
    for item in items:
        ids = item["show"]["ids"]
        tvdb_id = ids.get('tvdb')
        if not tvdb_id:
            continue
        
        show = tvdb[int(tvdb_id)]
        if add_tvshow_to_library(library_folder, show, ADDON_DEFAULT.id):
            set_property("clean_library", 1)
        
    # start scan 
    scan_library()
          
@plugin.route('/tv/add_to_library/<id>')
def tv_add_to_library(id):
    import_tvdb()    
    show = tvdb[int(id)]
    
    # get active players
    players = active_players("tvshows", filters = {'network': show.get('network')})

    # add default and selector options
    players.insert(0, ADDON_SELECTOR)
    players.insert(0, ADDON_DEFAULT)

    # let the user select one player
    selection = dialogs.select(_("Play with..."), [p.title for p in players])
    if selection == -1:
        return
    
    # get selected player
    player = players[selection]
    
    # setup library folder
    library_folder = setup_library(plugin.get_setting(SETTING_TV_LIBRARY_FOLDER))

    # add to library
    if add_tvshow_to_library(library_folder, show, player.id):
        set_property("clean_library", 1)
        
    # start scan 
    scan_library()
    
@plugin.route('/tv/play/<id>/<season>/<episode>/<mode>')
def tv_play(id, season, episode, mode):  
    play_episode(id, season, episode, mode)
    
def list_tvshows(response):
    """ TV shows listing """
    import_tvdb()
        
    # Attach TVDB data to TMDB results
    items = []
    results = response['results']
    for tvdb_show, tmdb_show in execute(tmdb_to_tvdb, results, workers=10):
        if tvdb_show is not None:
            info = build_tvshow_info(tvdb_show, tmdb_show)
            items.append(make_tvshow_item(info))
    
    if xbmc.abortRequested:
        return

    # Paging
    if 'page' in response:
        page = response['page']
        args = caller_args()
        if page < response['total_pages']:
            args['page'] = str(page + 1)
            items.append({
                'label': _("Next >>"),
                'icon': get_icon_path("item_next"),
                'path': plugin.url_for(caller_name(), **args)
            })
    
    return items
    
def trakt_get_genres():
    from trakt import trakt
    genres_dict = dict([(x['slug'], x['name']) for x in trakt.trakt_get_genres("movies")])
    genres_dict.update(dict([(x['slug'], x['name']) for x in trakt.trakt_get_genres("shows")]))
    return genres_dict
    
def list_trakt_tvshows(results):
    from trakt import trakt
    
    results = sorted(results,key=lambda item: item["show"]["title"].lower().replace("the ", ""))
    
    genres_dict = trakt_get_genres()
    
    shows = [get_tvshow_metadata_trakt(item["show"], genres_dict) for item in results]
    items = [make_tvshow_item(show) for show in shows if show.get('tvdb_id')]
    return items

def list_trakt_episodes(result, with_time=False):    
    genres_dict = trakt_get_genres()
    
    items = []
    for item in result:
        if 'episode' in item:
            episode = item['episode']
        else:
            episode = item
            
        id = episode["ids"].get("tvdb")
        if not id:
            continue
        
        season_num = episode["season"]
        episode_num = episode["number"]
        
        info = get_tvshow_metadata_trakt(item["show"], genres_dict)
        info['season'] = episode["season"] 
        info['episode'] = episode["number"]
        info['title'] = episode["title"]
        info['aired'] = episode.get('first_aired','')
        info['premiered'] = episode.get('first_aired','')
        info['rating'] = episode.get('rating', '')
        info['plot'] = episode.get('overview','')
        info['tagline'] = episode.get('tagline')
        info['votes'] = episode.get('votes','')
        #info['poster'] = episode['images']['poster']['thumb']

        label = "{0} - S{1:02d}E{2:02d} - {3}".format(item["show"]["title"], season_num, episode_num, episode["title"])

        if with_time and info['premiered']:
            airtime = time.strptime(item["first_aired"], "%Y-%m-%dt%H:%M:%S.000Z")
            airtime = time.strftime("%Y-%m-%d %H:%M", airtime)
            label = "{0}\n{1}".format(label, airtime)
            
        context_menu = [
             (
              _("Select stream..."),
              "PlayMedia({0})".format(plugin.url_for("tv_play", id=id, season=season_num, episode=episode_num, mode='select'))
             ),
             (
              _("Show info"),
              'Action(Info)'
             ),
             (
              _("Add to list"),
              "RunPlugin({0})".format(plugin.url_for("lists_add_episode_to_list", src='tvdb', id=id,
                                                     season=season_num, episode=episode_num))
             ),
        ]
        
        items.append({'label': label,
                      'path': plugin.url_for("tv_play", id=id, season=season_num, episode=episode_num, mode='default'),
                      'context_menu': context_menu,
                      'info': info,
                      'is_playable': True,
                      'info_type': 'video',
                      'stream_info': {'video': {}},
                      'thumbnail': info['poster'],
                      'poster': info['poster'],
                      'icon': "DefaultVideo.png",
                      'properties' : {'fanart_image' : info['fanart']},
                      })
        
    plugin.set_content('episodes')
    return items
    
def build_tvshow_info(tvdb_show, tmdb_show=None):
    tvdb_info = get_tvshow_metadata_tvdb(tvdb_show)
    tmdb_info = get_tvshow_metadata_tmdb(tmdb_show)
    
    info = {}
    info.update(tvdb_info)
    info.update(dict((k,v) for k,v in tmdb_info.iteritems() if v))
    
    # Prefer translated info
    if LANG != "en":
        for key in ('name', 'title', 'plot'):
            if is_ascii(info.get(key,'')) and not is_ascii(tvdb_info.get(key,'')):
                info[key] = tvdb_info[key]
    return info
    
def make_tvshow_item(info):                        
    tvdb_id = info['tvdb_id']
    
    context_menu = [
     (   
      _("Add to library"),
      "RunPlugin({0})".format(plugin.url_for("tv_add_to_library", id=tvdb_id))
     ),
     (
      _("Show info"), 'Action(Info)'
     ),
     (
      _("Add to list"),
      "RunPlugin({0})".format(plugin.url_for("lists_add_show_to_list", src='tvdb', id=tvdb_id,))
     )
    ]
             
    return {'label': info['title'],
            'path': plugin.url_for("tv_tvshow", id=tvdb_id),
            'context_menu': context_menu,
            'thumbnail': info['poster'],
            'icon': "DefaultVideo.png",
            'poster': info['poster'],
            'properties' : {'fanart_image' : info['fanart']},
            'info_type': 'video',
            'stream_info': {'video': {}},
            'info': info}
    
@plugin.cached(TTL=CACHE_TTL)
def list_seasons_tvdb(id):
    import_tvdb()
    id = int(id)
    
    show = tvdb[id]
    show_info = get_tvshow_metadata_tvdb(show, banners=False)
    

    
    items = []
    for (season_num, season) in show.items():
        if season_num == 0 or not season.has_aired(flexible=True):
            continue
        
        season_info = get_season_metadata_tvdb(show_info, season)

        context_menu = [
            (
                _("Show info"), 'Action(Info)'
            ),
            (
                _("Add to list"),
                "RunPlugin({0})".format(plugin.url_for("lists_add_season_to_list",
                                                       src='tvdb', id=id, season=season_num))
            )
        ]
        
        items.append({'label': u"%s %d" % (_("Season"), season_num),
                      'path': plugin.url_for(tv_season, id=id, season_num=season_num),
                      'context_menu': context_menu,
                      'info': season_info,
                      'thumbnail': season_info['poster'],
                      'icon': "DefaultVideo.png",
                      'poster': season_info['poster'],
                      'properties' : {'fanart_image' : season_info['fanart']},
                      })
    return items
    
@plugin.cached(TTL=CACHE_TTL)
def list_episodes_tvdb(id, season_num):
    import_tvdb()
    id = int(id)
    season_num = int(season_num)

    show = tvdb[id]
    show_info = get_tvshow_metadata_tvdb(show, banners=False)

    season = show[season_num]
    season_info = get_season_metadata_tvdb(show_info, season, banners=True)
    
    items = []
    for (episode_num, episode) in season.items():
        if episode_num == 0 or not episode.has_aired(flexible=True):
            break
        
        episode_info = get_episode_metadata_tvdb(season_info, episode)
                        
        context_menu = [
         (
          _("Select stream..."),
          "PlayMedia({0})".format(plugin.url_for("tv_play", id=id, season=season_num, episode=episode_num, mode='select'))
         ),
         (
          _("Show info"),
          'Action(Info)'
         ),
         (
          _("Add to list"),
          "RunPlugin({0})".format(plugin.url_for("lists_add_episode_to_list", src='tvdb', id=id,
                                                 season=season_num, episode = episode_num))
         ),
        ]
        
        items.append({'label': episode_info.get('title'),
                      'path': plugin.url_for("tv_play", id=id, season=season_num, episode=episode_num, mode='default'),
                      'context_menu': context_menu,
                      'info': episode_info,
                      'is_playable': True,
                      'info_type': 'video',
                      'stream_info': {'video': {}},
                      'thumbnail': episode_info['poster'],
                      'poster': season_info['poster'],
                      'icon': "DefaultVideo.png",
                      'properties' : {'fanart_image' : episode_info['fanart']},
                      })

    return items

def get_tvshow_metadata_tmdb(tmdb_show):
    info = {}

    if tmdb_show is None:
        return info
        
    genres = get_genres()
    
    info['tmdb'] = str(tmdb_show['id'])
    info['name'] = tmdb_show['name']
    info['title'] = tmdb_show['name']
    info['tvshowtitle'] = tmdb_show['original_name']
    info['originaltitle'] = tmdb_show['original_name']
    info['genre'] = u" / ".join([genres[x] for x in tmdb_show['genre_ids'] if x in genres])
    info['plot'] = tmdb_show['overview']
    info['rating'] = str(tmdb_show['vote_average'])
    info['votes'] = str(tmdb_show['vote_count'])
    
    
    if tmdb_show['poster_path']:
        info['poster'] = u'%s%s' % ("http://image.tmdb.org/t/p/w500", tmdb_show['poster_path'])
    else:
        info['poster'] = ''
    
    if tmdb_show['backdrop_path']:
        info['fanart'] = u'%s%s' % ("http://image.tmdb.org/t/p/original", tmdb_show['backdrop_path'])    
    else:
        info['fanart'] = ''
        
    return info
    
def tmdb_to_tvdb(tmdb_show):
    tvdb_show = None
        
    # Search by name and year
    name = tmdb_show['original_name']
    year = int(parse_year(tmdb_show['first_air_date']))
    results = [x['id'] for x in tvdb.search(name, year)]
    
    # Get by id if not a single result
    if len(results) != 1:        
        id = tmdb.TV(tmdb_show['id']).external_ids().get('tvdb_id', None)
        if id:
            results = [id]
    
    # Use first result if still have many
    if results:
        tvdb_show = tvdb[results[0]]
        
    return tvdb_show, tmdb_show
