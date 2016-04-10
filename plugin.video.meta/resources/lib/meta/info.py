import re
import copy
from meta import LANG
from meta.utils.text import parse_year

def get_movie_metadata(movie, genres_dict=None):        
    info = {}
    
    info['title'] = movie['title']
    info['year'] = parse_year(movie['release_date'])
    info['name'] = u'%s (%s)' % (info['title'], info['year'])

    info['premiered'] = movie['release_date']
    info['rating'] = movie['vote_average']
    info['votes'] = movie['vote_count']
    info['plot'] = movie['overview']
    
    info['originaltitle'] = movie['original_title']
    info['tmdb'] = str(movie['id'])
    
    info['poster'] = u'%s%s' % ("http://image.tmdb.org/t/p/w500", movie['poster_path'])
    info['fanart'] = u'%s%s' % ("http://image.tmdb.org/t/p/original", movie['backdrop_path'])    

    try:
        info['genre'] = u" / ".join([x['name'] for x in movie['genres']])
    except KeyError:
        if genres_dict:
            info['genre'] = u" / ".join([genres_dict[x] for x in movie['genre_ids']])
        else:
            info['genre'] = ''
        
    return info

def get_trakt_movie_metadata(movie, genres_dict=None):
    info = {}
    
    info['title'] = movie['title']
    info['year'] = movie['year']
    info['name'] = u'%s (%s)' % (info['title'], info['year'])

    info['premiered'] = movie.get('released')
    info['rating'] = movie.get('rating')
    info['votes'] = movie.get('votes')
    info['tagline'] = movie.get('tagline')
    info['plot'] = movie.get('overview')
    info['duration'] = 60 * (movie.get('runtime') or 0)
    info['mpaa'] = movie.get('certification')
    info['playcount'] = movie.get('plays')
    if not info['playcount'] and movie.get('watched'):
        info['playcount'] = 1
    info['tmdb'] = movie['ids'].get('tmdb')
    info['trakt_id'] = movie['ids'].get('trakt_id')
    info['imdb_id'] = movie['ids'].get('imdb')

    info['poster'] = movie['images']['poster']['thumb']
    info['fanart'] = movie['images']['fanart']['medium']    

    if genres_dict:
        info['genre'] = u" / ".join([genres_dict[x] for x in movie['genres']])

    if movie.get('trailer'):
        info['trailer'] = make_trailer(movie['trailer'])
            
    return info

def make_trailer(trailer_url):
    match = re.search('\?v=(.*)', trailer_url)
    if match:
        return 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % (match.group(1))
    
def get_tvshow_metadata_trakt(show, genres_dict):
    info = {}

    info['title'] = show['title']
    info['year'] = show['year']
    info['name'] = u'%s (%s)' % (info['title'], info['year'])

    info['tvshowtitle'] = info['title']

    info['premiered'] = show.get('released')
    info['rating'] = show.get('rating')
    info['votes'] = show.get('votes')
    info['tagline'] = show.get('tagline')
    info['plot'] = show.get('overview')
    info['duration'] = 60 * (show.get('runtime') or 0)
    info['studio'] = show.get('network','')
    info['mpaa'] = show.get('certification')
    info['playcount'] = show.get('plays')
    if not info['playcount'] and show.get('watched'):
        info['playcount'] = 1
    info['tmdb'] = show['ids'].get('tmdb')
    info['trakt_id'] = show['ids'].get('trakt_id')
    info['imdb_id'] = show['ids'].get('imdb')
    info['tvdb_id'] = show['ids'].get('tvdb')

    info['poster'] = show['images']['poster']['thumb']
    info['fanart'] = show['images']['fanart']['medium']

    if genres_dict:
        info['genre'] = u" / ".join([genres_dict[x] for x in show['genres']])

    if show.get('trailer'):
        info['trailer'] = make_trailer(show['trailer'])

    return info

def get_tvshow_metadata_tvdb(tvdb_show, banners=True):
    info = {}
    
    if tvdb_show is None:
        return info

    info['tvdb_id'] = str(tvdb_show['id'])
    info['name'] = tvdb_show['seriesname']
    info['title'] = tvdb_show['seriesname']
    info['tvshowtitle'] = tvdb_show['seriesname']
    info['originaltitle'] = tvdb_show['seriesname']
    #info['genre'] = 
    info['plot'] = tvdb_show.get('overview', '')
    if banners:
        info['poster'] = tvdb_show.get_poster(language=LANG)
    info['fanart'] = tvdb_show.get('fanart', '')
    info['rating'] = tvdb_show.get('rating')
    info['votes'] = tvdb_show.get('ratingcount')
    info['year'] = tvdb_show.get('year', 0)
    info['studio'] = tvdb_show.get('network','')
    info['imdb_id'] = tvdb_show.get('imdb_id', '')
            
    return info

def get_season_metadata_tvdb(show_metadata, season, banners=True):
    info = copy.deepcopy(show_metadata)
    
    del info['title']
    
    info['season'] = season.num    
    if banners:
        info['poster'] = season.get_poster(language=LANG)

    return info

def get_season_metadata_trakt(show_metadata, season, banners=True):
    info = copy.deepcopy(show_metadata)

    del info['title']

    info['season'] = season["number"]
    if banners:
        info['poster'] = season["images"]["poster"]["thumb"]

    return info

def get_episode_metadata_tvdb(season_metadata, episode, banners=True):
    info = copy.deepcopy(season_metadata)
    
    info['episode'] = episode.get('episodenumber')
    info['title'] = episode.get('episodename','')
    info['aired'] = episode.get('firstaired','')
    info['premiered'] = episode.get('firstaired','')
    info['rating'] = episode.get('rating', '')
    info['plot'] = episode.get('overview','')
    info['plotoutline'] = episode.get('overview','')
    info['votes'] = episode.get('ratingcount','')
        
    if banners:
        info['poster'] = episode['filename']
        
    return info

def get_episode_metadata_trakt(show_metadata, episode, banners=True):
    info = copy.deepcopy(show_metadata)

    info['episode'] = episode.get('number')
    info['title'] = episode.get('title','')
    info['aired'] = episode.get('first_aired','')
    info['premiered'] = episode.get('first_aired','')
    info['rating'] = episode.get('rating', '')
    info['plot'] = episode.get('overview','')
    info['plotoutline'] = episode.get('overview','')
    info['votes'] = episode.get('votes','')

    if banners:
        info['poster'] = episode['images']['screenshot']["thumb"]

    return info
