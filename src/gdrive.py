from collections import OrderedDict
from client_base import ClientBase
from googleapiclient.discovery import build


class GDriveClient(ClientBase):

    def get_file_list_from_directory(self, folder_id):
        # folder_id: Get the ID of the folder you want to list files from.
        # folder ids: 
        # Sabine
        # 1QBDjWsALZe20jXmdtMI9ziH8sVtG-oXE
        # Panke
        # 1gLTEsDUKTkXfvve4-k7YS8jTp5Xk4Fox
        credentials = self._build_creds()
        
        service = build('drive', 'v3', credentials=credentials)

        # Call the Drive v3 API
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="nextPageToken, files(name)").execute()
        items = results.get('files', [])

        name_link_dict = OrderedDict()
        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                name = item['name']
                url = item['webViewLink']
                print(u'{0}'.format(item['name']))
                name_link_dict[name] = url
        
        return name_link_dict

