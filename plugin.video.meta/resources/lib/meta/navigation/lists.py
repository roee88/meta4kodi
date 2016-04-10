from meta import plugin
from meta.navigation.movies import make_movie_item
from meta.info import get_tvshow_metadata_trakt, get_season_metadata_trakt, get_episode_metadata_trakt, \
    get_trakt_movie_metadata
from meta.navigation.base import get_icon_path, search
from meta.navigation.movies import make_movie_item
from meta.navigation.tvshows import make_tvshow_item, tv_play, tv_season
from meta.gui import dialogs
from language import get_string as _
from trakt import trakt

@plugin.route('/lists')
def lists():
    """ Lists directory """
    items = [
        {
            'label': _("Trakt liked lists"),
            'path': plugin.url_for("lists_trakt_liked_lists", page = 1),
            'icon': get_icon_path("traktlikedlists"),
        },
        {
            'label': _("Trakt my lists"),
            'path': plugin.url_for("lists_trakt_my_lists"),
            'icon': get_icon_path("traktmylists"),
        },
        {
            'label': _("Search"),
            'path': plugin.url_for("lists_trakt_search_for_lists"),
            'icon': get_icon_path("search"),
        },
    ]
    return items

@plugin.route('/lists/trakt/liked_lists/<page>')
def lists_trakt_liked_lists(page):
    lists, pages = trakt.trakt_get_liked_lists(page)
    items = []
    for list in lists:
        info = list["list"]
        name = info["name"]
        user = info["user"]["username"]
        slug = info["ids"]["slug"]
        items.append({
            'label': name,
            'path': plugin.url_for("lists_trakt_show_list", user = user, slug = slug),
            'icon': get_icon_path("traktlikedlists"),  # TODO
        })
    if pages > page:
        items.append({
            'label': _("Next >>"),
            'path': plugin.url_for("lists_trakt_liked_lists", page = int(page) + 1),
            'icon': get_icon_path("traktlikedlists"),  # TODO
        })
    return items

@plugin.route('/lists/trakt/my_lists')
def lists_trakt_my_lists():
    lists = trakt.trakt_get_lists()
    items = []
    for list in lists:
        name = list["name"]
        user = list["user"]["username"]
        slug = list["ids"]["slug"]
        items.append({
            'label': name,
            'path': plugin.url_for(lists_trakt_show_list, user = user, slug = slug),
            'icon': get_icon_path("traktmylists"),
        })
    return sorted(items,key = lambda item: item["label"])

@plugin.route('/lists/trakt_search_for_lists')
def lists_trakt_search_for_lists():
    search(lists_search_for_lists_term)

@plugin.route('/lists/search_for_lists_term/<term>/<page>')
def lists_search_for_lists_term(term,page):
    lists, pages = trakt.search_for_list(term, page)
    page = int(page)
    pages = int(pages)
    items = []
    for list in lists:
        if "list" in list:
            list_info = list["list"]
        else:
            continue
        name = list_info["name"]
        user = list_info["username"]
        slug = list_info["ids"]["slug"]

        info = {}
        info['title'] = name
        if "description" in list_info:
            info["plot"] = list_info["description"]
        else:
            info["plot"] = _("No description available")
        if user != None:
            items.append({
                'label': "{0} {1} {2}".format(name, _("by"), user),
                'path': plugin.url_for("lists_trakt_show_list", user=user, slug=slug),
                'info': info,
                'icon': get_icon_path("traktlikedlists"),  # TODO
            })

    if (len(items) < 25 and pages > page):
        page = page + 1
        results = lists_search_for_lists_term(term, page)
        return items + results
    if pages > page:
        items.append({
            'label': _("Next >>"),
            'path': plugin.url_for("lists_search_for_lists_term", term = term, page=page + 1),
            'icon': get_icon_path("traktlikedlists"),  # TODO
        })
    return items


@plugin.route('/lists/trakt/show_list/<user>/<slug>')
def lists_trakt_show_list(user, slug):
    list_items = trakt.get_list(user, slug)
    return _lists_trakt_show_list(list_items)

