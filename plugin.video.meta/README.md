# Meta for Kodi

##Description

Are you using multiple addons for streaming* of movies or TV series? Meta is here to make your life a bit easier!

\* Respect copyright laws. Meta is completely legal and provides no links at
all. It only re-arranges the content of your other, already installed, addons.
Do **not** ask for help on writing a Meta-player file for any addon that may
provide illegal content.

### What it does?
Instead of searching for the same content through all of your addons,
you simply find it in Meta and a list of all links from all configured addons
will be displayed right in front of you, allowing the selection of the addon to
use for playback. Meta can also search your local library or custom directories. 

### How does it work?
Meta lists content from TMDB and TVDB. 
By default, none of the media is playable. However, other addons can be linked
to Meta by writing small configuration files referred to as Meta-players. 
Meta uses the hints in the Meta-player to browse the external addon, find 
list items that match the desired media and create playable links from the paths
of these items. Meta aggregates all discovered links and displays them to the
user in a simple and well organized selection dialog.

### That sounds kind of slow :/
Not at all. Meta uses concurrent execution to browse through all addons 
simultaneously. Additionaly, discovered links are displayed as they are found 
and there is no need to wait for the process to complete before selecting a
link (the selection dialog is self-updating). Note that behavior is a bit
different if only a single Meta-player is active - a native selection dialog is shown if multiple links are found and automatic playback is used otherwise.

### Other features
- Multi-language:
    - All content displayed in Kodi's display language
- Easy library integration:
    - Automatic setup of video source and scraper.
    - Episodes marked as watched in library even when playing from within addon.
- Default Meta-player settings:
    - Default player for movies.
    - Default player for tv shows.
    - Default player for movies on play from library.
    - Default player for tv shows on play from library.
    - A player per tv-show selected when a show is added to library.
- Compatibility with script.trakt

### Fine.. how do I add a Meta-player for addon XYZ?
A Meta-player is a json file with ".meta.json" file extension that specifies
how to browse an external addon or a local diretory.

Existing Meta-players can easily be added to Meta from Meta's settings. 
Set in 'Players update URL' a link to a zip of all Meta-players to install,
save the settings and then re-open to select the 'Update players' option.

If no one created a Meta-player for the specific addon yet, you'll need to write
it on your own. It's really not that hard, go ahead and read next sections to
learn how to do that.

TIP: if you want to maintain a set of Meta-players online, create a github
repository with all Meta-players and use the following endpoint as the link to
use in Meta's settings: `https://api.github.com/repos/:owner/:repo/zipball`

##Parameters

The hints in a Meta-player can use parameters provided by Meta according to the
selected media itself. For example, {title} is the movie's name, {imdb} is the
movie's IMDB identifier, etc.

Parameters are written inside curly brackets {}. Formatting is also supported,
e.g.: {season:02d} is replaced with a 2-letters season number with a leading
zero if needed. See: 
https://docs.python.org/2/library/string.html#format-specification-mini-language

Text parameters also have siblings that determine how whitespaces are
interpreted. Currently _escaped replaces whitespaces with %2520 and _+ 
replaces whitespaces with a + sign. For example: 
{title}: Awesome movie
{title_+}: Awesome+movie
{title_escaped}: Awesome%2520movie

####Movie parameters:
-    id:
        TMDB id
-    imdb:
        IMDB id
-    trakt:
        Trakt id
-    slug:
        Trakt slug
-    title:
        Movie title
-    year:
        Movie release year
-    name:
        Formatted as "title (year)"

####TV show parameters:
-    id: 
        TVDB id
-    imdb:
        IMDB id
-    tmdb:
        TMDB id
-    trakt:
        Trakt id
-    slug:
        Trakt slug
-    showname:
        Show name as listed in TVDB
-    clearname:
        Show name excluding year if present
-    name:
        Format: showname SXXEXX
-    title:
        Episode title
-    season:
        Season number
-    episode:
        Episode number
-    absolute_number:
        Absolute episode number
