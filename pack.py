#!usrbinenv python
import re
import os
import zipfile

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

if __name__ == '__main__':
    os.system("del /S *.pyc")
    os.system("del /S *.pyo")
    os.system("del /S *.bak")

    addons = os.listdir(".")
    for addon in addons:
        try:
            # skip any file or .svn folder or .git folder
            if ( not os.path.isdir( addon ) or addon == ".svn" or addon == ".git" ): continue
            
            # create path
            _path = os.path.join( addon, "addon.xml" )
            # split lines for stripping
            #xml_lines = open( _path, "r" ).read().splitlines()
            #version = re.compile('version="(.*?)"').findall(xml_lines[1])[0]
            xml = open( _path, "r" ).read().replace("\r\n"," ").replace("\n"," ")
            version = re.compile('<addon.*?version="(.*?)"').findall(xml)[0]
            filename = "{0}-{1}.zip".format(addon, version)
            zippath = os.path.join('zip', addon, filename)
            try:
                os.makedirs(os.path.join('zip', addon))
            except:
                pass
            zipf = zipfile.ZipFile(zippath, 'w')
            zipdir(addon, zipf)
            zipf.close()
        except:
            pass
            
#    zipf = zipfile.ZipFile('Python.zip', 'w')
#    zipdir('tmp', zipf)
#    zipf.close()