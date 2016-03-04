import copy
from meta import LANG
from meta.utils.text import parse_year

def get_movie_metadata(movie, genres_dict=None):        
    info = {}
    
    info['title'] = movie['title']
    info['originaltitle'] = movie['original_title']
    info['year'] = parse_year(movie['release_date'])
    info['name'] = u'%s (%s)' % (info['title'], info['year'])
    info['tmdb'] = str(movie['id'])
    info['poster'] = u'%s%s' % ("http://image.tmdb.org/t/p/w500", movie['poster_path'])
    info['fanart'] = u'%s%s' % ("http://image.tmdb.org/t/p/original", movie['backdrop_path'])    
    info['rating'] = str(movie['vote_average'])
    info['votes'] = str(movie['vote_count'])
    info['plot'] = movie['overview']
    

    try:
        info['genre'] = u" / ".join([x['name'] for x in movie['genres']])
    except KeyError:
        if genres_dict:
            info['genre'] = u" / ".join([genres_dict[x] for x in movie['genre_ids']])
        else:
            info['genre'] = ''
        
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
    
    info['season'] = season.num    
    if banners:
        info['poster'] = season.get_poster(language=LANG)

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
