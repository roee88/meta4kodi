#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

import xbmc
from tvdb_api import Tvdb
from meta.utils.rpc import RPC

pluginid = "plugin.video.meta"

def get_url(stream_file):
    if stream_file.endswith(".strm"):
        with open(xbmc.translatePath(stream_file), "rb") as f:
            content = f.read()
            if content.startswith("plugin://" + pluginid):
                return content.replace("/library", "/select")
    return None
    
def get_imdb_id(media_type, dbid):
    if not dbid:
        return None
    dbid = int(dbid)
    if media_type == "movie":
        data = RPC.VideoLibrary.GetMovieDetails(properties=["imdbnumber","title", "year"], movieid=dbid)
        if "moviedetails" in data:
            return data["moviedetails"]['imdbnumber']
    elif media_type == "tvshow":
        data = RPC.VideoLibrary.GetTVShowDetails(properties=["imdbnumber","title", "year"], tvshowid=dbid)
        if "tvshowdetails" in data:
            return data["tvshowdetails"]['imdbnumber']
    
    return None

def get_tvshow_id_by_episode(dbid):
    if not dbid:
        return None
    dbid = int(dbid)
    data = RPC.VideoLibrary.GetEpisodeDetails(properties=["tvshowid"], episodeid=dbid)
    if "episodedetails" in data:
        return get_imdb_id(media_type="tvshow",
                                dbid=data['episodedetails']['tvshowid'])
    else:
        return None

def main():
    # TODO: on jarvis use sys.listitem and getProperty, getfilename, getVideoInfoTag
    stream_file = xbmc.getInfoLabel('ListItem.FileNameAndPath')    
    url = get_url(stream_file)
    
    if url is None:
    
        db_type = xbmc.getInfoLabel('ListItem.DBTYPE')
        
        if db_type == "movie":
            imdbnumber = xbmc.getInfoLabel('ListItem.IMDBNumber')
            url = "plugin://{0}/movies/play/{1}/{2}/select".format(pluginid, 
                    "imdb", imdbnumber)
        
        elif db_type == "episode":
            storage_path = xbmc.translatePath('special://profile/addon_data/%s/.storage/' % pluginid)
            if not os.path.isdir(storage_path):
                os.makedirs(storage_path)
            
            tvdb = Tvdb("0629B785CE550C8D", cache=storage_path)
            title = xbmc.getInfoLabel('ListItem.TVShowTitle')
            year = xbmc.getInfoLabel('ListItem.Property(year)')
            season = xbmc.getInfoLabel('ListItem.Season')
            episode = xbmc.getInfoLabel('ListItem.Episode')
            dbid = xbmc.getInfoLabel('ListItem.DBID')
            
            results = tvdb.search(title, year, language="all")
            if results:
                tvdb_id = None
                
                identifier = get_tvshow_id_by_episode(dbid)
                if identifier:
                    by_id = [x for x in results if x['id'] == identifier or x.get('imdb_id') == identifier]
                    if by_id:
                        tvdb_id = by_id[0]['id']
                        
                if tvdb_id is None:
                    tvdb_id = results[0]['id']
                    
                url = "plugin://{0}/tv/play/{1}/{2}/{3}/select".format(pluginid, 
                        tvdb_id, season, episode)
            else:
                title = "Meta"
                msg = "Failed to find media on TVDB"
                xbmc.executebuiltin('XBMC.Notification("%s", "%s", "%s", "%s")' 
                        % (msg, title, 2000, ''))
                
    xbmc.executebuiltin("PlayMedia({0})".format(url))
    
    
if __name__ == '__main__':
    main()