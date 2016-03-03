import copy

from xbmcswift2 import xbmc

from meta import plugin, import_tmdb, LANG
from meta.info import get_movie_metadata
from meta.utils.text import parse_year, date_to_timestamp
from meta.play.movies import play_movie
from meta.library.movies import setup_library, add_movie_to_library
from meta.library.tools import scan_library
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_base_genres, caller_name, caller_args
from language import get_string as _
from settings import CACHE_TTL, SETTING_MOVIES_LIBRARY_FOLDER


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
            'icon': get_icon_path("movies"),
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
    ]

    fanart = plugin.addon.getAddonInfo('fanart')
    for item in items:
        item['properties'] = {'fanart_image' : fanart}
        
    return items

@plugin.route('/movies/search')
def movies_search():
    """ Activate movie search """
    search(movies_search_term)

@plugin.route('/movies/search_term/<term>/<page>')
def movies_search_term(term, page):
    """ Perform search of a specified <term>"""
    import_tmdb()
    result = tmdb.Search().movie(query=term, language = LANG, page = page)
    return list_movies(result)

@plugin.cached_route('/movies/most_popular/<page>', TTL=CACHE_TTL)
def movies_most_popular(page):
    """ Most popular movies """
    import_tmdb()    
    result = tmdb.Movies().popular(language=LANG, page=page)
    return list_movies(result)

@plugin.cached_route('/movies/now_playing/<page>', TTL=CACHE_TTL)
def movies_now_playing(page):
    import_tmdb()
    result = tmdb.Movies().now_playing(language=LANG, page=page)    
    return list_movies(result)

@plugin.cached_route('/movies/top_rated/<page>', TTL=CACHE_TTL)
def movies_top_rated(page):
    import_tmdb()    
    result = tmdb.Movies().top_rated(language=LANG, page=page)
    return list_movies(result)

@plugin.cached_route('/movies/blockbusters/<page>', TTL=CACHE_TTL)
def movies_blockbusters(page):
    import_tmdb()
    result = tmdb.Discover().movie(language=LANG, **{'page': page, 'sort_by': 'revenue.desc'})   
    return list_movies(result)

@plugin.cached_route('/movies/genre/<id>/<page>', TTL=CACHE_TTL)
def movies_genre(id, page):
    """ Movies by genre id """
    import_tmdb()
    result = tmdb.Genres(id).movies(id=id, language=LANG, page=page)
    return list_movies(result)
    
@plugin.route('/movies/genres')
def movies_genres():
    """ List all movie genres """
    genres = get_base_genres()
    return sorted([{ 'label': name,
              'icon': get_genre_icon(id),
              'path': plugin.url_for(movies_genre, id=id, page='1') } 
            for id, name in genres.items()], key=lambda k: k['label'])

@plugin.route('/movies/add_to_library/<id>')
def movies_add_to_library(id):
    """ Add movie to library """
    library_folder = setup_library(plugin.get_setting(SETTING_MOVIES_LIBRARY_FOLDER))

    # TODO: we actually prefer tmdb...
    
    import_tmdb()
    movie = tmdb.Movies(id).info()
    imdb_id = movie.get('imdb_id')
    date = date_to_timestamp(movie.get('release_date'))
    if imdb_id:
        add_movie_to_library(library_folder, "imdb", imdb_id, date)
    else:
        add_movie_to_library(library_folder, "tmdb", id, date)
    
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

def list_movies(result):
    genres_dict = get_base_genres()
        
    items = [make_movie_item(get_movie_metadata(item, genres_dict)) \
                for item in result['results']]
        
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
    
    
def make_movie_item(movie_info):

    tmdb_id = movie_info['tmdb']
    
    context_menu = [
     (
       _("Select stream..."),
       "PlayMedia({0})".format(plugin.url_for("movies_play", src='tmdb', id=tmdb_id, mode='select'))
     ),                
     (
      _("Add to library"), 
      "RunPlugin({0})".format(plugin.url_for("movies_add_to_library", id=tmdb_id))
     ),
     (
      _("Show info"),
      'Action(Info)'
     ),
    ]
    
    return {'label': movie_info['title'],
            'path': plugin.url_for("movies_play", src='tmdb', id=tmdb_id, mode='default'),
            'context_menu': context_menu,
            'thumbnail': movie_info['poster'],
            'icon': "DefaultVideo.png",
            'poster': movie_info['poster'],
            'properties' : {'fanart_image' : movie_info['fanart']},
            'is_playable': True,
            'info_type': 'video',
            'info': movie_info}
