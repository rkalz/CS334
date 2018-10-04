class HtmlHandler:
    def parseHtml(self, html):
        from bs4 import BeautifulSoup, SoupStrainer
        soup = BeautifulSoup(html, 'html.parser')

        links = []

        for link in soup.find_all('a', href=True):
            links.append(link['href'])
        
        return links

# Tests
if __name__ == "__main__":
    html = """
    """

    handler = HtmlHandler()
    print(handler.parseHtml(html))
