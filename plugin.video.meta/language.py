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
            id = 31000
            print "warning: missing translation for", missing
            for text in missing:
                entry = polib.POEntry(
                    msgid=text,
                    msgstr=u'',
                    msgctxt="#{0}".format(id)
                )
                id += 1
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
_ALL['general'] = 32000
_ALL['players url'] = 32010
_ALL['install from url'] = 32012
_ALL['movies'] = 32100
_ALL['enable movie players'] = 32110
_ALL['preferred movie player'] = 32120
_ALL['preferred movie player from library'] = 32121
_ALL['tv shows'] = 32200
_ALL['enable tv players'] = 32201
_ALL['preferred tv player'] = 32210
_ALL['preferred tv player from library'] = 32211
_ALL['library'] = 32300
_ALL['library folder'] = 32301
_ALL['library folder'] = 32302
_ALL['update library'] = 32303
_ALL['advanced'] = 32400
_ALL['clear cache'] = 32401
_ALL['automatic movies library server'] = 32304
_ALL['set added time to release date'] = 32305
_ALL['use simple selection dialog'] = 32402
_ALL['attempt to hide keyboard while meta is searching (may not work or cause issues on some skins)'] = 32403
_ALL['would you like to automatically set meta as a movies video source?'] = 31000
_ALL['genres'] = 31001
_ALL['select stream...'] = 31002
_ALL['show info'] = 31003
_ALL['video not found :('] = 31004
_ALL['add to library'] = 31005
_ALL['do you want to remove your existing players first?'] = 31006
_ALL['enter password'] = 31007
_ALL['players updated'] = 31008
_ALL['enable players'] = 31009
_ALL['season'] = 31010
_ALL['top rated'] = 31012
_ALL['blockbusters'] = 31013
_ALL['on the air'] = 31014
_ALL['update players'] = 31015
_ALL['would you like to automatically set meta as a tv shows source?'] = 31016
_ALL['search'] = 31017
_ALL['search for'] = 31018
_ALL['next >>'] = 31019
_ALL['error'] = 31020
_ALL['popular'] = 31021
_ALL['select default player'] = 31022
_ALL['failed to update players'] = 31023
_ALL['in theatres'] = 31024
_ALL['select player'] = 31025
_ALL['warning'] = 31026
_ALL['library setup'] = 31027
_ALL['play with...'] = 31028
