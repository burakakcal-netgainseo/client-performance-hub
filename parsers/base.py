from abc import ABC, abstractmethod

class BaseParser(ABC):
    def __init__(self, client_config):
        self.client_config = client_config

    @abstractmethod
    def parse(self, email_msg):
        """
        Parse the email message and return a list of dictionaries,
        where each dictionary represents a row for the spreadsheet.
        Returns empty list if not applicable.
        """
        pass
