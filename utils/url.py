import urllib.parse
from rpaChallenge.utils.date import date_formatting
import config

class UrlParser:
    def __init__(self, query):
            self.query = query
            self.months = config.months
            self.formatted_endDate, self.formatted_startDate = date_formatting.calculate_dates(self.months)

    # Encoding URL
    def encode_query(self):
        return urllib.parse.quote(self.query)

    # Building URL
    def construct_url(self):
        query_encoded = self.encode_query()
        return f"https://www.nytimes.com/search?dropmab=false&endDate={self.formatted_endDate}&query={query_encoded}&sort=newest&startDate={self.formatted_startDate}"