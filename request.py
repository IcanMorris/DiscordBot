import requests # pip install requests
from html.parser import HTMLParser
import merch


class MerchWebsiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_stock_section = False
        self.recording_table = 0
        self.merch_items = []
        self.curr_merch_attrs = []
        self.curr_attr = 0
        self.curr_data = ''
        self.curr_img_key = ''
        self.skipped_head = False
        self.stock_date = ''

    def handle_starttag(self, tag, attrs):
        assert self.recording_table >= 0
        if self.recording_table:
            if tag != 'img':
                # print("inc !img: ", tag)
                self.recording_table += 1
                # print(self.recording_table)
            if tag == 'tbody':
                self.recording_table += 2
            if tag == 'tr':
                self.curr_attr = 0
            elif tag == 'td':
                assert self.curr_attr < 5
                self.curr_attr += 1
            elif tag == 'img':
                self.curr_img_key = [value for key, value in attrs if key == 'alt'][0]
        elif self.in_stock_section and tag == 'table':
            # print("inc table")
            self.recording_table += 1

    def handle_endtag(self, tag):
        assert self.recording_table >= 0
        if self.recording_table:
            # print(self.recording_table)
            self.recording_table -= 1
            if tag == 'tr':
                # print("tr found")
                if self.skipped_head:
                    assert all(value is not None for value in self.curr_merch_attrs)
                    assert len(self.curr_merch_attrs) == 5
                    self.merch_items.append(merch.MerchItem(*self.curr_merch_attrs))
                    self.curr_merch_attrs = []
                else:
                    self.skipped_head = True
            elif tag == 'td':
                # print("td found")
                self.curr_merch_attrs.append(self.curr_img_key if self.curr_attr == 1 else self.curr_data)
            if self.recording_table == 0:
                self.in_stock_section = False

    def handle_data(self, data):
        if data == 'Current stock':
            # self.output += 'found section'
            self.in_stock_section = True
        if self.recording_table and data not in ('\n', '[1]'):
            self.curr_data = data.strip()


def parse_merch_items():
    parser = MerchWebsiteParser()
    r = requests.get('https://runescape.wiki/w/Travelling_Merchant%27s_Shop')
    parser.feed(r.text)
    return parser.merch_items

class DateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.date = ''
        self.ye = False
        self.first = True
        self.line_num = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'i' and self.first:
            self.ye = True
            self.first = False

    def handle_endtag(self, tag):
        if tag == 'i' and self.ye:
            self.ye = False

    def handle_data(self, data):
        if self.ye:
            self.line_num += 1
            if self.line_num == 2 or self.line_num == 4:
                self.date += data + " "

def parse_stock_date():
    parser = DateParser()
    r = requests.get('https://runescape.wiki/w/Travelling_Merchant%27s_Shop')
    parser.feed(r.text)
    return parser.date[:2].strip()

parse_merch_items()