import os
import shutil

from xbmcswift2 import xbmc, xbmcvfs

from meta import plugin, import_tvdb, LANG
from meta.utils.text import to_utf8, date_to_timestamp, equals
from meta.utils.rpc import RPC
from meta.utils.properties import set_property
from meta.library.tools import scan_library, add_source
from meta.gui import dialogs

from settings import SETTING_TV_LIBRARY_FOLDER, SETTING_LIBRARY_SET_DATE
from language import get_string as _

def update_library():
    import_tvdb()
    
    folder_path = plugin.get_setting(SETTING_TV_LIBRARY_FOLDER)
    if not xbmcvfs.exists(folder_path):
        return
        
    # get library folder
    library_folder = setup_library(folder_path)
    
    # get shows in library
    try:
        shows = xbmcvfs.listdir(library_folder)[0]
    except:
        shows = []

    # update each show
    clean_needed = False
    updated = 0
    for id in shows:
        id = int(id)
        
        # add to library
        with tvdb.session.cache_disabled():
            if add_tvshow_to_library(library_folder, tvdb[id]):
                clean_needed = True
        updated += 1
                
    if clean_needed:
        set_property("clean_library", 1)
        
    # start scan
    if updated > 0:
        scan_library()

def add_tvshow_to_library(library_folder, show, play_plugin = None):
    clean_needed = False
    
    id = show['id']
    showname = to_utf8(show['seriesname'])

    ## Create show folder
    enc_show = showname.translate(None, '\/:*?"<>|').strip('.')
    show_folder = os.path.join(library_folder, str(id)+'/')
    if not xbmcvfs.exists(show_folder):
        try: 
            xbmcvfs.mkdir(show_folder)
        except:
            pass

        # Create play with file
        if play_plugin is not None:
            player_filepath = os.path.join(show_folder, 'player.info')
            player_file = xbmcvfs.File(player_filepath, 'w')
            content = "{0}".format(play_plugin)
            player_file.write(content)
            player_file.close()
            
        # Create nfo file
        nfo_filepath = os.path.join(show_folder, 'tvshow.nfo')
        if not xbmcvfs.exists(nfo_filepath):
            nfo_file = xbmcvfs.File(nfo_filepath, 'w')
            content = "http://thetvdb.com/index.php?tab=series&id=%s" % str(id)
            nfo_file.write(content)
            nfo_file.close()

    ## Get existing items in library
    
    # get all ids of the show
    ids = [id, show.get('imdb_id', None)]   # TODO: add tmdb!
    ids = [x for x in ids if x]

    # get show episodes in library
    try:
#        if not plugin.get_setting(SETTING_CHECK_LIBRARY_DUPS, converter=bool):
#            raise Exception()

        # get tvshow from library
        libshows = RPC.VideoLibrary.GetTVShows(properties=["imdbnumber", "title", "year"])['tvshows']
        libshows = [i for i in libshows if str(i['imdbnumber']) in ids or (str(i['year']) == str(show.get('year', 0)) and equals(show['seriesname'], i['title']))]
        libshow = libshows[0]
        
        # get existing (non strm) episodes in library
        libepisodes = RPC.VideoLibrary.GetEpisodes(filter={"and": [ {"field": "tvshow", "operator": "is", "value": to_utf8(libshow['title'])}]}, properties=["season", "episode", "file"])['episodes']
        libepisodes = [(int(i['season']), int(i['episode'])) for i in libepisodes if not i['file'].endswith(".strm")]
    except:
        libepisodes = []
    
    ## Create content strm files
    for (season_num,season) in show.items():
        if season_num == 0: # or not season.has_aired():
            continue
            
        for (episode_num, episode) in season.items():
            if episode_num == 0:
                continue
            
            delete = False
            if not episode.has_aired(flexible=True):
                delete = True
                #break
            
            if delete or (season_num, episode_num) in libepisodes:
                if library_tv_remove_strm(show, show_folder, id, season_num, episode_num):
                    clean_needed = True
            else:
                library_tv_strm(show, show_folder, id, season_num, episode_num)

    files, dirs = xbmcvfs.listdir(show_folder)
    if not dirs:
        shutil.rmtree(show_folder)
        clean_needed = True
                
    return clean_needed
    
def library_tv_remove_strm(show, folder, id, season, episode):
    enc_season = ('Season %s' % season).translate(None, '\/:*?"<>|').strip('.')
    enc_name = 'S%02dE%02d' % (season, episode)
    
    season_folder = os.path.join(folder, enc_season)
    stream_file = os.path.join(season_folder, enc_name + '.strm')
    if xbmcvfs.exists(stream_file):
        xbmcvfs.delete(stream_file)
        
        while not xbmc.abortRequested and xbmcvfs.exists(stream_file):
            xbmc.sleep(1000)
        
        a,b = xbmcvfs.listdir(season_folder)
        if not a and not b:
            xbmcvfs.rmdir(season_folder)
        
        return True
    return False
    
def library_tv_strm(show, folder, id, season, episode):        
    # Create season folder
    enc_season = ('Season %s' % season).translate(None, '\/:*?"<>|').strip('.')
    folder = os.path.join(folder, enc_season)
    try: 
        xbmcvfs.mkdir(folder)
    except: 
        pass
        
    # Create episode strm
    enc_name = 'S%02dE%02d' % (season, episode)
    stream = os.path.join(folder, enc_name + '.strm')
    if not xbmcvfs.exists(stream):
        file = xbmcvfs.File(stream, 'w')
        content = plugin.url_for("tv_play", id=id, season=season, episode=episode, mode='library')
        file.write(str(content))
        file.close()
        
        if plugin.get_setting(SETTING_LIBRARY_SET_DATE, converter=bool):
            try:
                firstaired = show[season][episode]['firstaired']
                t = date_to_timestamp(firstaired)
                os.utime(stream, (t,t))
            except:
                pass
    
def get_player_plugin_from_library(id):        
    # Specified by user
    try:
        library_folder = plugin.get_setting(SETTING_TV_LIBRARY_FOLDER)
        player_file = xbmcvfs.File(os.path.join(library_folder, str(id), "player.info"))
        content = player_file.read()
        player_file.close()
        if content:
            return content
    except:
        pass
    
    return None

def setup_library(library_folder):
    if library_folder[-1] != "/":
        library_folder += "/"

    if not xbmcvfs.exists(library_folder):
        # create folder
        xbmcvfs.mkdir(library_folder)
        
        # auto configure folder
        msg = _("Would you like to automatically set Meta as a tv shows source?")
        if dialogs.yesno(_("Library setup"), msg):
            source_name = "Meta TVShows"
            
            source_content = "('{0}','tvshows','metadata.tvdb.com','',0,0,'<settings><setting id=\"RatingS\" value=\"TheTVDB\" /><setting id=\"absolutenumber\" value=\"false\" /><setting id=\"dvdorder\" value=\"false\" /><setting id=\"fallback\" value=\"true\" /><setting id=\"fanart\" value=\"true\" /><setting id=\"language\" value=\"{1}\" /></settings>',0,0,NULL,NULL)".format(library_folder, LANG)

            add_source(source_name, library_folder, source_content)

    # return translated path
    return xbmc.translatePath(library_folder)
