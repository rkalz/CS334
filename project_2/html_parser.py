# USAGE:
# 1. Import
# 2. Create new HtmlHandler - handler
# 3. Pass parseHtml() the html recieved from http_handler
# 4. Do stuff with the returned array

class HtmlHandler:
    def parseHtml(self, html):
        from html.parser import HTMLParser
        flags = []

        class MyHTMLParser(HTMLParser):
            def handle_data(self, data):
                if data[0:5] == "FLAG:":
                    flags.append(data)

        parser = MyHTMLParser()
        parser.feed(html)

        return flags

# Tests
if __name__ == "__main__":
    handler = HtmlHandler()
    print(handler.parseHtml('<h3>FLAG: 1234</h3><h3>FLAG: 12345678</h3><h1>NOPE</h1>'))
