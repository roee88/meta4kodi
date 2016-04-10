import copy

from xbmcswift2 import xbmc, xbmcplugin

from meta import plugin, import_tmdb, LANG
from meta.info import get_movie_metadata, get_trakt_movie_metadata
from meta.gui import dialogs
from meta.utils.text import parse_year, date_to_timestamp, to_utf8
from meta.play.movies import play_movie
from meta.library.movies import setup_library, add_movie_to_library
from meta.library.tools import scan_library
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_base_genres, caller_name, caller_args
from language import get_string as _
from settings import CACHE_TTL, SETTING_MOVIES_LIBRARY_FOLDER


MOVIE_SORT_METHODS = [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL, xbmcplugin.SORT_METHOD_DATE, xbmcplugin.SORT_METHOD_VIDEO_YEAR]

@plugin.route('/movies')
def movies():
    """ Movies directory """
    items = [
        {
            'label': _("Search"),
            'path': plugin.url_for(movies_search),
            'icon': get_icon_path("search"),
        },
        {
            'label': _("Genres"),
            'path': plugin.url_for(movies_genres),
            'icon': get_icon_path("genres"),
        },
        {
            'label': _("Popular"),
            'path': plugin.url_for(movies_most_popular, page='1'),
            'icon': get_icon_path("popular"),
        },
        {
            'label': _("In theatres"),
            'path': plugin.url_for(movies_now_playing, page='1'),
            'icon': get_icon_path("intheatres"),
        },
        {
            'label': _("Top rated"),
            'path': plugin.url_for(movies_top_rated, page='1'),
            'icon': get_icon_path("top_rated"),
        },
        {
            'label': _("Blockbusters"),
            'path': plugin.url_for(movies_blockbusters, page='1'),
            'icon': get_icon_path("most_voted"),
        },
        {
            'label': _("Trakt collection"),
            'path': plugin.url_for(movies_trakt_collection),
            'icon': get_icon_path("traktcollection"),
            'context_menu': [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for(movies_trakt_collection_to_library))
                )
            ],
        },
        {
            'label': _("Trakt watchlist"),
            'path': plugin.url_for(movies_trakt_watchlist),
            'icon': get_icon_path("traktwatchlist"),
            'context_menu': [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for(movies_trakt_watchlist_to_library))
                )
            ],
        },
        {
            'label': _("Trakt recommendations"),
            'path': plugin.url_for(movies_trakt_recommendations),
            'icon': get_icon_path("traktrecommendations"),
        },
    ]

    fanart = plugin.addon.getAddonInfo('fanart')
    for item in items:
        item['properties'] = {'fanart_image' : fanart}
        
    return items

@plugin.route('/movies/search')
def movies_search():
    """ Activate movie search """
    search(movies_search_term)

@plugin.route('/movies/play_by_name/<name>/<lang>')
def movies_play_by_name(name, lang = "en"):
    """ Activate tv search """
    import_tmdb()
    from meta.utils.text import parse_year

    items = tmdb.Search().movie(query=name, language=lang, page=1)["results"]

    if items == []:
        dialogs.ok(_("Movie not found"), "{0} {1}".format(_("No movie information found on TMDB for"),name))
        return

    if len(items) > 1:
        selection = dialogs.select(_("Choose Movie"), ["{0} ({1})".format(
            to_utf8(s["title"]),
            parse_year(s["release_date"])) for s in items])
    else:
        selection = 0
    if selection != -1:
        id = items[selection]["id"]
        movies_play("tmdb", id, "default")

@plugin.route('/movies/search_term/<term>/<page>')
def movies_search_term(term, page):
    """ Perform search of a specified <term>"""
    import_tmdb()
    result = tmdb.Search().movie(query=term, language = LANG, page = page)
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/most_popular/<page>')
def movies_most_popular(page):
    """ Most popular movies """
    import_tmdb()    
    result = tmdb.Movies().popular(language=LANG, page=page)
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/now_playing/<page>')
def movies_now_playing(page):
    import_tmdb()
    result = tmdb.Movies().now_playing(language=LANG, page=page)    
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/top_rated/<page>')
def movies_top_rated(page):
    import_tmdb()    
    result = tmdb.Movies().top_rated(language=LANG, page=page)
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/blockbusters/<page>')
def movies_blockbusters(page):
    import_tmdb()
    result = tmdb.Discover().movie(language=LANG, **{'page': page, 'sort_by': 'revenue.desc'})   
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/genre/<id>/<page>')
def movies_genre(id, page):
    """ Movies by genre id """
    import_tmdb()
    result = tmdb.Genres(id).movies(id=id, language=LANG, page=page)
    return plugin.finish(list_tmdb_movies(result), sort_methods=MOVIE_SORT_METHODS)
    
@plugin.route('/movies/genres')
def movies_genres():
    """ List all movie genres """
    genres = get_base_genres()
    return sorted([{ 'label': name,
              'icon': get_genre_icon(id),
              'path': plugin.url_for(movies_genre, id=id, page='1') } 
            for id, name in genres.items()], key=lambda k: k['label'])

