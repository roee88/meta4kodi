# -*- coding: utf-8 -*-
from meta.utils.text import to_utf8
    
def query_trakt(path):
    import requests
    headers = {'Content-Type': 'application/json', 'trakt-api-version': '2'}
    api_key = "578aa4af9acbb324d42ff08a7a1eeeab3d329a3c259abd58aab107f23351d870"
    headers['trakt-api-key'] = api_key
    response = requests.request(
        "GET",
        "https://api-v2launch.trakt.tv/{0}".format(path),
        headers=headers)

    response.raise_for_status()
    response.encoding = 'utf-8'
    return response.json()

def search_trakt(**search_params):
    import urllib
    search_params = dict([(k, to_utf8(v)) for k, v in search_params.items() if v])
    return query_trakt("search?{0}".format(urllib.urlencode(search_params)))
    
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
