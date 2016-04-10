# -*- coding: utf-8 -*-
import requests
import urllib
import time

import xbmc, xbmcgui

from meta.utils.text import to_utf8
from meta.gui import dialogs
from meta import plugin
from settings import *
from language import get_string as _

API_ENDPOINT = "https://api-v2launch.trakt.tv"
CLIENT_ID = "578aa4af9acbb324d42ff08a7a1eeeab3d329a3c259abd58aab107f23351d870"
CLIENT_SECRET = "41deac2a06e008f5fea43ec916f17949be520450f37874cc2f3fdeeaa861f529"
LIST_PRIVACY_IDS = (
    'private',
    'friends',
    'public'
)

def call_trakt(path, params={}, data=None, is_delete=False, with_auth=True, pagination = False, page = 1):
    params = dict([(k, to_utf8(v)) for k, v in params.items() if v])
    
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }

    def send_query():
        if with_auth:
            try:
                expires_at = plugin.get_setting(SETTING_TRAKT_EXPIRES_AT, converter=int)
                if time.time() > expires_at:
                    trakt_refresh_token()
            except:
                pass
                
            token = plugin.get_setting(SETTING_TRAKT_ACCESS_TOKEN)
            if token:
                headers['Authorization'] = 'Bearer ' + token
        if data is not None:
            assert not params
            return requests.post("{0}/{1}".format(API_ENDPOINT, path), json=data, headers=headers)
        elif is_delete:
            return requests.delete("{0}/{1}".format(API_ENDPOINT, path), headers=headers)
        else:
            return requests.get("{0}/{1}".format(API_ENDPOINT, path), params, headers=headers)

    def paginated_query(page):
        lists = []
        params['page'] = page
        results = send_query()
        if with_auth and results.status_code == 401 and dialogs.yesno(_("Authenticate Trakt"), _(
                "You must authenticate with Trakt. Do you want to authenticate now?")) and trakt_authenticate():
            response = paginated_query()
            return response
        results.raise_for_status()
        results.encoding = 'utf-8'
        lists.extend(results.json())
        return lists, results.headers["X-Pagination-Page-Count"]

    if pagination == False:
        response = send_query()
        if with_auth and response.status_code == 401 and dialogs.yesno(_("Authenticate Trakt"), _(
                "You must authenticate with Trakt. Do you want to authenticate now?")) and trakt_authenticate():
            response = send_query()
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.json()
    else:
        (response, numpages) = paginated_query(page)
        return response, numpages
    

    
def search_trakt(**search_params):
    return call_trakt("search", search_params)

def find_trakt_ids(id_type, id, query=None, type=None, year=None):
    response = search_trakt(id_type=id_type, id=id)
    if not response and query:
        response = search_trakt(query=query, type=type, year=year)
        if response and len(response) > 1:
            response = [r for r in response if r[r['type']]['title'] == query]

    if response:
        content = response[0]
        return content[content["type"]]["ids"]

    return {}
            

def trakt_get_device_code():
    data = { 'client_id': CLIENT_ID }
    return call_trakt("oauth/device/code", data=data, with_auth=False)


