import gspread
from client_base import ClientBase
from settings import SPREADSHEET_NAME

# idea from:
# https://towardsdatascience.com/turn-google-sheets-into-your-own-database-with-python-4aa0b4360ce7
# docs:
# https://docs.gspread.org/en/latest/user-guide.html#sharing-a-spreadsheet


class GSheetsClient(ClientBase):

    def _client(self):
        credentials = self._build_creds()
        return gspread.authorize(credentials)
    
    def create_spreadsheet(self, sheet_name):
        return self.client.create(sheet_name)
    
    def open_spreadsheet(self, sheet_input):
        # Open the spreadsheet. Can also do open_by_key, open_by_url
        # <Spreadsheet 'Telegram Bookings Backend' id:1wekJwtLxqWINkQ8OTXB_rK9LHGxaqpfoMKa9Zthh3-Y>
        try:
            self.spreadsheet = self.client.open(sheet_input)
        except gspread.exceptions.SpreadsheetNotFound:
            try:
                self.spreadsheet = self.client.open_by_url(sheet_input)
            except gspread.exceptions.NoValidUrlKeyFound:
                self.spreadsheet = self.client.open_by_key(sheet_input)
                # gspread.exceptions.APIError
                # just let the last one raise.
        return self.spreadsheet

    def get_or_create_spreadsheet(self, sheet_name):
        # only accepts sheet name, not key or url
        try:
            self.spreadsheet = self.client.open(sheet_name)
        except gspread.exceptions.SpreadsheetNotFound:
            self.spreadsheet = self.create_spreadsheet(sheet_name)
        return self.spreadsheet

    def share_spreadsheet(self, sheet_input, email):
        if not self.spreadsheet:
            self.open_spreadsheet(sheet_input)
        return self.spreadsheet.share(email, perm_type='user', role='writer')
