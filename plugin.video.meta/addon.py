#!/usr/bin/python
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

import os
import time
import shutil
import traceback

from xbmcswift2 import xbmcplugin

from meta import plugin
from meta.utils.properties import get_property, set_property, clear_property
from meta.gui import dialogs
from meta.play import updater
from meta.play.players import get_players, ADDON_SELECTOR 

import meta.navigation.movies
import meta.navigation.tvshows
import meta.navigation.live
from meta.navigation.base import get_icon_path
from meta.play.base import active_players

import meta.library.tvshows
import meta.library.movies

from language import get_string as _
from settings import *

@plugin.route('/')
def root():
    """ Root directory """
    items = [
        {
            'label': _("Movies"),
            'path': plugin.url_for("movies"),
            'icon': get_icon_path("movies"),
        },
        {
            'label': _("TV Shows"),
            'path': plugin.url_for("tv"),
            'icon': get_icon_path("tv"),
        },
        {
            'label': _("Live"),
            'path': plugin.url_for("live"),
            'icon': get_icon_path("tv"),
        }
    ]
    
    fanart = plugin.addon.getAddonInfo('fanart')
    for item in items:
        item['properties'] = {'fanart_image' : fanart}
        
    return items
    
@plugin.route('/clear_cache')
def clear_cache():
    """ Clear all caches """
    for filename in os.listdir(plugin.storage_path):
        file_path = os.path.join(plugin.storage_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception, e:
            traceback.print_exc()

@plugin.route('/update_library')
def update_library():
    is_updating = get_property("updating_library")
    
    now = time.time()
    if is_updating and now - int(is_updating) < 120:
        plugin.log.debug("Skipping library update")
        return
        
    try:
        set_property("updating_library", int(now))
        meta.library.tvshows.update_library()
        meta.library.movies.update_library()
    finally:
        clear_property("updating_library")

@plugin.route('/settings/players/<media>')
def settings_set_players(media):
    players = get_players(media)
    players = sorted(players,key=lambda player: player.clean_title.lower())

    # Get selection by user
    selected = None
    try:
        result = dialogs.multiselect(_("Enable players"), [p.clean_title for p in players])
        if result is not None:
            selected = [players[i].id for i in result]
    except:
        msg = "Kodi 16 required. Do you want to enable all players instead?"
        if dialogs.yesno(_("Warning"), _(msg)):
            selected = [p.id for p in players]
    
    if selected is not None:
        if media == "movies":
            plugin.set_setting(SETTING_MOVIES_ENABLED_PLAYERS, selected)
        elif media == "tvshows":
            plugin.set_setting(SETTING_TV_ENABLED_PLAYERS, selected)
        elif media == "live":
            plugin.set_setting(SETTING_LIVE_ENABLED_PLAYERS, selected)
        else:
            raise Exception("invalid parameter %s" % media)
    
    plugin.open_settings()
    
@plugin.route('/settings/default_player/<media>')
def settings_set_default_player(media):
    players = active_players(media)
    players.insert(0, ADDON_SELECTOR)
    
    selection = dialogs.select(_("Select player"), [p.title for p in players])
    if selection >= 0:
        selected = players[selection].id
        if media == "movies":
            plugin.set_setting(SETTING_MOVIES_DEFAULT_PLAYER, selected)
        elif media == "tvshows":
            plugin.set_setting(SETTING_TV_DEFAULT_PLAYER, selected)
        else:
            raise Exception("invalid parameter %s" % media)
    
    plugin.open_settings()
    
@plugin.route('/settings/default_player_fromlib/<media>')
def settings_set_default_player_fromlib(media):
    players = active_players(media)
    players.insert(0, ADDON_SELECTOR)
    
    selection = dialogs.select(_("Select player"), [p.title for p in players])
    if selection >= 0:
        selected = players[selection].id
        if media == "movies":
            plugin.set_setting(SETTING_MOVIES_DEFAULT_PLAYER_FROM_LIBRARY, selected)
        elif media == "tvshows":
            plugin.set_setting(SETTING_TV_DEFAULT_PLAYER_FROM_LIBRARY, selected)
        else:
            raise Exception("invalid parameter %s" % media)
    
    plugin.open_settings()
    
@plugin.route('/update_players')
def update_players():
    url = plugin.get_setting(SETTING_PLAYERS_UPDATE_URL)
    
    if updater.update_players(url):
        plugin.notify(msg=_('Players updated'), delay=1000)
    else:
        plugin.notify(msg=_('Failed to update players'), delay=1000)
    
    plugin.open_settings()
        

#########   Main    #########

def main():
    if '/movies' in sys.argv[0]:
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    elif '/tv' in sys.argv[0]:
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    plugin.run()

if __name__ == '__main__':
    main()
