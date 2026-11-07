from dataclasses import dataclass
from google.oauth2.credentials import Credentials


@dataclass
class Agent_context:
    credentials:Credentials