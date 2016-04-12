import re
from meta import plugin, LANG
from meta.utils.text import to_unicode
from meta.play.players import get_needed_langs, ADDON_SELECTOR
from meta.play.base import active_players, action_cancel, action_play, on_play_video

from settings import SETTING_USE_SIMPLE_SELECTOR, SETTING_LIVE_DEFAULT_PLAYER

def play_channel(channel, program, language, mode="default"):
    # Get players to use
    if mode == 'select':
        play_plugin = ADDON_SELECTOR.id
    else:
        play_plugin = plugin.get_setting(SETTING_LIVE_DEFAULT_PLAYER)
    players = active_players("live", filters = {"channel": channel})
    players = [p for p in players if p.id == play_plugin] or players
    if not players:
        xbmc.executebuiltin( "Action(Info)")
        action_cancel()
        return

    # Get parameters
    params = {}
    for lang in get_needed_langs(players):
        params[lang] = get_channel_parameters(channel, program, language)
        params[lang] = to_unicode(params[lang])

    # Go for it
    link = on_play_video(mode, players, params)
    if link:
        action_play({
            'label': channel,
            'path': link,
            'is_playable': True,
            'info_type': 'video',
        })

def get_channel_parameters(channel, program, language):
    channel_regex = re.compile("(.+?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*.*?(\d*)$",
                               re.IGNORECASE|re.UNICODE)
    parameters = {}
    parameters['name'] = channel
    parameters['basename'] = re.sub(channel_regex, r"\1",channel)
    parameters['extension'] = re.sub(channel_regex, r"\2",channel)
    parameters['delay'] = re.sub(channel_regex, r"\3", channel)
    parameters['program'] = program
    parameters['language'] = language

    return parameters