@plugin.route('/lists/trakt/_show_list/<list_items>')
def _lists_trakt_show_list(list_items):
    genres_dict = trakt.trakt_get_genres("tv")

    if type(list_items) == str:
        import urllib
        list_items = eval(urllib.unquote(list_items))

    items = []
    for list_item in list_items[:25]:
        item = None
        item_type = list_item["type"]

        if item_type == "show":
            tvdb_id = list_item["show"]["ids"]["tvdb"]
            show = list_item["show"]
            info = get_tvshow_metadata_trakt(show, genres_dict)

            context_menu = [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for("tv_add_to_library", id=tvdb_id))
                ),
                (
                    _("Show info"), 'Action(Info)'
                ),
                (
                    _("Remove from list"),
                    "RunPlugin({0})".format(plugin.url_for("lists_remove_show_from_list", src="tvdb", id=tvdb_id))
                )
            ]

            item = ({
                'label': info['title'],
                'path': plugin.url_for("tv_tvshow", id=tvdb_id),
                'context_menu': context_menu,
                'thumbnail': info['poster'],
                'icon': "DefaultVideo.png",
                'poster': info['poster'],
                'properties' : {'fanart_image' : info['fanart']},
                'info_type': 'video',
                'stream_info': {'video': {}},
                'info': info
            })

        elif item_type == "season":
            tvdb_id = list_item["show"]["ids"]["tvdb"]
            season = list_item["season"]
            show = list_item["show"]
            show_info = get_tvshow_metadata_trakt(show, genres_dict)
            season_info = get_season_metadata_trakt(show_info,season, genres_dict)
            label = "{0} - Season {1}".format(show["title"],season["number"])


            context_menu = [
                (
                    _("Add to library"),
                    "RunPlugin({0})".format(plugin.url_for("tv_add_to_library", id=tvdb_id))
                ),
                (
                    _("Show info"), 'Action(Info)'
                ),
                (
                    _("Remove from list"),
                    "RunPlugin({0})".format(plugin.url_for("lists_remove_season_from_list", src="tvdb",
                                                           id=tvdb_id, season=list_item["season"]["number"]))
                )
            ]

            item = ({
                'label': label,
                'path': plugin.url_for(tv_season, id=tvdb_id, season_num=list_item["season"]["number"]),
                'context_menu': context_menu,
                'info': season_info,
                'thumbnail': season_info['poster'],
                'icon': "DefaultVideo.png",
                'poster': season_info['poster'],
                'properties': {'fanart_image': season_info['fanart']},
            })

        elif item_type == "episode":
            tvdb_id = list_item["show"]["ids"]["tvdb"]

            episode = list_item["episode"]
            show = list_item["show"]

            season_number = episode["season"]
            episode_number = episode["number"]

            show_info = get_tvshow_metadata_trakt(show, genres_dict)
            episode_info = get_episode_metadata_trakt(show_info, episode)
            label = "{0} - S{1}E{2} - {3}".format(show_info["title"], season_number,
                                                  episode_number, episode_info["title"])

            context_menu = [
                (
                    _("Select stream..."),
                    "PlayMedia({0})".format(
                        plugin.url_for("tv_play", id=tvdb_id, season=season_number,
                                       episode=episode_number, mode='select'))
                ),
                (
                    _("Show info"),
                    'Action(Info)'
                ),
                (
                    _("Add to list"),
                    "RunPlugin({0})".format(plugin.url_for("lists_add_episode_to_list", src='tvdb', id=tvdb_id,
                                                           season=season_number, episode=episode_number))
                ),
                (
                    _("Remove from list"),
                    "RunPlugin({0})".format(plugin.url_for("lists_remove_season_from_list", src="tvdb", id=tvdb_id,
                                                           season=season_number, episode = episode_number))
                )
            ]

            item = ({
                'label': label,
                'path': plugin.url_for("tv_play", id=tvdb_id, season=season_number,
                                       episode=episode_number, mode='default'),
                'context_menu': context_menu,
                'info': episode_info,
                'is_playable': True,
                'info_type': 'video',
                'stream_info': {'video': {}},
                'thumbnail': episode_info['poster'],
                'poster': episode_info['poster'],
                'icon': "DefaultVideo.png",
                'properties': {'fanart_image': episode_info['fanart']},
                      })

        elif item_type == "movie":
            movie = list_item["movie"]
            movie_info = get_trakt_movie_metadata(movie)

            item = make_movie_item(movie_info, True)

        if item is not None:
            items.append(item)
    if len(list_items) >= 25:
        items.append({
            'label': _('Next >>'),
            'path': plugin.url_for(_lists_trakt_show_list, list_items=str(list_items[25:]))
        })
    return items

