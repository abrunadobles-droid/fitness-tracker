"""
Cliente de Garmin Connect
"""
from garminconnect import Garmin
from datetime import datetime, timedelta
import config

class GarminClient:
    def __init__(self):
        self.client = None
    
    def login(self):
        self.client = Garmin(config.GARMIN_EMAIL, config.GARMIN_PASSWORD)
        self.client.login()
    
    def get_stats_for_date(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self.client.get_stats(date_str)
    
    def get_sleep_data(self, date=None):
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        return self.client.get_sleep_data(date_str)
    
    def get_activities(self, start_date=None, end_date=None, limit=10):
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        
        start = 0
        activities = self.client.get_activities(start, limit)
        return activities
