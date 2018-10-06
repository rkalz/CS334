from html.parser import HTMLParser

class HTMLHandler(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            link = dict(attrs).get('href')