def trakt_get_device_token(device_codes):
    data = {
        "code": device_codes["device_code"],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    start = time.time()
    expires_in = device_codes["expires_in"]
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create(
        _("Authenticate Trakt"), 
        _("Please go to https://trakt.tv/activate and enter the code"),
        str(device_codes["user_code"])
    )

    try:
        time_passed = 0
        while not xbmc.abortRequested and not progress_dialog.iscanceled() and time_passed < expires_in:            
            try:
                response = call_trakt("oauth/device/token", data=data, with_auth=False)
            except requests.HTTPError, e:
                if e.response.status_code != 400:
                    raise e
                
                progress = int(100 * time_passed / expires_in)
                progress_dialog.update(progress)
                xbmc.sleep(max(device_codes["interval"], 1)*1000)
            else:
                return response
                
            time_passed = time.time() - start
            
    finally:
        progress_dialog.close()
        del progress_dialog
        
    return None

def trakt_refresh_token():
    data = {        
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "refresh_token",
        "refresh_token": plugin.get_setting(SETTING_TRAKT_REFRESH_TOKEN)
    }

    response = call_trakt("oauth/token", data=data, with_auth=False)
    if response:
        plugin.set_setting(SETTING_TRAKT_ACCESS_TOKEN, response["access_token"])
        plugin.set_setting(SETTING_TRAKT_REFRESH_TOKEN, response["refresh_token"])


def trakt_authenticate():
    code = trakt_get_device_code()
    token = trakt_get_device_token(code)
    if token:
        expires_at = time.time() + 60*60*24*30#*3
        plugin.set_setting(SETTING_TRAKT_EXPIRES_AT, str(expires_at))
        plugin.set_setting(SETTING_TRAKT_ACCESS_TOKEN, token["access_token"])
        plugin.set_setting(SETTING_TRAKT_REFRESH_TOKEN, token["refresh_token"])
        return True
    return False
    
@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_collection(type):
    return call_trakt("sync/collection/{0}".format(type), params={'extended':'full,images'})
        
@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_watchlist(type):
    return call_trakt("sync/watchlist/{0}".format(type), params={'extended':'full,images'})

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_lists():
    return call_trakt("users/me/lists")

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_liked_lists(page = 1):
    result, pages = call_trakt("users/likes/lists", params={'limit': 25}, pagination= True, page = page)
    return result, pages

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_list(user, list_slug):
    path = "users/{0}/lists/{1}/items".format(user, list_slug)
    return call_trakt(path, params={'extended':'full,images'})

def add_list(name, privacy_id=None, description=None):
    data = {
        'name': name,
        'description': description or '',
        'privacy': privacy_id or LIST_PRIVACY_IDS[0]
    }
    return call_trakt("users/me/lists", data=data)

def del_list(list_slug):
    path = "users/me/lists/{0}".format(list_slug)
    return call_trakt(path, is_delete=True)
    
@plugin.cached(TTL=60*24, cache="trakt")
def trakt_get_genres(type):
    return call_trakt("genres/{0}".format(type))
    
@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_calendar():
    return call_trakt("calendars/my/shows".format(type), params={'extended':'full,images'})
    
@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_next_episodes():
    shows = call_trakt("sync/watched/shows", params={'extended':'noseasons,full,images'})
    
    hidden_shows = [item["show"]["ids"]["trakt"] for item in trakt_get_hidden_items("progress_watched") if item["type"] == "show"]

    items = []
    for item in shows:
        show = item["show"]
        id = show["ids"]["trakt"]
        if id in hidden_shows:
            continue
            
        response = call_trakt("shows/{0}/progress/watched".format(id))    
        if response["next_episode"]:
            next_episode = response["next_episode"]
            next_episode["show"] = show
            items.append(next_episode)

    return items

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def trakt_get_hidden_items(type):
    return call_trakt("users/hidden/{0}".format(type))

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_show(id):
    return call_trakt("shows/{0}".format(id), params={'extended': 'full,images'})

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_season(id,season_number):
    seasons = call_trakt("shows/{0}/seasons".format(id), params={'extended': 'images'})
    for season in seasons:
        if season["number"] == season_number:
            return season

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_episode(id, season, episode):
    return call_trakt("shows/{0}/seasons/{1}/episodes/{2}".format(id, season, episode),
                      params={'extended': 'full,images'})

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_movie(id):
    return call_trakt("movies/{0}".format(id), params={'extended': 'full,images'})

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def get_recommendations(type):
    return call_trakt("/recommendations/{0}".format(type), params={'extended': 'full,images'})

def add_to_list(username, slug, data):
    return call_trakt("/users/{0}/lists/{1}/items".format(username, slug), data = data)

def remove_from_list(username, slug, data):
    return call_trakt("/users/{0}/lists/{1}/items/remove".format(username, slug), data = data)

@plugin.cached(TTL=CACHE_TTL, cache="trakt")
def search_for_list(list_name, page):
    results, pages = call_trakt("search", params={'type': "list", 'query': list_name, 'limit': 25}, pagination= True, page = page)
    return results, pages