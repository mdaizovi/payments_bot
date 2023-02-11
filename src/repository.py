from gsheets import GSheetsClient
from settings import SPREADSHEET_NAME
from consts import TEXT_ANCHORS

class EventRepository():

    def __init__(self):
        self.db = GSheetsClient()
        self.spreadsheet = self.db.open_spreadsheet(sheet_input=SPREADSHEET_NAME)
        self.event = None

    def get_event_by_sheet_name(self, name):
        self.event = self.spreadsheet.worksheet(name)
        return self.event

    def get_event_by_sheet_index(self, index):
        self.event = self.spreadsheet.get_worksheet(index)
        return self.event

    def _get_value_by_anchor_text(self, text):
        # row_number = cell.row
        # column_number = cell.col
        # row and column coordinates:
        # val = worksheet.cell(1, 2).value
        anchor_cell = self.event.find(text)
        return self.event.cell(anchor_cell.row, anchor_cell.col + 1).value

    #TODO get address, etc
    def get_event_display_name(self):
        return self._get_value_by_anchor_text(TEXT_ANCHORS["EVENT_NAME"])
    
    def _get_event_price(self):
        return self._get_value_by_anchor_text(TEXT_ANCHORS["EVENT_PRICE"])
    
    def get_event_price_int(self):
        base_price = self._get_event_price()
        return int(float(base_price) * 100)

    def get_participants(self):
        contents = self.event.get_all_values()
        participant_anchor_cell = self.event.find(TEXT_ANCHORS["PARTICIPANTS"])
        return contents[participant_anchor_cell.row+1:]

    def add_participant(self, payload_value_list):
        # Get last record
        participant_anchor_cell = self.event.find(TEXT_ANCHORS["PARTICIPANTS"])
        participants = self.get_participants()
        # + 2: 1 for the header row in Participants, 1 to get next empty row 
        next_row = participant_anchor_cell.row + len(participants) + 2
        self.event.update(f"B{next_row}:I{next_row}", [payload_value_list])


    def event_is_full(self):
        max_participants = self._get_value_by_anchor_text(TEXT_ANCHORS["EVENT_MAX"])
        participants = self.get_participants()
        return len(participants) >= int(max_participants)