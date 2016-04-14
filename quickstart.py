from __future__ import print_function
import sys
import httplib2
import os
import io
import apiclient
import time
import sqlite3
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
SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/activity'
CLIENT_SECRET_FILE = 'client_secret_426774337873-0jm29chokpdr9pm0scnla58ck6g1s0r3.apps.googleusercontent.com.json'
APPLICATION_NAME = 'Wdrive'

class GoogleDriveInstance():

    def __init__(self, argv):
        """Get the credentials and set the parameters for sync"""
        """local_path:  (String) The directory that will be local Google Drive folder."""
        """opt_list: (List) The list of IDs that will not be synced with the cloud."""

        self.local_path = os.getcwd()+"/googledrive/"
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
        self.credentials = self.get_credentials()
        self.index_database = sqlite3.connect('./.database/drive.db')
        self.database_cursor = self.index_database.cursor()
        self.opt_list, self.change_page_token,self.last_check_time = self.get_configs()
        

        try:
            self.http = self.credentials.authorize(httplib2.Http())
            self.service = apiclient.discovery.build('drive', 'v3', http=self.http)
        except httplib2.ServerNotFoundError:
            print ("ServerNotFoundError: Please try again later")

#        results = self.service.files().get(fileId='0B8lhn7ceZT9iZWN5LU50V0xFbWs').execute()
#        self.download_folder(results,self.local_path + '/test')
#        self.detect_changes()
        
        self.detect_acticities()
        
    def get_file_from_db(self, fileId):
        results = self.database_cursor.execute(
                "SELECT * FROM files WHERE fileId =?", fileId)
        for row in results:
            return GoogleDriveInstance(row)


    def get_path(self):
        home_dir = os.path.expanduser('~')
        profile_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return profile_dir

    def get_file_path(self, fileId):
        base_path = self.local_path
        extend_path = []
        #root_response = self.service.files().list(q = "'root' in parents").execute()
        #root_fileId = response['files']['id'] 
        #root_file = self.service.files().get(fileId = root_fileId).execute()
        #rootId = root_file['parents']
        item = self.service.files().get(fileId = fileId, fields = 'name, parents').execute()

        while True:
            fileId = item['parents'][0]
            item = self.service.files().get(fileId = fileId, fields = 'name, parents').execute()
            if 'parents' not in item:
                break
            extend_path.append(item['name'])
        extend_path.reverse()

        return base_path + "/".join(extend_path)


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
            s = config.readline().strip()
            OPTOUTLIST = s.split(",")
            s = config.readline().strip()
            if s != '' and s != 'None':
                change_page_token = int(s)
            else:
                change_page_token = None
            s = config.readline().strip()
            last_check_time = int(s)

        except IOError:
            config = open(config_path, 'w')
            OPTOUTLIST = []
            change_page_token = None
            last_check_time = int(round(time.time()*1000))
            config.write(",".join(OPTOUTLIST)+'\n'+str(change_page_token)+'\n'+str(last_check_time))
            print ("New profile established. Please use\n\t\twdrive ignore\nto opt out folders you don't want to be synced.")
        
        config.close()

        return OPTOUTLIST, change_page_token, last_check_time

    def update_configs(self):
        config_dir = self.get_path()
        config_path = os.path.join(config_dir,
                                       'Wdrive.cfg')
        config = open(config_path, 'w')
        OPTOUTLIST = self.opt_list
        change_page_token = self.change_page_token
        last_check_time = self.last_check_time
        config.write(",".join(OPTOUTLIST)+'\n'+str(change_page_token)+'\n'+str(last_check_time))
        config.close()


    def opt_out(self,ID):
        if ID not in self.opt_list:
            self.opt_list.append(ID)
            self.update_configs()
        return True

    def opt_in(self,ID):
        if ID in self.opt_list:
            self.opt_list.pop(self.opt_list.index(ID))
            self.update_configs()
        return True


    def makedir_from_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print ("{0}".format(path))

    def get_files_by_folder(self, folder):
        files = self.service.files().list(q = "'{0}' in parents".format(folder)).execute()
        files  = files.get(['files'], [])
        return files


    def download_fileInstance(self, fileInstance, base_path = "./"):
        if self.is_folder(fileInstance):
            self.download_folder(fileInstance, base_path + '/{0}'.format(fileInstance.name))
        else:
            file_path = os.path.join(base_path, fileInstance.name)
            fileInstance.path = file_path
            if fileInstance.is_google_doc:
                link_fileInstance = self.service.file().get(fileId = fileInstance.fileId, fields = "webViewLink").execute()
                with open("{0}/{1}.desktop".format(base_path,fileInstance.name),'w') as shortcut:
                    shortcut.write("[Desktop Entry]\nEncoding=UTF-8\nName={0}\nURL={1}\nType=Link\nIcon=text-html\nName[en_US]=Google document link".format(fileInstance.name,link_fileInstance['webViewLink']))
                
            else:
                request = self.service.file().get_media(fileId=fileInstance.fileId)
                fh = io.FileIO(file_path,'wb')
                downloader = apiclient.http.MediaIoBaseDownload(fh, request)
                done = False
                while done == False:
                    status, done = downloader.next_chunk()
                    print ("File {0} downloaded {1} %.".format( fileInstance.name ,int(status.progress() * 100)))
                fh.close()

    def download_folder(self, folder, base_path = "./"):
        self.makedir_from_path(base_path)
        results = self.service.files().list(q="'{0}' in parents".format(folder['id'])).execute()
        while True:
            file_list = results.get('files',[])
            for file in file_list:
                if file['id'] in self.opt_list:
                    return
                fileInstance = GoogleDriveInstance(file)
                self.index_dict[fild['id']] = fileInstance
                self.download_file(fileInstance)
            if 'nextPageToken' in results:
                 results = self.service.files().list(pageToken = results['nextPageToken']).execute()
            else:
                break
        return

    def detect_acticities(self):
        service = apiclient.discovery.build('appsactivity','v1', http = self.http)
        results = service.activities().list(
                source='drive.google.com',
                groupingStrategy='driveUi',
                drive_ancestorId='root', 
                pageSize=10
                ).execute()
        activities = results.get('activities', [])
        last_check_time = self.last_check_time
        self.last_check_time = activities[0]['combinedEvent']['eventTimeMillis']
        self.update_configs()

        while True:
            if not activities:
                print('No activity.')
            else:
                print('Activities since the last check:')
                for activity in activities:
                    events = activity['singleEvents']
                    for event in events:
                        eventTime = int(event['eventTimeMillis'])
                        if eventTime <= last_check_time:
                            return
                        user = event.get('user', None)
                        target = event.get('target', None)
                        if self.is_google_doc(target) == True:
                            continue
                        print('{0}: {1}, {2}, {3} ({4})'.format(
                            eventTime, 
                            user['name'],
                            event['primaryEventType'], 
                            target['name'], 
                            target['mimeType']
                            ))
                        #self.handle_event(event)
            if 'nextPageToken' in results:
                results = service.activities().list(
                        source='drive.google.com',
                        drive_ancestorId='root', 
                        pageToken=results['nextPageToken'],
                        pageSize=10
                        ).execute()
                activities = results.get('activities', [])
            else:
                break

    def handle_event(self, event):
        eventType = event['primaryEventType']
        fileId = event['target']['id']
        if eventType == 'trash':
            pass
        elif eventType == 'create':
            path = self.get_file_path(fileId)
            self.download_file(file, path)
        elif eventType == 'rename':
            path = self.get_file_path(fileId)
            os.rename(path + event['oldTitle'], path + event['newTitle'])
        return

    def detect_changes(self):
        print (self.change_page_token)
        if self.change_page_token == None:
            response = self.service.changes().getStartPageToken().execute()
            self.change_page_token = response.get('startPageToken')
        page_token = self.change_page_token
        while page_token != None:
            response = self.service.changes().list(
                    pageToken = page_token,
                    spaces='drive'
                    ).execute()
            print (self.change_page_token)
            print (response.get('changes'))
            for change in response.get('changes'):
                fileId = change.get('fileId')
                if fileId in self.opt_list:
                    continue
                file = self.service.files().get(fileId = fileId, fields = "id,name,mimeType,parents").execute()
                print (file)
                if self.is_google_doc(file) == False and 'parents' in file:
                    print ("{0}".format(file['id']))
                    print (self.is_folder(file))
                    if self.is_folder(file) == True:
                        print (file['name'])
                    #path = self.get_file_path(fileId)
                    #self.download_file(file, path)
            if 'newStartPageToken' in response:
                self.change_page_token = response.get('newStartPageToken')
            page_token = response.get('nextPageToken')
        self.update_configs()

class GoogleDriveFile():
    def __init__(self, row):
        self.id,
        self.fileid, 
        self.name, 
        self.mimeType, 
        self.path, 
        self.parents, 
        self.last_modified = row

    def is_folder(self):
        return self.mimeType == 'application/vnd.google-apps.folder'

    def is_google_doc(self):
        return self.mimeType in ["application/vnd.google-apps.document","application/vnd.google-apps.presentation","application/vnd.google-apps.script","application/vnd.google-apps.spreadsheet","application/vnd.google-apps.form","application/vnd.google-apps.drawing","application/vnd.google-apps.map","application/vnd.google-apps.sites"] 





if __name__ == '__main__':
    drive = GoogleDriveInstance(sys.argv)
