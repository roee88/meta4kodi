import os
import json
import urllib

from xbmcswift2 import xbmc, xbmcvfs

from meta import plugin, import_tmdb, LANG
from meta.utils.text import date_to_timestamp
from meta.library.tools import scan_library, add_source
from meta.utils.rpc import RPC
from meta.gui import dialogs

from language import get_string as _
from settings import SETTING_MOVIES_SERVER_URL, SETTING_MOVIES_LIBRARY_FOLDER, SETTING_LIBRARY_SET_DATE

@plugin.cached(TTL=60*2)
def query_movies_server(url):
    response = urllib.urlopen(url)
    return json.loads(response.read())

def update_library():
    """ Update library """
    url = plugin.get_setting(SETTING_MOVIES_SERVER_URL, converter=str)
    if not url:
        return
    
    # Get movies list from movies-server
    movies = query_movies_server(url)
    
    # setup library folder
    library_folder = setup_library(plugin.get_setting(SETTING_MOVIES_LIBRARY_FOLDER))

    changed = False

    # add new movies
    for movie in movies:
        date = int(movie.get('date', 0))
        imdb = movie.get('imdb')
        tmdb = movie.get('tmdb')
        
        if imdb:
            if add_movie_to_library(library_folder, "imdb", imdb, date):
                changed = True
        elif tmdb:
            if add_movie_to_library(library_folder, "tmdb", tmdb, date):
                changed = True
        
    # remove old movies from DB
    keep_movies = [movie['imdb'] for movie in movies]
    
    db_movies = RPC.video_library.get_movies(properties=['title', 'imdbnumber','file'])    
    for movie in db_movies.get('movies', []):
        file = xbmc.translatePath(movie['file'])
        imdb = os.path.splitext(os.path.basename(file))[0]
        if imdb not in keep_movies and plugin.id in file:
            
            # remove movie
            RPC.video_library.remove_movie(movieid=movie["movieid"])
            
            # remove strm and nfo files
            os.remove(file)
            try:
                os.remove(file.replace(".strm", ".nfo"))
            except:
                pass
            
            changed = True
    
    if changed:
        scan_library()

def add_movie_to_library(library_folder, src, id, date):    
    changed = False
    
    # create nfo file
    nfo_filepath = os.path.join(library_folder, str(id)+".nfo")
    if not xbmcvfs.exists(nfo_filepath):
        changed = True
        nfo_file = xbmcvfs.File(nfo_filepath, 'w')
        if src == "imdb":
            content = "http://www.imdb.com/title/%s/" % str(id)
        else:
            content = "http://www.themoviedb.org/movie/%s" % str(id)
        nfo_file.write(content)
        nfo_file.close()
        if date and plugin.get_setting(SETTING_LIBRARY_SET_DATE, converter=bool):
            os.utime(nfo_filepath, (date,date))
        
    # create strm file
    strm_filepath = os.path.join(library_folder, str(id)+".strm")
    if not xbmcvfs.exists(strm_filepath):
        changed = True
        strm_file = xbmcvfs.File(strm_filepath, 'w')
        content = plugin.url_for("movies_play", src=src, id=id, mode='library')
        strm_file.write(content)
        strm_file.close()
        if date and plugin.get_setting(SETTING_LIBRARY_SET_DATE, converter=bool):
            os.utime(strm_filepath, (date,date))
    
    return changed    

def setup_library(library_folder):
    if library_folder[-1] != "/":
        library_folder += "/"

    if not xbmcvfs.exists(library_folder):
        # create folder
        xbmcvfs.mkdir(library_folder)
        
        # auto configure folder
        msg = _("Would you like to automatically set Meta as a movies video source?")
        if dialogs.yesno(_("Library setup"), msg):
            source_name = "Meta Movies"
            
            source_content = "('{0}','movies','metadata.themoviedb.org','',2147483647,0,'<settings><setting id=\"RatingS\" value=\"TMDb\" /><setting id=\"certprefix\" value=\"Rated \" /><setting id=\"fanart\" value=\"true\" /><setting id=\"keeporiginaltitle\" value=\"false\" /><setting id=\"language\" value=\"{1}\" /><setting id=\"tmdbcertcountry\" value=\"us\" /><setting id=\"trailer\" value=\"true\" /></settings>',0,0,NULL,NULL)".format(library_folder, LANG)

            add_source(source_name, library_folder, source_content)

    # return translated path
    return xbmc.translatePath(library_folder)
