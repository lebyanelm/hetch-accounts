import nanoid
from datetime import timedelta, datetime

from models.time_created import TimeCreatedModel
from models.data import Data

""" Class for generating Authentication codes. """
class VerificationCodeModel(Data):
    def __init__(self, old_code = None):
        if old_code and old_code["code"]:
            self.code = old_code["code"]
            self.time_created = old_code["time_created"]
        else:
            self.code = nanoid.generate("0123456789", size=5)
            self.time_created = TimeCreatedModel().__dict__

    def verify(self, from_code: str) -> bool:
        return self.code == from_code