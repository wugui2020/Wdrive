from __future__ import print_function
import sys
import httplib2
import os
import io
import apiclient
from ast import literal_eval


import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret_426774337873-0jm29chokpdr9pm0scnla58ck6g1s0r3.apps.googleusercontent.com.json'
APPLICATION_NAME = 'Wdrive'

class GoogleDriveInstance():

    def __init__(self, argv):
        """Get the credentials and set the parameters for sync"""
        """local_path:  (String) The directory that will be local Google Drive folder."""
        """opt_list: (List) The list of IDs that will not be synced with the cloud."""

        self.local_path = os.getcwd()+"/googledrive"
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
        self.credentials = self.get_credentials()
        self.opt_list = self.get_configs()
        
        

        try:
            http = self.credentials.authorize(httplib2.Http())
            service = apiclient.discovery.build('drive', 'v3', http=http)
        except httplib2.ServerNotFoundError:
            print ("ServerNotFoundError: Please try again later")

        results = service.files().get(fileId='0B8lhn7ceZT9iYVgzd3lYdE9zSWM').execute()
        self.download_folder(results,self.local_path + '/Documents')

    def get_path(self):
        home_dir = os.path.expanduser('~')
        profile_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return profile_dir


    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        credential_dir = self.get_path()
        credential_path = os.path.join(credential_dir,
                                       'Wdrive.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def get_configs(self):
        config_dir = self.get_path()
        config_path = os.path.join(config_dir,
                                       'Wdrive.cfg')
        try:
            config = open(config_path, 'r')
            s = config.readline()
            OPTOUTLIST = s.split(",")
        except IOError:
            config = open(config_path, 'w')
            OPTOUTLIST = []
            config.write(",".join(OPTOUTLIST))
            print ("New profile established. Please use\n\t\twdrive ignore\nto opt out folders you don't want to be synced.")
        
        config.close()

        return OPTOUTLIST

    def opt_out(self,ID):
        config_dir = self.get_path()
        config_path = os.path.join(config_dir,
                                       'Wdrive.cfg')
        config = open(config_path, 'r+b')
        s = config.readline()
        OPTOUTLIST = s.split(",")
        OPTOUTLIST.append(ID)
        self.opt_list = OPTOUTLIST
        if ID not in self.opt_list:
            config.write(","+ID)
        config.close()
        return True

    def makedir_from_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print ("{0}".format(path))

    def get_files_by_folder(self, folder):
        files = service.files().list(q = "'{0}' in parents".format(folder)).execute()
        files  = files.get(['files'], [])
        return files

    def get_items_by_id(self, fileId):
        return

    def is_folder(self, file):
        return file['mimeType'] == 'application/vnd.google-apps.folder'

    def is_google_doc(self, file):
        return file['mimeType'][0:27] == "application/vnd.google-apps" 

    def download_folder(self, folder, base_path = "./"):
        self.makedir_from_path(base_path)
        http = self.credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('drive','v3',http=http)
        results = service.files().list(q="'{0}' in parents".format(folder['id'])).execute()
        while True:
            file_list = results.get('files',[])
            for file in file_list:
                if file['id'] in self.opt_list:
                    continue
                if self.is_folder(file):
                    self.download_folder(file, base_path + '/{0}'.format(file['name']))
                else:
                    file_path = os.path.join(base_path, file['name'])
                    if self.is_google_doc(file):
                        link_file = service.files().get(fileId = file['id'], fields = "webViewLink").execute()
                        with open("{0}/{1}.desktop".format(base_path,file['name']),'w') as shortcut:
                            shortcut.write("[Desktop Entry]\nEncoding=UTF-8\nName={0}\nURL={1}\nType=Link\nIcon=text-html\nName[en_US]=Google document link".format(file['name'],link_file['webViewLink']))
                        
                    else:
                        request = service.files().get_media(fileId=file['id'])
                        fh = io.FileIO(file_path,'wb')
                        downloader = apiclient.http.MediaIoBaseDownload(fh, request)
                        done = False
                        while done == False:
                            status, done = downloader.next_chunk()
                            print ("File {0} downloaded {1} %.".format( file['name'] ,int(status.progress() * 100)))
                        fh.close()
            if 'nextPageToken' in results:
                 results = service.files().list(pageToken = results['nextPageToken']).execute()
            else:
                break
        return





if __name__ == '__main__':
    drive = GoogleDriveInstance(sys.argv)
