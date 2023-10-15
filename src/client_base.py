import gspread
from oauth2client.service_account import ServiceAccountCredentials


# idea from:
# https://towardsdatascience.com/turn-google-sheets-into-your-own-database-with-python-4aa0b4360ce7
# docs:
# https://docs.gspread.org/en/latest/user-guide.html#sharing-a-spreadsheet


class ClientBase():

    def __init__(self):
        # so bad i don't care fix later
        self.client = self._client()
        self.spreadsheet = None

    def _client(self):
        credentials = self._build_creds()
        #return gspread.authorize(credentials)
    
    def _build_creds(self):
        # Connect to Google
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive"
            ]

        return ServiceAccountCredentials.from_json_keyfile_name("creds/gs_credentials.json", scope)
    

