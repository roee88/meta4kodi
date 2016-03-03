#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

import xbmc
from tvdb_api import Tvdb

pluginid = "plugin.video.meta"

def get_url(stream_file):
    if stream_file.endswith(".strm"):
        with open(xbmc.translatePath(stream_file), "rb") as f:
            content = f.read()
            if content.startswith("plugin://" + pluginid):
                return content.replace("/library", "/select")
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
        else:
            storage_path = xbmc.translatePath('special://profile/addon_data/%s/.storage/' % pluginid)
            if not os.path.isdir(storage_path):
                os.makedirs(storage_path)
            
            tvdb = Tvdb("0629B785CE550C8D", language="all", cache=storage_path)
            title = xbmc.getInfoLabel('ListItem.TVShowTitle')
            year = xbmc.getInfoLabel('ListItem.Property(year)')
            season = xbmc.getInfoLabel('ListItem.Season')
            episode = xbmc.getInfoLabel('ListItem.Episode')
            results = [x['id'] for x in tvdb.search(title, year)]
            if results:
                tvdb_id = results[0]
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