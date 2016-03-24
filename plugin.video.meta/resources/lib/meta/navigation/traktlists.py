from meta import plugin
from meta.gui import dialogs
from meta.navigation.base import search, get_icon_path, get_genre_icon, get_genres, get_tv_genres, caller_name, caller_args, get_base_genres
from meta.navigation.movies import movies_search_term
from trakt.trakt import trakt_get_collection, trakt_get_watchlist, trakt_get_calendar
import time

@plugin.route('/trakt')
def trakt():
    """ Trakt directory """
    items = [
        {
            'label': "Collections",
            'path': plugin.url_for(trakt_collections),
        },
        {
            'label': "Watchlists",
            'path': plugin.url_for(trakt_watchlists),
        },
        {
            'label': "My Calendar",
            'path': plugin.url_for(trakt_calendar),
        },
    ]

    fanart = plugin.addon.getAddonInfo('fanart')
    for item in items:
        item['properties'] = {'fanart_image' : fanart}

    return items

@plugin.route('/trakt/collections')
def trakt_collections():
    items = [
        {
            'label': "Movie Collection",
            'path': plugin.url_for(trakt_movie_collection),
        },
        {
            'label': "TV Collection",
            'path': plugin.url_for(trakt_tv_collection),
        },
    ]

    return items


@plugin.route('/trakt/watchlists')
def trakt_watchlists():
    items = [
        {
            'label': "Movie Watchlist",
            'path': plugin.url_for(trakt_movie_watchlist),
        },
        {
            'label': "TV Watchlist",
            'path': plugin.url_for(trakt_tv_watchlist),
        },
    ]

    return items

@plugin.route('/trakt/movie_collection')
def trakt_movie_collection():
    movies = trakt_get_collection("movies")
    movies = sorted(movies, key=lambda k: k["movie"]["title"])
    items = []
    for item in movies:
        movie = item["movie"]
        items.append({'label': movie["title"],
                      'path': "plugin://plugin.video.meta/movies/play/imdb/" + str(movie["ids"]["imdb"]) + "/select"
        })

    return items

@plugin.route('/trakt/tv_collection')
def trakt_tv_collection():
    shows = trakt_get_collection("shows")
    shows = sorted(shows, key=lambda k: k["show"]["title"])
    items = []
    for item in shows:
        show = item["show"]
        items.append({'label': show["title"],
                      'path': "plugin://plugin.video.meta/tv/tvdb/" + str(show["ids"]["tvdb"])
        })

    return items

@plugin.route('/trakt/movie_watchlist')
def trakt_movie_watchlist():
    movies = trakt_get_watchlist("movies")
    movies = sorted(movies, key=lambda k: k["movie"]["title"])
    items = []
    for item in movies:
        movie = item["movie"]
        items.append({'label': movie["title"],
                      'path': "plugin://plugin.video.meta/movies/play/imdb/" + str(movie["ids"]["imdb"]) + "/select"
        })

    return items

@plugin.route('/trakt/tv_watchlist')
def trakt_tv_watchlist():
    shows = trakt_get_watchlist("shows")
    shows = sorted(shows, key=lambda k: k["show"]["title"])
    items = []
    for item in shows:
        show = item["show"]
        items.append({'label': show["title"],
                      'path': "plugin://plugin.video.meta/tv/tvdb/" + str(show["ids"]["tvdb"])
        })

    return items

@plugin.route('/trakt/calendar')
def trakt_calendar():
    shows = trakt_get_calendar()
    items = []
    for item in shows:
        show = item["show"]
        episode = item["episode"]
        season = episode["season"]
        number = episode["number"]
        episode_title = episode["title"]
        episode_name = "{0} - S{1}E{2} - {3}".format(show["title"], season, number, episode_title)
        airtime = time.strptime(item["first_aired"], "%Y-%m-%dt%H:%M:%S.000Z")
        airtime = time.strftime("%Y-%m-%d %H:%M", airtime)
        items.append({'label': "{0}\n{1}".format(episode_name,airtime),
                      'path': "plugin://plugin.video.meta/tv/play/{0}/{1}/{2}/default".format(show["ids"]["tvdb"],season,episode)
        })

    return items
