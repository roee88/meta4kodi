import re
from meta import plugin, LANG
from meta.utils.text import to_unicode
from meta.play.players import get_needed_langs, ADDON_SELECTOR
from meta.play.base import active_players, action_cancel, action_activate, action_play, action_resolve, get_video_link

from settings import SETTING_USE_SIMPLE_SELECTOR, SETTING_LIVE_DEFAULT_PLAYER

def play_channel(channel,mode="DEFAULT"):

    # Get active players
    players = active_players("live", filters = {"channel": channel})
    if not players:
        xbmc.executebuiltin( "Action(Info)")
        action_cancel()
        return

    # Get player to use
    if mode == 'select':
        play_plugin = ADDON_SELECTOR.id
    else:
        play_plugin = plugin.get_setting(SETTING_LIVE_DEFAULT_PLAYER)

    # Use just selected player if exists (selectors excluded)
    players = [p for p in players if p.id == play_plugin] or players

    # Preload params
    params = {}
    for lang in get_needed_langs(players):
        params[lang] = get_channel_parameters(channel)
        params[lang] = to_unicode(params[lang])

    # BETA
    use_simple_selector = plugin.get_setting(SETTING_USE_SIMPLE_SELECTOR, converter=bool)
    is_extended = not (use_simple_selector or len(players) == 1)
    if is_extended:
        action_cancel()

    # Get single video selection
    selection = get_video_link(players, params, mode, use_simple_selector)

    if not is_extended:
        action_cancel()

    if not selection:
        return

    # Get selection details
    link = selection['path']
    action = selection.get('action', '')

    plugin.log.info('Playing url: %s' % link.encode('utf-8'))

    # Activate link
    if action == "ACTIVATE":
        action_activate(link)
    else:
        listitem = {
            'label': channel,
            'path': link,
            'is_playable': True,
            'info_type': 'video',
        }

        if action == "PLAY":
            action_play(listitem)
        else:
            action_resolve(listitem)

def get_channel_parameters(channel):
    channel_regex = re.compile("(.+?)\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*.*?(\d*)$",
                               re.IGNORECASE|re.UNICODE)
    parameters = {}
    parameters['name'] = channel
    parameters['basename'] = re.sub(channel_regex, r"\1",channel)
    parameters['extension'] = re.sub(channel_regex, r"\2",channel)
    parameters['delay'] = re.sub(channel_regex, r"\3", channel)

    return parameters
