from bcrypt import hashpw, gensalt
from libgravatar import Gravatar
from os import environ
from requests import get

class AccountModel:
	def __init__(self, params):
		super().__init__()
		self.display_name = params.get("display_name")
		self.email_address = params.get("email_address")

		# Save the password as a hashed version
		if params.get("_id") is None:
			self.username = self.email_address.split("@")[0]
			password = bytes(params.get("password"), "utf-8")
			self.password = hashpw(password, salt=gensalt()).decode()

			# Profile avatar
			self.set_profile_avatar()
		else:
			self._id = params.get("_id")
			self.password = params.get("password")
			self.username = params.get("username")

		# Information that deals with funding and eggs related
		self.eggs = [] if params.get("eggs") is None else params.get("eggs")
		self.eggs_funded = [] if params.get("eggs_funded") is None else params.get("eggs_funded")
		self.eggs_archived = [] if params.get("eggs_archived") is None else params.get("eggs_archived")
		self.eggs_bookmarked = [] if params.get("eggs_bookmarked") is None else params.get("eggs_bookmarked")

		# Information related to biography
		self.home_city = "" if params.get("home_city") is None else params.get("home_city")
		self.nationality = "" if params.get("nationality") is None else params.get("nationality")
		self.gender = 0 if params.get("gender") is None else params.get("gender")
		self.age = 0 if params.get("age") is None else params.get("age")
		self.occupation = "" if params.get("occupation") is None else params.get("occupation")
		self.interests = ["inspiring"] if params.get("interests") is None else params.get("interests")
		self.external_links = [] if params.get("external_links") is None else params.get("external_links")

		# Profile information
		self.comments = [] if params.get("comments") is None else params.get("comments")
		self.recent_searches = [] if params.get("recent_searches") is None else params.get("recent_searches")
		self.followers = [] if params.get("followers") is None else params.get("followers")
		self.follows = [] if params.get("follows") is None else params.get("follows")
		self.previous_usernames = [self.username] if params.get("previous_usernames") is None else params.get("previous_usernames")

		# Sensative information that should be hidden from public
		self.payment_tokens = []  if params.get("payment_tokens") is None else params.get("payment_tokens")
		self.transactions = [] if params.get("transactions") is None else params.get("transactions")
		
		self.verification_codes = [] if params.get("verification_codes") is None else params.get("verification_codes")
		self.notifications = [] if params.get("notifications") is None else params.get("notifications")
		self.preferences = {
			"2fa_authentication": False,
			"is_expire_login": True
		} if params.get("preferences") is None else params.get("preferences")

		self._schema_version_ = 2022.01 if params.get("_schema_version_") is None else params.get("_schema_version_")

	def set_profile_avatar(self):
		# Determine a profile picture to use
		# Check if user registered for Gravatar
		gravatar = Gravatar(self.email_address)
		gravatar_profile = gravatar.get_profile()
		gravatar_profile_status_code = get(gravatar_profile).status_code
		if gravatar_profile_status_code == 404:
			# Generate a random abstract profile picture
			self.profile_image = f"https://avatars.dicebear.com/api/pixel-art-neutral/{self.username}.svg"
		else:
			# Use Gravatar image
			self.profile_image = gravatar.get_image()
			
	def sanitize(self) -> dict:
		""" Sensative information """
		copy = {**self.to_dict()}
		copy["_id"] = str(copy["_id"])

		del copy["password"]
		del copy["verification_codes"]
		del copy["notifications"]
		del copy["preferences"]
		del copy["payment_tokens"]
		del copy["transactions"]
		del copy["previous_usernames"]
		del copy["recent_searches"]
		del copy["interests"]
		del copy["eggs_archived"]
		
		return copy

	def sanitize_soft(self) -> dict:
		""" Sensative information """
		copy = {**self.to_dict()}
		copy["_id"] = str(copy["_id"])

		del copy["password"]
		del copy["verification_codes"]
		del copy["payment_tokens"]

		return copy

	def to_dict(self) -> dict:
		return self.__dict__