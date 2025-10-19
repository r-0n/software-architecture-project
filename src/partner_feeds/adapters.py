# src/partner_feeds/adapters.py
from abc import ABC, abstractmethod
import csv
import json
from typing import List, Dict

class FeedAdapter(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        pass

class CSVFeedAdapter(FeedAdapter):
    def parse(self, file_path: str) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [dict(row) for row in reader]

class JSONFeedAdapter(FeedAdapter):
    def parse(self, file_path: str) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

class FeedAdapterFactory:
    @staticmethod
    def get_adapter(format_type: str) -> FeedAdapter:
        adapters = {
            'CSV': CSVFeedAdapter(),
            'JSON': JSONFeedAdapter()
        }
        return adapters.get(format_type.upper())