@plugin.route('/lists/add_movie_to_list/<src>/<id>')
def lists_add_movie_to_list(src, id):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if (src == "tmdb" or src == "trakt"): #trakt seems to want integers unless imdb
            id = int(id)
        data = {
            "movies": [
                {
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.add_to_list(user, slug, data)

@plugin.route('/lists/add_show_to_list/<src>/<id>')
def lists_add_show_to_list(src, id):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt":  # trakt seems to want integers
            id = int(id)
        data = {
            "shows": [
                {
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.add_to_list(user, slug, data)

@plugin.route('/lists/add_season_to_list/<src>/<id>/<season>')
def lists_add_season_to_list(src, id, season):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt":  # trakt seems to want integers
            season = int(season)
            id = int(id)
        data = {
            "shows": [
                {
                    "seasons": [
                        {
                            "number": season,
                        }
                    ],
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.add_to_list(user, slug, data)

@plugin.route('/lists/add_episode_to_list/<src>/<id>/<season>/<episode>')
def lists_add_episode_to_list(src, id, season, episode):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt": #trakt seems to want integers
            season = int(season)
            episode = int(episode)
            id = int(id)
        data = {
                "shows": [
                    {
                        "seasons": [
                            {
                                "number": season,
                                "episodes": [
                                    {
                                        "number": episode
                                    }
                                ]
                            }
                        ],
                        "ids": {
                            src: id
                        }
                    }
                ]
            }

        trakt.add_to_list(user, slug, data)

@plugin.route('/lists/remove_movie_from_list/<src>/<id>')
def lists_remove_movie_from_list(src, id):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if (src == "tmdb" or src == "trakt"):  # trakt seems to want integers unless imdb
            id = int(id)
        data = {
            "movies": [
                {
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.remove_from_list(user, slug, data)

@plugin.route('/lists/remove_show_from_list/<src>/<id>')
def lists_remove_show_from_list(src, id):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt":  # trakt seems to want integers
            id = int(id)
        data = {
            "shows": [
                {
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.remove_from_list(user, slug, data)

@plugin.route('/lists/remove_season_from_list/<src>/<id>/<season>')
def lists_remove_season_from_list(src, id, season):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt":  # trakt seems to want integers
            season = int(season)
            id = int(id)
        data = {
            "shows": [
                {
                    "seasons": [
                        {
                            "number": season,
                        }
                    ],
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.remove_from_list(user, slug, data)

@plugin.route('/lists/remove_episode_from_list/<src>/<id>/<season>/<episode>')
def lists_remove_episode_from_list(src, id, season, episode):
    selected = get_list_selection()
    if selected is not None:
        user = selected['user']
        slug = selected['slug']
        if src == "tvdb" or src == "trakt":  # trakt seems to want integers
            season = int(season)
            episode = int(episode)
            id = int(id)
        data = {
            "shows": [
                {
                    "seasons": [
                        {
                            "number": season,
                            "episodes": [
                                {
                                    "number": episode
                                }
                            ]
                        }
                    ],
                    "ids": {
                        src: id
                    }
                }
            ]
        }

        trakt.remove_from_list(user, slug, data)

def get_list_selection():
    trakt_lists = trakt.trakt_get_lists()
    my_lists = []
    for list in trakt_lists:
        my_lists.append({
            'name': list["name"],
            'user': list["user"]["username"],
            'slug': list["ids"]["slug"]
        })

    selection = dialogs.select(_("Select list"), [l["name"] for l in my_lists])
    if selection >= 0:
        return my_lists[selection]
    return None
