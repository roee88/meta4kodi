import os
import glob
import time
import xml.etree.ElementTree as ET
try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database

from xbmcswift2 import xbmc
from meta.utils.rpc import RPC

def scan_library():
    while not xbmc.abortRequested and \
     (xbmc.getCondVisibility('Library.IsScanning') or \
     xbmc.getCondVisibility('Window.IsActive(progressdialog)')):
        xbmc.sleep(1000)
    xbmc.executebuiltin('UpdateLibrary(video)')
    
def get_movie_from_library(imdbnumber):
    imdbnumber = str(imdbnumber)
    
    db_movies = RPC.video_library.get_movies(properties=['title', 'file', 'imdbnumber'])
        
    for movie in db_movies.get('movies', []):
        if movie['imdbnumber'] != imdbnumber:
            continue
        if movie['file'].endswith(".strm"):
            continue
        return {'label': movie['title'], 'path': movie['file']}
    return None

def get_episode_from_library(imdbnumber, season, episode):
    imdbnumber = str(imdbnumber)
    season = int(season)
    episode = int(episode)
    
    db_shows = RPC.video_library.get_tv_shows(properties=['imdbnumber', 'file'])
    
    for show in db_shows.get('tvshows', []):
        if show['imdbnumber'] != imdbnumber:
            continue
            
        db_episodes = RPC.video_library.get_episodes(tvshowid=show["tvshowid"],\
            season=season, properties=['episode', 'file', 'title'])
        
        for ep in db_episodes.get('episodes', []):
            if ep['episode'] != episode:
                continue
            if ep['file'].endswith(".strm"):
                continue
            return {'label': ep['title'], 'path': ep['file']}
    return None

def add_source(source_name, source_path, source_content):    
    xml_file = xbmc.translatePath('special://profile/sources.xml')
    if not os.path.exists(xml_file):
        with open(xml_file, "w") as f:
            f.write("""<sources>
    <programs>
        <default pathversion="1" />
    </programs>
    <video>
        <default pathversion="1" />
    </video>
    <music>
        <default pathversion="1" />
    </music>
    <pictures>
        <default pathversion="1" />
    </pictures>
    <files>
        <default pathversion="1" />
    </files>
</sources>""")
    
    existing_source = _get_source_attr(xml_file, source_name, "path")
    if existing_source and existing_source != source_path:
        _remove_source_content(existing_source)
    
    if _add_source_xml(xml_file, source_name, source_path):
        _set_source_content(source_content)
    
#########   XML functions   #########

def _add_source_xml(xml_file, name, path):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    sources = root.find('video')

    existing_source = None
    
    for source in sources.findall('source'):
        xml_name = source.find("name").text
        xml_path = source.find("path").text
        if xml_name == name or xml_path == path:
            existing_source = source
            break
            
    if existing_source is not None:
        xml_name = source.find("name").text
        xml_path = source.find("path").text
        if xml_name == name and xml_path == path:
            return False
        elif xml_name == name:
            source.find("path").text = path
        else:
            source.find("name").text = name
    else:
        new_source = ET.SubElement(sources, 'source')
        new_name = ET.SubElement(new_source, 'name')
        new_name.text = name
        new_path = ET.SubElement(new_source, 'path')
        new_path.attrib['pathversion'] = "1"
        new_path.text = path
    
    _indent_xml(root)
    tree.write(xml_file)
    return True

def _indent_xml(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent_xml(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def _get_source_attr(xml_file, name, attr):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    sources = root.find('video')
    for source in sources.findall('source'):
        xml_name = source.find("name").text
        if xml_name == name:
            return source.find(attr).text
    return None

#########   Database functions  #########

def _db_execute(db_name, command):
    databaseFile = _get_database(db_name)
    if not databaseFile:
        return False
        
    dbcon = database.connect(databaseFile)
    dbcur = dbcon.cursor()
    
    dbcur.execute(command)
    #try:
    #    dbcur.execute(command)
    #except database.Error as e:
    #    print "MySQL Error :", e.args[0], q.decode("utf-8")
    #    return False
        
    dbcon.commit()
    
    return True

def _get_database(db_name):
    path_db = "special://profile/Database/" + db_name
    filelist = glob.glob(xbmc.translatePath(path_db))
    if filelist:
        return filelist[-1]
    return None

def _remove_source_content(path):
    q = "DELETE FROM path WHERE strPath LIKE '%{0}%'".format(path)
    return _db_execute("MyVideos*.db", q)

def _set_source_content(content):    
    q = "INSERT OR REPLACE INTO path (strPath,strContent,strScraper,strHash,scanRecursive,useFolderNames,strSettings,noUpdate,exclude,dateAdded,idParentPath) VALUES "
    q += content
    return _db_execute("MyVideos*.db", q)
    