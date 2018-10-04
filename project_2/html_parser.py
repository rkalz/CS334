# USAGE:
# 1. Import
# 2. Create new HtmlHandler - handler
# 3. Pass parseHtml() the html recieved from http_handler
# 4. Do stuff with the returned array

class HtmlHandler:
    def parseHtml(self, html):
        from html.parser import HTMLParser
        flags = []
        links = []

        class MyHTMLParser(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    links.append(attrs)
                    
            def handle_data(self, data):
                print(data)
                if data[0:5] == "FLAG:":
                    flags.append(data)
                if data[0:4] == "http":
                    links.append(data)

        parser = MyHTMLParser()
        parser.feed(html)

        return flags, links

# Tests
if __name__ == "__main__":
    handler = HtmlHandler()
    print(handler.parseHtml('<h3>FLAG: 1234</h3><h3>FLAG: 12345678</h3><h1>No flag</h1><a href="https://www.uab.edu/">UAB</a><a href="https://www.uab2.edu/">UAB2</a>'))
