import os

from xbmcswift2 import xbmc, xbmcvfs

from meta import plugin, import_tvdb
from meta.utils.text import date_to_timestamp
from meta.library.tools import scan_library, add_source
from meta.gui import dialogs

from settings import SETTING_TV_LIBRARY_FOLDER
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
    updated = 0
    for id in shows:
        id = int(id)
        
        # add to library
        with tvdb.session.cache_disabled():
            add_tvshow_to_library(library_folder, tvdb[id])
        updated += 1
                
    # start scan
    if updated > 0:
        scan_library()

def add_tvshow_to_library(library_folder, show, play_plugin = None):
    id = show['id']
    showname = show['seriesname']
    if type(showname) == unicode:
        showname = showname.encode('utf-8')

    # Create show folder
    enc_show = showname.translate(None, '\/:*?"<>|').strip('.')
    show_folder = os.path.join(library_folder, str(id)+'/')
    if not os.path.exists(show_folder):
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
        if not os.path.isfile(nfo_filepath):
            nfo_file = xbmcvfs.File(nfo_filepath, 'w')
            content = "http://thetvdb.com/index.php?tab=series&id=%s" % str(id)
            nfo_file.write(content)
            nfo_file.close()

    # Create content strm files
    next_forced_update = 0
    for (season_num,season) in show.items():
        if season_num == 0: # or not season.has_aired():
            continue
            
        for (episode_num, episode) in season.items():
            if episode_num == 0:
                continue
            
            if not episode.has_aired():
                next_forced_update = episode.get_air_time()
                break
            
            library_tv_strm(show, show_folder, id, season_num, episode_num)

        if next_forced_update:
            break
            
    # Last updated
    if show['lastupdated']:
        try:
            lastupdated_path = os.path.join(show_folder, "lastupdated")
            file = xbmcvfs.File(lastupdated_path, "w")
            file.write("{0} {1}".format(show['lastupdated'], next_forced_update))
            file.close()
        except:
            pass

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
    if not os.path.exists(stream):
        file = xbmcvfs.File(stream, 'w')
        content = plugin.url_for("tv_play", id=id, season=season, episode=episode, mode='library')
        file.write(str(content))
        file.close()

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
            
            source_content = "('{0}','tvshows','metadata.tvdb.com','',0,0,'<settings><setting id=\"RatingS\" value=\"TheTVDB\" /><setting id=\"absolutenumber\" value=\"false\" /><setting id=\"dvdorder\" value=\"false\" /><setting id=\"fallback\" value=\"true\" /><setting id=\"fanart\" value=\"true\" /><setting id=\"language\" value=\"he\" /></settings>',0,0,NULL,NULL)".format(library_folder)

            add_source(source_name, library_folder, source_content)

    # return translated path
    return xbmc.translatePath(library_folder)
