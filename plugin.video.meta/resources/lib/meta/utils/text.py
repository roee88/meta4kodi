import copy
import urllib
import time
from urlparse import urlparse, parse_qs, urlunparse
    
def to_utf8(obj):
    if isinstance(obj, unicode):
        obj = obj.encode('utf-8', 'ignore')
        
    elif isinstance(obj, dict):
        obj = copy.deepcopy(obj)
        for key, val in obj.items():
            obj[key] = to_utf8(val)
            
    elif obj is not None and hasattr(obj, "__iter__"):
        obj = obj.__class__([to_utf8(x) for x in obj])
        
    else:
        pass
        
    return obj

def to_unicode(obj):
    if isinstance(obj, basestring):
        try:
            obj = unicode(obj, 'utf-8')
        except TypeError:
            pass
            
    elif isinstance(obj, dict):
        obj = copy.deepcopy(obj)
        for key, val in obj.items():
            obj[key] = to_unicode(val)
            
    elif obj is not None and hasattr(obj, "__iter__"):
        obj = obj.__class__([to_unicode(x) for x in obj])
        
    else:
        pass
        
    return obj
        
def equals(a, b):
    return to_unicode(a) == to_unicode(b)
    
def is_ascii(s):
    try:
        if isinstance(s, basestring):
            s.decode()
        return True
    except UnicodeDecodeError:
        pass
    except UnicodeEncodeError:
        pass
    return False
    
def urlencode_path(path):
    path = to_utf8(path)
    o = urlparse(path)
    query = parse_qs(o.query)
    path = urlunparse([o.scheme, o.netloc, o.path, o.params, urllib.urlencode(query, True), o.fragment])
    return path

def parse_year(text):
    try:
        return text.split("-")[0].strip()  
    except:
        return '0'
        
def date_to_timestamp(date_str, format="%Y-%m-%d"):
    if date_str:
        try:
            tt = time.strptime(date_str, format)    
            return int(time.mktime(tt))
        except:
            return 0 # 1970
    return None