-    firstaired:
        First aired date (yyyy-mm-dd)
-    year:
        First aired year
-    network:
        Broadcast network
-    genre:
        Genre as listed in TMDB

##Meta-player format

Root: dictionary
```
    "name": string
        Display name (HTML tags allowed)

    "plugin": string [optional]
        Ignore player if a plugin with the id of the sepecified value is not
        installed.
        
    "id": string [optional, default=from file name]
        Unique string identifier. As convension please use: 
        "provider.{your_name}.{addon_name}"

    "filters": dictionary [optional]
        Ignore player if filters don't match.
        Currently only "network" filter for tvshows is supported.
        Example: {"network": "BBC"}.

    "postprocess": string [optional]
        Restricted python code (imports, modules and builtins are disallowed).
        The code should only be used to modify found links. Use the variable "link" to refer to the link to modify. 
        Example: "link.replace('demo=1','demo=0')"
        
    "movies": list<CommandSequence> [optional]
        List of CommandSequence entries for playing a movie video.
        Meta executes all CommandSequence entries (one at the time).
                        
    "tvshows": list<CommandSequence> [optional]
        List of CommandSequence entries for playing an episode.
        Meta executes all CommandSequence entries (one at the time).
```    

CommandSequence: list\<CommandItem\>
```    
    List of CommandItem entries.
    Meta stops executing a CommandSequence at the first successful CommandItem.
```

CommandItem: dict
```    
    "action": string [optional, default="RESOLVE"]
        RESOLVE:  Calls xbmcplugin.setResolvedUrl on selected link.
                    use it if final url is video.
        PLAY:     Calls xbmc.Player.play on selected link.
                    use it if final url is video but RESOLVE results in a dialog message reporting failed playback although video is playing in background.        
        ACTIVATE: Calls Container.Update on selected link.
                    use it if final url is a folder or a custom view.

    "language": string [optional, default="en"]
        Language to use for parameters.
        
    "link": string
        A parameterized URL.
        
        If URL is final then the "steps" item should be omitted.
        Example: 
            [*] plugin://plugin.video.example/{imdb}/play
            
        If browsing list items is needed then a "plugin://" url should be used
        as a starting point for external browsing.
        Examples:
            [*] plugin://plugin.video.example/?action=search&q={title}
            [*] plugin://plugin.video.example/all/
            [*] plugin://plugin.video.example

    "steps": list<string> [optional]
        List of parameterized regex entries to hint how to browse the external
        addon. For example if plugin.video.example provides a list of public
        domain movies in its root, and after selecting a movie the user needs
        to select one of two list items: "play movie" or "play trailer" then
        the steps to use are: ["{title}", "play movie"].
        
        The matching is done by comparing the text in the addon to the step's
        regex. Before comparing, the following symbols are replaced with
        whitespace in both the text from the addon and parameters: ., %20.
        
        Common regex symbols:
        .   - Any character.
        *   - Previous character/group can appear zero or many times.
        +   - Previous character/group can appear one or more times.
        ?   - Previous character/group is optional.
        .*  - Match anything (greedy).
        .*? - Match anything (not greedy).
        $$  - Match start of string or end of string or whitespace or [ or ].
              Note: not a standard regex but we have added it for convinence.
```

##How to write a CommandSequence?

we will now show three methods that may be used. In our example we will add 
support for a (dummy) plugin that has the id plugin.video.example.

1. Browsing an external addon: 
    Say the addon lists all movies in english inside Movies->All and after 
    choosing a movie it shows (**not** in a dialog) a few links in the a 
    "[Quality] name" format.
    
    Here is the CommandSequence to use for adding support for this addon,
    prefering 720P first and falling back to any quality otherwise:
    
    ```json
    [
     {
      "link": "plugin://plugin.video.example",
      "steps": ["Movies", "All", "{title}", "\[720p\].*"]
     },
     {
      "link": "plugin://plugin.video.example",
      "steps": ["Movies", "All", "{title}", ".*"]
     }     
    ]
    ```

