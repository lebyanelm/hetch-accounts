import bson
from models.data import Data


class Comment(Data):
	def __init__(self, data):
		super().__init__()

		self.parent_egg = data.get("parent_egg")
		if self.parent_egg is not None:
			self.parent_egg = bson.objectid.ObjectId(self.parent_egg)
		
		self.body = data.get("body")
		self.commenter = data.get("commenter")

		self.reply_of = data.get("reply_of")
		if self.reply_of is not None:
			self.reply_of = bson.objectid.ObjectId(self.reply_of)

		self.replies = data.get("replies")
		if self.replies == None:
			self.replies = []
            
 		self.likes = []
		self.likes_count = 0

		self.dislikes = []
		self.dislikes_count = 0
		
		self.reports = []
		self.reports_count = 0
		
		self.is_edited = False

		self._schema_version_ = 2022.01