@plugin.route('/movies/trakt/collection')
def movies_trakt_collection():
    from trakt import trakt
    result = trakt.trakt_get_collection("movies")
    return plugin.finish(list_trakt_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/trakt/watchlist')
def movies_trakt_watchlist():
    from trakt import trakt
    result = trakt.trakt_get_watchlist("movies")
    return plugin.finish(list_trakt_movies(result), sort_methods=MOVIE_SORT_METHODS)

@plugin.route('/movies/trakt/recommendations')
def movies_trakt_recommendations():
    from trakt import trakt
    genres_dict = dict([(x['slug'], x['name']) for x in trakt.trakt_get_genres("movies")])
    movies = trakt.get_recommendations("movies")
    items = []
    for movie in movies:
        items.append(make_movie_item(get_trakt_movie_metadata(movie, genres_dict)))
    return items
    
@plugin.route('/movies/trakt/collection_to_library')
def movies_trakt_collection_to_library():
    from trakt import trakt
    if dialogs.yesno(_("Add all to library"), _("Are you sure you want to add your entire Trakt collection to Kodi library?")):
        movies_add_all_to_library(trakt.trakt_get_collection("movies"))

@plugin.route('/movies/trakt/watchlist_to_library')
def movies_trakt_watchlist_to_library():
    from trakt import trakt
    if dialogs.yesno(_("Add all to library"), _("Are you sure you want to add your entire Trakt watchlist to Kodi library?")):
        movies_add_all_to_library(trakt.trakt_get_watchlist("movies"))
        
def movies_add_all_to_library(items):
    library_folder = setup_library(plugin.get_setting(SETTING_MOVIES_LIBRARY_FOLDER))
    
    for item in items:
        ids = item["movie"]["ids"]
        if ids.get('imdb'):
            add_movie_to_library(library_folder, "imdb", ids["imdb"], None)
        elif ids.get('tmdb'):
            add_movie_to_library(library_folder, "tmdb", ids["tmdb"], None)
        else:
            plugin.log.error("movie %s is missing both imdb and tmdb ids" % ids['slug'])
            
    scan_library()
                
@plugin.route('/movies/add_to_library/<src>/<id>')
def movies_add_to_library(src, id):
    """ Add movie to library """
    library_folder = setup_library(plugin.get_setting(SETTING_MOVIES_LIBRARY_FOLDER))

    date = None
    if src == "tmdb":
        import_tmdb()

        movie = tmdb.Movies(id).info()
        date = date_to_timestamp(movie.get('release_date'))
        imdb_id = movie.get('imdb_id')
        if imdb_id:
            src = "imdb"
            id = imdb_id
    
    add_movie_to_library(library_folder, src, id, date)   
    scan_library()

@plugin.route('/movies/play/<src>/<id>/<mode>')
def movies_play(src, id, mode="external"):
    import_tmdb()

    tmdb_id = None
    if src == "tmdb":
        tmdb_id = id
    elif src == "imdb":
        info = tmdb.Find(id).info(external_source="imdb_id")
        try:
            tmdb_id = info["movie_results"][0]["id"]
        except (KeyError, TypeError):
            pass
            
    if tmdb_id:
        play_movie(tmdb_id, mode)
    else:
        plugin.set_resolved_url()

def list_tmdb_movies(result):
    genres_dict = get_base_genres()
    movies = [get_movie_metadata(item, genres_dict) for item in result['results']]
    items = [make_movie_item(movie) for movie in movies]
    
    if 'page' in result:
        page = result['page']
        args = caller_args()
        if page < result['total_pages']:
            args['page'] = str(page + 1)
            items.append({
                'label': _("Next >>"),
                'icon': get_icon_path("item_next"),
                'path': plugin.url_for(caller_name(), **args)
            })

    return items
    
def list_trakt_movies(results):
    from trakt import trakt
    
    results = sorted(results,key=lambda item: item["movie"]["title"].lower().replace("the ", ""))
    
    genres_dict = dict([(x['slug'], x['name']) for x in trakt.trakt_get_genres("movies")])
    movies = [get_trakt_movie_metadata(item["movie"], genres_dict) for item in results]
    items = [make_movie_item(movie) for movie in movies]
    return items
    
def make_movie_item(movie_info, is_list = False):

    tmdb_id = movie_info.get('tmdb')
    imdb_id = movie_info.get('imdb')
    
    if tmdb_id:
        id = tmdb_id 
        src = 'tmdb'
    else:
        id = imdb_id 
        src = 'imdb'
    
    context_menu = [
     (
       _("Select stream..."),
       "PlayMedia({0})".format(plugin.url_for("movies_play", src=src, id=id, mode='select'))
     ),                
     (
      _("Add to library"), 
      "RunPlugin({0})".format(plugin.url_for("movies_add_to_library", src=src, id=id))
     ),
     (
      _("Add to list"),
      "RunPlugin({0})".format(plugin.url_for("lists_add_movie_to_list", src=src, id=id))
     ),
     (
      _("Show info"),
      'Action(Info)'
     ),
    ]

    if is_list:
        context_menu.append(
            (
                _("Remove from list"),
                "RunPlugin({0})".format(plugin.url_for("lists_remove_movie_from_list", src=src, id=id))
            )
        )

    
    return {
        'label': movie_info['title'],
        'path': plugin.url_for("movies_play", src=src, id=id, mode='default'),
        'context_menu': context_menu,
        'thumbnail': movie_info['poster'],
        'icon': "DefaultVideo.png",
        'poster': movie_info['poster'],
        'properties' : {'fanart_image' : movie_info['fanart']},
        'is_playable': True,
        'info_type': 'video',
        'stream_info': {'video': {}},
        'info': movie_info
    }