2. Using library integration:
        
    Say the addon has a library integration feature. Use it to add some movie to
    your library and locate the generated strm file. Open it in text editor and 
    you will see the final url to use for playing the movie you have added. If
    all parameters inside the url are supported by Meta, then you can use it by 
    adding a simple CommandSequence. For example if the strm contains:
    
    plugin://plugin.video.example/tt1234567/play
        
    Then use the following CommandSequence:
    ```json
    [
     {
      "link": "plugin://plugin.video.example/{imdb}/play"
     }
    ]
    ```        
3. Using search:
        
    Say the addon we are adding also has a search feature that allows the user
    to enter free text and returns a folder listing all movie results. 
        
    A. locate the search function inside the addon's code. 
    Normally searching for the word 'keyboard' will get you close. 
         
    B. identify what the code does with the entered search phrase.
    In some addons a plugin url would be generated and Container.Update would be
    executed with that url. If that's the case then just print the url and see
    the printed url in kodi.log. If all parameters in the url are supported then
    replace the parameters in the url as decsribed earlier (in 2) and use it as
    the link in the CommandSequence (followed by any required steps).
         
    In other cases a funtion would be called after the user enters a search
    phrase passing the entered text as an argument. Lets assume that in our
    example there is such a function call to a function named do_search. Now we 
    need a way to call do_search from Meta using a url. To do this find the part
    of code that parses args (usually this is written at the bottom of the main
    python file) and locate which args are needed in order to call do_search
    with the search phrase. Lets assume for our example we need to pass mode=2
    to call do_search and the search phrase is pased using q=<search_phrase>.
    Then the CommandSequence to use (prefering 720P) is:
         
    ```json
    [
     {
      "link": "plugin://plugin.video.example/?mode=2&q={title}",
      "steps": ["{title}", "\[720p\].*"]
     },
     {
      "link": "plugin://plugin.video.example/?mode=2&q={title}",
      "steps": ["{title}", ".*"]
     }     
    ]
    ```
    
##Full examples

Filename: provider.library.meta.json

Description: Search media in Kodi's library.

```
{
    "id": "provider.library",
    "name": "Library",
    "tvshows": [
        [
            {
                "link": "tvshows"
            }
        ]
    ],
    "movies": [
        [
            {
                "link": "movies"
            }
        ]
    ]
}
```

Filename: provider.local.meta.json

Description: Search episode in a local folder. The folder must be configured in Kodi's file explorer.

```
{
    "id": "provider.local",
    "name": "Local",
    "tvshows": [
        [
            {
                "link": "c:/Videos/",
                "steps": [
                    "{clearname}.*S{season:02d}E{episode:02d}.*(avi|mp4)"
                ]
            }
        ]
    ]
}
```

Filename: provider.quasar.meta.json

Description: Play using plugin.video.quasar.

```
{
    "id": "provider.quasar",
    "plugin": "plugin.video.quasar",
    "name": "[COLOR FFD15FEE]Quasar[/COLOR]",
    "movies": [
        [
            {
                "link": "plugin://plugin.video.quasar/movie/{imdb}/play"
            }
        ]
    ],
    "tvshows": [
        [
            {
                "link": "plugin://plugin.video.quasar/show/{id}/season/{season}/episode/{episode}/play"
            }
        ]
    ]
}
```

Filename: provider.iba.meta.json

Description: Search episodes in plugin.video.IBA.

```
{
    "id": "provider.iba",
    "name": "[COLOR FF418106]הערוץ הראשון[/COLOR]",
    "plugin": "plugin.video.IBA",
    "filters": {
        "network": "הערוץ הראשון"
    },
    "tvshows": [
        [
            {
                "language": "he",
                "link": "plugin://plugin.video.IBA/",
                "steps": [
                    "{showname}",
                    ".*עונה {season}",
                    "(?:{showname}|פרקים מלאים)",
                    ".*פרק {episode}"
                ]
            }
        ]
    ]
}
```
