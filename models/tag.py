# dependencies
from models.data import Data

class Tag(Data):
	def __init__(self, name, is_automatic=False):
		super().__init__()

		self.name = name
		self.reads = 0
		self.searches = 0
		self.related_eggs = []
		self.eggs_count = 0

		_schema_version_ = 2022.01
