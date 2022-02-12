import requests, json

class SearchTenor:

    def __init__(self):
        self.apikey = "KRW5EO7DDGWE"

    def fetch_gif_data(self, search_term, limit):
        response = requests.get(
            f"https://g.tenor.com/v1/search?q={search_term}&key={self.apikey}&limit={limit}"
        )
        self.gif_data = json.loads(response.content)
        return self.gif_data