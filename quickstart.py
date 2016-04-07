from __future__ import print_function
import sys
import httplib2
import os
import io
import apiclient


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

class GoogleDriveSession():

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
            OPTOUTLIST = config.readline().split(',')
        except IOError:
            config = open(config_path, 'w')
            OPTOUTLIST = []
            config.write(",".join(map(str,OPTOUTLIST)))
            print ("New profile established. Please use\n\t\twdrive ignore\nto opt out folders you don't want to be synced.")
        
        config.close()

        return OPTOUTLIST


    def update(LOCALPATH, credentials):
        http = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('drive','v3',http=http)
        results = service.files().list(q='mimeType = "application/pdf"').execute()
        items = results.get('files',[])
        for item in items:
            request = service.files().get_media(fileId=item['id'])
            item_path = os.path.join(LOCALPATH, item['name'])
            fh = io.FileIO(item_path,'wb')
            downloader = apiclient.http.MediaIoBaseDownload(fh, request)
            done = False
            while done == False:
                status, done = downloader.next_chunk()
                print ("File {0} downloaded {1} %.".format( item['name'] ,int(status.progress() * 100)))
            fh.close()
        return

    def download_file(LOCALPATH, credentials):
        http = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('drive','v3',http=http)
        results = service.files().list(q='mimeType = "application/pdf"').execute()
        items = results.get('files',[])
        for item in items:
            request = service.files().get_media(fileId=item['id'])
            item_path = os.path.join(LOCALPATH, item['name'])
            fh = io.FileIO(item_path,'wb')
            downloader = apiclient.http.MediaIoBaseDownload(fh, request)
            done = False
            while done == False:
                status, done = downloader.next_chunk()
                print ("File {0} downloaded {1} %%.".format( item['name'] ,int(status.progress() * 100)))
            fh.close()
        return



    def opt_out(ID):
        config_dir = get_path()
        config_path = os.path.join(config_dir,
                                       'Wdrive.cfg')
        config = open(config_path, 'r')
        OPTOUTLIST = config.readline().split(',')
        OPTOUTLIST.append(ID)
        config.write(",".join(map(str,OPTOUTLIST)))
        config.close()
        return True

if __name__ == '__main__':
    GoogleDriveSession(sys.argv)
