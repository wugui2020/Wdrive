from __future__ import print_function
import sys
import httplib2
import os
import io
import apiclient
import time
import sqlite3
from ast import literal_eval
from shutil import rmtree
from shutil import move


import oauth2client
from oauth2client import client
from oauth2client import tools


SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/activity'
CLIENT_SECRET_FILE = 'client_secret_426774337873-0jm29chokpdr9pm0scnla58ck6g1s0r3.apps.googleusercontent.com.json'
APPLICATION_NAME = 'Wdrive'

"""
=========================
  Google Drive Instance
=========================
"""


class GoogleDriveInstance():

    def __init__(self, argv):
        """Get the credentials, setup the database and set the parameters for sync"""
	"""credentials: (Object) The credential interface from Drive API"""
        """index_database: (Object) The database for file indexing."""
	"""local_path:  (String) The directory that will be local Google Drive folder."""
        """opt_list: (List) The list of IDs that will not be synced with the cloud."""
	"""change_page_token: (String) The string for Drive change queries."""
	"""last_check_time: (Integer) Time when the last change happened in milisec from epoc."""
	
        print (argv)

        self.local_path = os.getcwd()+"/googledrive/"
        if not os.path.exists(self.local_path):
            os.makedirs(self.local_path)
        self.credentials = self.get_credentials()
        self.index_database = sqlite3.connect('./drive.db')
        self.database_cursor = self.index_database.cursor()

        self.opt_list, self.change_page_token,self.last_check_time = self.get_configs()
        try:
            self.http = self.credentials.authorize(httplib2.Http())
            self.service = apiclient.discovery.build('drive', 'v3', http=self.http)
        except httplib2.ServerNotFoundError:
            print ("ServerNotFoundError: Please try again later")
        root_folder = self.service.files().list(q = "'root' in parents", fields = "files(parents)").execute()

        self.root_id = root_folder['files'][0]['parents'][0]

        self.database_cursor.execute(
                """SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'files'""")
        exist = self.database_cursor.fetchall()
        if exist == []:
            self.database_cursor.execute(
                """CREATE TABLE files
                (
                fileId text,
                name text,
                path text,
                inode integer,
                parents text,
                isFolder integer,
                UNIQUE (fileId)
                )""")
            self.index_database.commit()
        if argv[1] == '-i':
            folder = self.service.files().get(fileId = self.root_id).execute()
            self.download_folder(folder, "./googledrive")
        elif argv[1] == '-out':
            opt_name = argv[2]
            file = self.service.files().list(q = 'name = "{0}"'.format(opt_name))
            self.opt_out(file['id'])
        elif argv[1] == '-in':
            opt_name = argv[2]
            file = self.service.files().list(q = 'name = "{0}"'.format(opt_name))
            self.opt_in(file['id'])
        elif argv[1] == "-push":
            self.check_local_changes()
        elif argv[1] == "-pull":
            self.detect_changes()
        else:
            print "wrong argument"


            #self.database_cursor.execute(
            #        """DROP TABLE files
            #        """)


    """
    ===============================
	Drive Instace Operations
    ===============================
    """
    

    def get_inf_path(self):
        home_dir = os.path.expanduser('~')
        profile_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        return profile_dir


    def makedir_from_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print ("{0}".format(path))
        
    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        credential_dir = self.get_inf_path()
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
        config_dir = self.get_inf_path()
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
        config_dir = self.get_inf_path()
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
    
    def change_filter(self, change):
        fileId = change.get('fileId')
        print ("fileid",fileId)
        file = change.get('file')
        if 'parents' not  in file:
            return None
        while fileId not in self.opt_list and fileId != self.root_id:
            entry = self.query_file_via_fileId(fileId)
            if entry == None:
                while True:
                    try:
                        results = self.service.files().get(fileId = fileId, fields = "parents").execute()
                        break
                    except apiclient.errors.HttpError:
                        time.sleep(1)
                if 'parents' not in results:
                    return None
                fileId = results['parents'][0]
            else:
                return file

        return None


    def detect_changes(self):
        if self.change_page_token == None:
            response = self.service.changes().getStartPageToken().execute()
            self.change_page_token = response.get('startPageToken')
        page_token = self.change_page_token
        while page_token != None:
            response = self.service.changes().list(
                    pageToken = page_token,
                    fields = "changes(fileId, file(id, name, mimeType, parents, trashed)), nextPageToken, newStartPageToken",
                    spaces='drive'
                    ).execute()
            for change in response.get('changes'):
                file = self.change_filter(change)
                if file == None:
                    continue
                self.handle_changes(file)
		    # 'parents in file means it's in your drive'
                                        #path = self.get_file_path(fileId)
                    #self.download_file(file, path)
            if 'newStartPageToken' in response:
                self.change_page_token = response.get('newStartPageToken')
            page_token = response.get('nextPageToken')
        print (self.change_page_token)
        self.update_configs()

    def handle_changes(self, file):
        if file['trashed'] == True:
            entry = self.query_file_via_fileId(file['id'])
            print("entry",entry)
            path = os.path.join(entry[2],entry[1])
            if self.is_folder(file) == True:
                rmtree(path)
            else:
                os.remove(path)
            self.database_cursor.execute(
                    """
                    DELETE FROM files
                    WHERE fileId =?
                    """, (file['id'],))
            self.index_database.commit()
            print ("{0} has been deleted.".format(file['name']))
            return
        else:
            self.database_cursor.execute(
                    """
                    SELECT * FROM files
                    WHERE fileId = ?
                    """
                    ,(file['id'],))
            exist = self.database_cursor.fetchall()
            print ("exist",exist)

            if exist != []:
                parent_on_file = exist[0][4]
                path = exist[0][2]
                name = exist[0][1]
                if parent_on_file == file['parents'][0]:
                    if name != file['name']:
                        old_name = os.path.join(path, name)
                        new_name = os.path.join(path, file['name'])
                        if self.is_google_doc(file):
                            oldname += ".desktop"
                            newname += ".desktop"
                        os.rename(old_name, new_name)
                else:
                    newpath = self.get_file_path(file)
                    oldpath = os.path.join(path, name)
                    if self.is_google_doc(file):
                        oldpath += ".desktop"
                        newpath += ".desktop"
                    move(oldpath, newpath)
                if self.is_folder(file) == True:
                    self.folder_path_update(file) # recursive path update to be implemented

            else:
                path = self.get_file_path(file)
                if self.is_folder(file):
                    self.download_folder(file, path)
                else:
                    self.download_file(file, path)

            stat = os.stat(path)
            inode = stat.st_ino
            self.log_database(file, path, inode)

        print ("{0} has been updated.".format(file['name']))

        return
        
    def folder_path_update(self, file):
        print ("folder path update", file)
    	self.database_cursor.execute(
    		"""
    		SELECT name, fileId
    		FROM files
    		WHERE fileId = ?
    		"""
    		,(file['id'],))
    	entry = self.database_cursor.fetchall()
        print ("entry", entry)
    	name_on_file = entry[0][0]
    	results = self.database_cursor.execute(
    		"""
    		SELECT fileId, parents, isFolder
    		FROM files
    		WHERE parents = ?
    		""", (file['id'],))
    	for row in results:
    		path = os.path.join(self.get_file_path(file), file['name'])
		results = self.database_cursor.execute(
	    		"""
	    		UPDATE files
	    		SET path = ?
	    		WHERE parents = ?
	    		""", (path, file['id']))
	    	self.index_database.commit()
	    	if row[2] == 1:
    		    item = self.service.files().get(fileId = row[0]).execute()
	    	    self.folder_path_update(item)

    def log_database(self, file, path, inode):
        checker = self.database_cursor.execute(
                """
                SELECT * FROM files
                WHERE fileId = ?
                """, (file['id'],))
        exist = self.database_cursor.fetchall()
        isFolder = [0,1][self.is_folder(file)]

        if exist:
            self.database_cursor.execute(
                    """
                    UPDATE files
                    SET name = ?, path = ?, inode = ?, parents = ?, isFolder = ?
                    WHERE fileId = ?;
                    """
                    , (file['name'], path, inode, file['parents'][0], isFolder, file['id']))
        else:   

            self.database_cursor.execute(
                """
                INSERT INTO files 
                VALUES(?,?,?,?,?,?) 
                """
                ,(file['id'], file['name'], path, inode, file['parents'][0], isFolder))
        self.index_database.commit()
        return

    def list_database_files(self):
        results = self.database_cursor.execute(
                """
                SELECT * FROM files
                """)
        for row in results:
            print (row)

    def check_local_changes(self):
        base_path = self.local_path + '222'
        missing, new = [], []
        for path, dir_list, file_list in os.walk(base_path):
            local_files = dir_list + file_list
            # missing file check
            all_files_in_db = self.query_local_file(path)
            for file in all_files_in_db:
                if len(file[0]) > 28:
                    file_name = file[1] + ".desktop"
                else:
                    file_name = file[1]
                file_path = os.path.join(path, file_name)
                print (file_path)
                if os.path.exists(file_path) == False:
                    missing.append(file[0])
                else:
                    stats = os.stat(file_path)
                    if stats.st_ino != file[3]:
                        print (stats.st_ino, file[3])
                        missing.append(file[0])
            i = 0
            while i < len(local_files):
                if local_files[i].endswith('.desktop'):
                    i += 1
                    continue
                exist = self.query_local_file(path, name = file_name)
                if exist == None:
                    file_name = local_files.pop(i)
                    parent = self.query_local_file(path)[0][4]
                    file_path = os.path.join(path, file_name)
                    is_folder = os.path.isdir(file_path)
                    new.append((path, file_name, parent,is_folder))
                else:
                    i += 1
            i = 0
            while i < len(local_files):
                if local_files[i].endswith('.desktop'):
                    i += 1
                    continue
                stats = os.stat(os.path.join(path, local_files[i]))
                exist = self.query_local_file(path, inode = stats[1])
                if exist == None:
                    file_name = local_files.pop(i)
                    parent = self.query_local_file(path)[0][4]
                    file_path = os.path.join(path, file_name)
                    is_folder = os.path.isdir(file_path)
                    new.append((path,file_name, parent,is_folder))
                else:
                    i += 1
        print ("missing", missing, "new", new)
        self.files_update(missing, new)
        return

    def files_update(self, missing, new):
        for file_id in missing:
            self.service.files().update(body = {'trashed':True}, fileId = file_id).execute()
            self.database_cursor.execute(
                    "DELETE FROM files WHERE fileId = ?", (file_id,))
            self.index_database.commit()
        if new != []:
            id_list = self.service.files().generateIds(count = len(new)).execute()
            for file_path, file_name, parent, is_folder in new:
                newfile_id = id_list['ids'].pop()
                if file_name.endswith('.desktop'): 
                    name = file_name[:-8]
                else:
                    name = file_name
                data = {'id':newfile_id, 'name':name, 'parents':[parent]}
                path = os.path.join(file_path, file_name)
                if is_folder:
                    data['mimeType'] = 'application/vnd.google-apps.folder'
                    self.service.files().create(body = data).execute()
                    is_folder = 1
                else:
                    media = apiclient.http.MediaFileUpload(path, resumable = True)
                    self.service.files().create(body = data, media_body = media).execute()
                    is_folder = 0
                inode = os.stat(path).st_ino
                self.database_cursor.execute(
                        "INSERT INTO files VALUES (?,?,?,?,?,?)", (newfile_id, name, file_path, inode, parent, is_folder))
                self.index_database.commit()
        response = self.service.changes().getStartPageToken().execute()
        self.change_page_token = response.get('startPageToken')
        self.update_configs()

        return

    """
    ==============================
          File Operations
    ==============================
    """



    def query_local_file(self, path, name = None, inode = None):
        if name == None and inode == None:
            results = self.database_cursor.execute(
                    "SELECT * FROM files WHERE path =?", (path,))
            return results.fetchall()
        if name != None and inode == None: # query by name and path --- rename check
            results = self.database_cursor.execute(
                    "SELECT * FROM files WHERE path =? and name = ?", (path, name))
            for row in results:
                return row
        else: # query by inode and path --- edit check
            results = self.database_cursor.execute(
                    "SELECT * FROM files WHERE path =? and inode = ?", (path, inode))
            for row in results:
                return row


    
        
    def query_file_via_fileId(self, fileId = None):
	if fileId == None:
	    print ("No id provided")
	    return
        results = self.database_cursor.execute(
                "SELECT * FROM files WHERE fileId =?", (fileId,))
        for row in results:
            return row


    def is_folder(self,file):
        return file['mimeType'] == 'application/vnd.google-apps.folder'

    def is_google_doc(self, file):
        return file['mimeType'] in ["application/vnd.google-apps.document","application/vnd.google-apps.presentation","application/vnd.google-apps.script","application/vnd.google-apps.spreadsheet","application/vnd.google-apps.form","application/vnd.google-apps.drawing","application/vnd.google-apps.map","application/vnd.google-apps.sites"] 


    def download_file(self, file, base_path = "./"):
        inode = 0
        if self.is_folder(file) == True:
            self.download_folder(file, base_path + '/{0}'.format(file['name']))
            file_path =  base_path + '/{0}'.format(file['name'])
        else:
            file_path = os.path.join(base_path, file['name'])
            fileId = file['id']
            if self.is_google_doc(file):
                link_file = self.service.files().get(fileId = fileId, fields = "webViewLink").execute()
                file_path += ".desktop"
                with open("{0}/{1}.desktop".format(base_path,file['name']),'w') as shortcut:
                    shortcut.write("[Desktop Entry]\nEncoding=UTF-8\nName={0}\nURL={1}\nType=Link\nIcon=text-html\nName[en_US]=Google document link".format(file['name'],link_file['webViewLink']))
                
            else:
                request = self.service.files().get_media(fileId=fileId)
                fh = io.FileIO(file_path,'wb')
                downloader = apiclient.http.MediaIoBaseDownload(fh, request)
                done = False
                while done == False:
                    status, done = downloader.next_chunk()
                    print ("File {0} downloaded {1} %.".format( file['name'] ,int(status.progress() * 100)))
                fh.close()
        stat = os.stat(file_path)
        inode = stat.st_ino
        self.log_database(file, base_path, inode)

    def download_folder(self, folder, base_path = "./"):
        print (folder)
        self.makedir_from_path(base_path)
        results = self.service.files().list(q="'{0}' in parents".format(folder['id']), fields = "files(id, name, mimeType, parents, trashed)").execute()
        while True:
            file_list = results['files']
            for file in file_list:
                if file['id'] in self.opt_list or file['trashed'] == True:
                    continue
                self.download_file(file, base_path)
            if 'nextPageToken' in results:
                 results = self.service.files().list(pageToken = results['nextPageToken']).execute()
            else:
                break
        return

    def get_file_path(self, file):
        extend_path = []
        entry = self.query_file_via_fileId(file['id'])
        print (entry)
        while entry == None:
            parent_Id = file['parents'][0]
            item = self.service.files().get(fileId = parent_Id, fields = 'id, name, parents').execute()
            print ("file", item)
            if 'parents' not in item:
                base_path = self.local_path
                extend_path.reverse()
                return base_path + '/' + "/".join(extend_path)
            extend_path.append(item['name'])
            entry = self.query_file_via_fileId(item['id'])
            print (entry)
        base_path = entry[2]
        extend_path.reverse()
        final = base_path + '/' + "/".join(extend_path)
        return final
    """
    ========================
       Outdated functions
    ========================
    """
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



    def get_files_by_folder(self, folder):
        files = self.service.files().list(q = "'{0}' in parents".format(folder)).execute()
        files  = files.get(['files'], [])
        return files




if __name__ == '__main__':
    drive = GoogleDriveInstance(sys.argv)
    #results = drive.service.files().get(fileId='0B8lhn7ceZT9iZWN5LU50V0xFbWs', fields = "id, name, mimeType, parents").execute()
    #drive.download_folder(results,drive.local_path + '222')
    
#    drive.detect_changes()
    #drive.list_database_files()
#    drive.check_local_changes()
#    print ([0,1][drive.is_folder(results)])
#    print (drive.change_page_token)
#    print (drive.change_page_token)
#    results = drive.service.files().get(fileId='1k5r3spjkSQa6OntFfJRLIfUztoAPnGxXhyvlOfQ7OR4', fields="name, id, parents").execute()
#    print (results)
#    print (drive.get_file_path(results))
