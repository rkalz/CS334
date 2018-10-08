class HtmlHandler:
    def parseHtml(self, html):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        links = []
        flags = []
        if html != None:
            for link in soup.find_all('a', href=True):
                links.append(link['href'])
            for line in soup.find_all('h3',attrs={"class" : "secret_flag"}):
                flags.append(line.text)
        
        return links, flags

# Tests
if __name__ == "__main__":
    html = """
        <html>
            <body>
                <p>I'm a paragraph</p>
                <h3 class='secret_flag'>FLAG: 12klj3123jn1kj321</h3>
                <h3 class='secret_flag'>FLAG: 1293891023j21i31j2nnkj</h3>
                <a href="http://example.com"/>
                <a href="https://example.com"/>
            </body>
        </html>
    """

    handler = HtmlHandler()
    parsed = handler.parseHtml(html)
    # Print both returned arrays
    print(parsed)
    # Accessing the first array [0] ( the links ), at the 2nd position [1]
    print(parsed[0][1])
