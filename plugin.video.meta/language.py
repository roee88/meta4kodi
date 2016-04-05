#! /usr/bin/python

def get_string(t):
    from meta import plugin
    id = _ALL.get(t.lower())
    if id:
        return plugin.get_string(id)
    else:
        plugin.log.error("missing translation for " + t.lower())
        return t
    
_ALL = {}

if __name__ == "__main__":
    import polib
    po = polib.pofile('resources/language/English/strings.po')
    
    try:
        import re
        import subprocess
        r = subprocess.check_output(["grep", "-hnr", "_([\'\"]", "."])
        strings = re.compile("_\([\"'](.*?)[\"']\)", re.IGNORECASE).findall(r)
        translated = [m.msgid.lower().replace("'", "\\'") for m in po]        
        missing = set([s for s in strings if s.lower() not in translated])
        if missing:
            ids_range = range(30000, 31000)
            ids_reserved = [int(m.msgctxt[1:]) for m in po]
            ids_available = [x for x in ids_range if x not in ids_reserved]
            print "warning: missing translation for", missing
            for text in missing:
                id = ids_available.pop(0)
                entry = polib.POEntry(
                    msgid=text,
                    msgstr=u'',
                    msgctxt="#{0}".format(id)
                )
                po.append(entry)
            po.save('resources/language/English/strings.po')
    except:
        pass
        
    content = []
    with open(__file__, "r") as me:
        content = me.readlines()
        content = content[:content.index("#GENERATED\n")+1]
    
    with open(__file__, 'w') as f:
        f.writelines(content)
        for m in po:
            line = "_ALL['{0}'] = {1}\n".format(m.msgid.lower().replace("'", "\\'"), m.msgctxt.replace('#', '').strip())
            f.write(line)

#GENERATED
_ALL['general'] = 30000
_ALL['players url'] = 30010
_ALL['install from url'] = 30012
_ALL['movies'] = 30100
_ALL['enable movie players'] = 30110
_ALL['preferred movie player'] = 30120
_ALL['preferred movie player from library'] = 30121
_ALL['tv shows'] = 30200
_ALL['enable tv players'] = 30201
_ALL['preferred tv player'] = 30210
_ALL['preferred tv player from library'] = 30211
_ALL['library'] = 30300
_ALL['library folder'] = 30301
_ALL['library folder'] = 30302
_ALL['update library'] = 30303
_ALL['advanced'] = 30400
_ALL['clear cache'] = 30401
_ALL['automatic movies library server'] = 30304
_ALL['set added time to release date'] = 30305
_ALL['use simple selection dialog'] = 30402
_ALL['number of simultaneous searches'] = 30404
_ALL['attempt to hide dialogs while meta is searching'] = 30410
_ALL['hide progress dialogs'] = 30411
_ALL['hide information dialogs'] = 30412
_ALL['hide keyboard dialog'] = 30413
_ALL['would you like to automatically set meta as a movies video source?'] = 30600
_ALL['genres'] = 30601
_ALL['select stream...'] = 30602
_ALL['show info'] = 30603
_ALL['video not found :('] = 30604
_ALL['add to library'] = 30605
_ALL['do you want to remove your existing players first?'] = 30606
_ALL['enter password'] = 30607
_ALL['players updated'] = 30608
_ALL['enable players'] = 30609
_ALL['season'] = 30610
_ALL['top rated'] = 30612
_ALL['blockbusters'] = 30613
_ALL['on the air'] = 30614
_ALL['update players'] = 30615
_ALL['would you like to automatically set meta as a tv shows source?'] = 30616
_ALL['search'] = 30617
_ALL['search for'] = 30618
_ALL['next >>'] = 30619
_ALL['error'] = 30620
_ALL['popular'] = 30621
_ALL['select default player'] = 30622
_ALL['failed to update players'] = 30623
_ALL['in theatres'] = 30624
_ALL['select player'] = 30625
_ALL['warning'] = 30626
_ALL['library setup'] = 30627
_ALL['play with...'] = 30628
_ALL['trakt watchlist'] = 30414
_ALL['please go to https://trakt.tv/activate and enter the code'] = 30415
_ALL['next episodes'] = 30416
_ALL['authenticate trakt'] = 30417
_ALL['add all to library'] = 30418
_ALL['are you sure you want to add your entire trakt collection to kodi library?'] = 30419
_ALL['trakt collection'] = 30420
_ALL['are you sure you want to add your entire trakt watchlist to kodi library?'] = 30421
_ALL['you must authenticate with trakt. do you want to authenticate now?'] = 30422
_ALL['my calendar'] = 30423
_ALL['live'] = 30500
_ALL['enable live players'] = 30501
_ALL['prefered live player'] = 30510
_ALL['move down'] = 30001
_ALL['move up'] = 30002
_ALL['clear channels'] = 30003
_ALL['remove channel'] = 30004
