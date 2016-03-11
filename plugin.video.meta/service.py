#!/usr/bin/python
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

import datetime

from xbmcswift2 import xbmc
from meta.video_player import VideoPlayer
from meta.utils.properties import get_property, clear_property
from addon import update_library
from settings import UPDATE_LIBRARY_INTERVAL

player = VideoPlayer()

class Monitor(xbmc.Monitor):
    def onDatabaseUpdated(self, database):
        if database == "video":
            if get_property("clean_library"):
                xbmc.executebuiltin("XBMC.CleanLibrary(video, false)")
                clear_property("clean_library")
                
monitor = Monitor()

def go_idle(duration):
    while not xbmc.abortRequested and duration > 0:
        if player.isPlayingVideo():
            player.currentTime = player.getTime()
        xbmc.sleep(1000)
        duration -= 1

def future(seconds):
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds)


def main():
    go_idle(25)
    next_update = future(0)
    while not xbmc.abortRequested:
        if next_update <= future(0):
            next_update = future(UPDATE_LIBRARY_INTERVAL)
            update_library()
        go_idle(30*60)

if __name__ == '__main__':
    main()