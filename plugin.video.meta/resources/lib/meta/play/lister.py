import re
import copy
from threading import Event
from xbmcswift2 import xbmc, xbmcgui

from meta import plugin
from meta.utils.text import urlencode_path, to_utf8, to_unicode
from meta.utils.rpc import RPC

# These are replace with whitespace in labels and parameters
IGNORE_CHARS = ('.', '%20')#('+', '-', '%20', '.', ' ')

def regex_escape(string):
    for c in ".$^{[(|)*+?\\":
        string = string.replace(c, "\\"+c)
    return string
    
@plugin.cached(TTL=5, cache="browser")
def list_dir(path):
    path = urlencode_path(path)

    try:
        response = RPC.files.get_directory(media="files", directory=path, properties=["season","episode"])
    except:
        plugin.log.error(path)
        raise
    dirs = []
    files = []
    
    for item in response.get('files', []):
        if item.has_key('file') and item.has_key('filetype') and item.has_key('label'):
            if item['filetype'] == 'directory':
                # ignore .xsp and .xml directories
                for ext in (".xsp", ".xml"):
                    if item['file'].endswith(ext) or item['file'].endswith(ext+"/"):
                        continue
                dirs.append({'path':item['file'], 'label':item['label'], 'season': item.get('season')})
            else:
                files.append({'path':item['file'], 'label':item['label'], 'episode': item.get('episode')})
                
    return [path,dirs,files]
    
class Lister:
    def __init__(self, preserve_viewid=None, stop_flag=None):
        if stop_flag is None:
            stop_flag = Event()
        self.stop_flag = stop_flag
        
        if preserve_viewid is None:
            window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            preserve_viewid = window.getFocusId()
        self.preserve_viewid = preserve_viewid
        
    def get(self, path, guidance, parameters):            
        try:
            return self._browse_external(path, guidance, parameters)
        finally:
            self._restore_viewid()

    def is_active(self):
        return not self.stop_flag.is_set()
        
    def stop(self):
        if not self.stop_flag.is_set():
            self.stop_flag.set()
            
            
#    @staticmethod
#    def _replace_special_chars(text):
#        for c in ('\+', '\-', '\%20', '\.', '\ '):
#            text = text.replace(c, ' ')
#        return text
        
    @staticmethod
    def _has_match(item, pattern, parameters):
        # Match by season
        if pattern == "{season}" and item.get('season'):
            item_season = str(item.get('season'))
            param_season = str(parameters.get('season'))
            if item_season == param_season:
                return True
        # Match by episode
        elif pattern == "{episode}" and item.get('episode'):
            item_episode = str(item.get('episode'))
            param_episode = str(parameters.get('episode'))
            print "XB", item_episode, param_episode
            if item_episode == param_episode:
                return True
        
        # Match by label
        label = item['label']
        pattern = to_unicode(pattern)
        # Custom $$ shortcut for unicode word boundary
        pattern = pattern.replace("$$", r"($|^|\s|\]|\[)")
                
        # Detect season number if searching for season 1
        #   to later allow first season to have no number
        first_season = False
        if '{season}' in pattern and '1' == str(parameters.get('season')):
            pattern = pattern.replace('{season}', '(?P<season>\d*)')
            first_season = True
            
        # Apply parameters to pattern
        pattern = pattern.format(**parameters)
       
        # Remove special chars
        for c in IGNORE_CHARS:
            #pattern = pattern.replace("\\"+c, ' ')
            label = label.replace(c, ' ')

        # Make sure both label and pattern are unicode
        pattern = to_unicode(to_utf8(pattern))               
        label = to_unicode(to_utf8(label))
        
        plugin.log.debug("matching pattern {0} to label {1}".format(to_utf8(pattern), to_utf8(label)))
         
        # Test for a match
        r = re.compile(pattern, re.I|re.UNICODE)
        match = r.match(label)
        
        # If full match
        if match is not None and match.end() == len(label):
            # Special handling of first season
            if first_season and not match.group('season') in ('1', '', '01'):
                return False
            
            # Matched!
            plugin.log.debug("match: " + to_utf8(label))
            return True
            
        return False

    def _restore_viewid(self):
        xbmc.executebuiltin("Container.SetViewMode(%d)" % self.preserve_viewid)
        
    def _browse_external(self, path, guidance, parameters):
        # Escape parameters
        parameters = copy.deepcopy(parameters)
        for key, value in parameters.items():
            if isinstance(value, basestring):
                for c in IGNORE_CHARS:
                    value = value.replace(c, ' ')
                #parameters[key] = re.escape(value)
                parameters[key] = regex_escape(value)
        
        result_dirs = []
        result_files = []
        
        for i, hint in enumerate(guidance):
            # Stop early if requested
            if self.stop_flag.isSet() or xbmc.abortRequested:
                return [],[]
            
            # Path not found?
            if not path:
                break

            # List path directory
            try:
                _, dirs, files = list_dir(path)        
            except:
                break
            finally:
                self._restore_viewid()
            
            # Get matching directories
            matched_dirs = [x for x in dirs \
             if Lister._has_match(x, hint, parameters)]
            
            # Next path is first matched directory
            path = None
            if matched_dirs:
                path = matched_dirs[0]['path']

            # Last hint
            if i == len(guidance) - 1:
                # Get matching files
                result_files = [x for x in files \
                 if Lister._has_match(x, hint, parameters)]
                result_dirs = matched_dirs
                           
        # Always return some list (and not None)
        result_files = result_files or []
        result_dirs = result_dirs or []
        
        return result_files, result_dirs
