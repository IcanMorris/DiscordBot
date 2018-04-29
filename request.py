import requests # pip install requests
from html.parser import HTMLParser
import output


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

    def handle_starttag(self, tag, attrs):
        assert self.recording_table >= 0
        if self.recording_table:
            if tag != 'img':
                self.recording_table += 1
            if tag == 'tr':
                self.curr_attr = 0
            elif tag == 'td':
                assert self.curr_attr < 4
                self.curr_attr += 1
            elif tag == 'img':
                self.curr_img_key = [value for key, value in attrs if key == 'data-image-key'][0]
        elif self.in_stock_section and tag == 'table':
            self.recording_table += 1

    def handle_endtag(self, tag):
        assert self.recording_table >= 0
        if self.recording_table:
            self.recording_table -= 1
            if tag == 'tr':
                if self.skipped_head:
                    assert all(value is not None for value in self.curr_merch_attrs)
                    assert len(self.curr_merch_attrs) == 4
                    self.merch_items.append(output.MerchItem(*self.curr_merch_attrs))
                    self.curr_merch_attrs = []
                else:
                    self.skipped_head = True
            elif tag == 'td':
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
    r = requests.get('http://runescape.wikia.com/wiki/Travelling_Merchant%27s_Shop')
    parser.feed(r.text)
    return parser.merch_items