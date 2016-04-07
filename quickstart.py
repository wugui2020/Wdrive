from __future__ import print_function
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
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
CLIENT_SECRET_FILE = 'client_secret_426774337873-0jm29chokpdr9pm0scnla58ck6g1s0r3.apps.googleusercontent.com.json'
APPLICATION_NAME = 'Wdrive'


def get_path():
    home_dir = os.path.expanduser('~')
    profile_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    return profile_dir


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = get_path()
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

def get_configs():
    config_dir = get_path()
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


def initialze():
    """Get the credentials and set the parameters for sync"""
    """LOCALPATH:  (String) The directory that will be local Google Drive folder."""
    """OPTOUTLIST: (List) The list of IDs that will not be synced with the cloud."""

    LOCALPATH = os.getcwd()+"/googledrive"
    print (LOCALPATH)
    if not os.path.exists(LOCALPATH):
        os.makedirs(LOCALPATH)
    credentials = get_credentials()
    OPTOUTLIST = get_configs()

    try:
        http = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('drive', 'v3', http=http)
    except httplib2.ServerNotFoundError:
        print ("ServerNotFoundError: Please try again later")
    update(credentials)

def update(credentials):
    http = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('drive','v3',http=http)
    results = service.files().list().execute()
    items = results.get('files',[])
    request = service.files().get(fileId="1IBpyvYnXHMHxWqw9X5ulVw-B58HOxzf7Et8h3w0RWdU").execute()
    print (request)
    #fh = io.BytesIO()
    #downloader = apiclient.http.MediaIoBaseDownload(fh, request)
    #done = False
    #while done == False:
    #    status, done = downloader.next_chunk()
    #    print ("downloaded %d %%." % int(status.progress() * 100))
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
    initialze()
