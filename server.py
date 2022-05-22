"""
_________________________________
HETCH_ACCOUNTS
Server description goes here
_________________________________
"""

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from pymongo import MongoClient
from os import environ
from dotenv import load_dotenv
from sys import exc_info
from bcrypt import checkpw
from datetime import timedelta, datetime
from jwt import encode, decode, exceptions
from traceback import format_exc
from utilities import parse_request, validate_request

from models.response import Response
from models.time_created import TimeCreatedModel
from models.account import AccountModel

"""
__________________________________
DEVELOPMENTAL ENVIRONMENT VARIABLES
__________________________________
"""
if environ.get("environment") != "production":
	load_dotenv()


"""
__________________________________
SERVER INSTANCE SETUP
__________________________________
"""
server_instance = Flask(__name__,
			static_folder="./assets/",
            static_url_path="/accounts/assets/") 
CORS(server_instance, resources={r"*": {"origins": "*"}})

"""
__________________________________
DATABASE CONNECTION
__________________________________
"""
db_client = None
db_connection_failed = False
if environ.get("MONGO_CONNECTION"):
	try:
		db_client = MongoClient(environ["MONGO_CONNECTION"],
								serverSelectionTimeoutMS=10000)
		
		""" Run an opperation to test the database """
		db_client.sandbox_hetchfundcapital.connections.insert_one({
			"app_name": "accounts",
			"timestamp": TimeCreatedModel().timestamp,
			"day": TimeCreatedModel().day })
		print("_______DATABASE CONNECETED_______")
	except:
		print(exc_info())
		print("_________DATABASE CONNECETION FAILED___________")
		db_connection_failed = True

"""
__________________________________
SERVER INSTANCE ROUTES
__________________________________
"""

""" Returns status of the server. """
@server_instance.route("/accounts/status", methods=["GET"])
@cross_origin()
def status():
	status = not db_connection_failed
	return Response(cd=200 if status == True else 500,
					msg="Running." if status == True else "Something's not right.").to_json()


""" Creating a new hetch account. """
@server_instance.route("/accounts/", methods=["POST"])
@cross_origin()
@parse_request
def create_new_hetch_account():
	json = request.json
	schema = { "email_address": str, "display_name": str, "password": str }
	v_errors = validate_request(d=json, schema=schema)
	if len(v_errors) == 0:
		a = AccountModel(params=json)
		existing = db_client.hetchfund.accounts.find_one({"email_address": json["email_address"]})
		if existing == None:
			db_client.hetchfund.accounts.insert_one(a.to_dict())
			return Response(cd=200, d=a.sanitize()).to_json()
		else:
			return Response(cd=208, msg=f'Account with email address "{json["email_address"]}" already exists.').to_json()
	else:
		return Response(cd=400, d={"errors": v_errors}).to_json()
	return Response(cd=200).to_json()


"""Retrieving hetch account from record."""
@server_instance.route("/accounts/<username>/", methods=["GET"])
def get_hetch_account(username: str) -> str:
	hetch_account = db_client.hetchfund.accounts.find_one({"username": username})
	if hetch_account:
		a = AccountModel(hetch_account)
		return Response(cd=200, d=a.sanitize()).to_json()
	return Response(cd=404, msg="Account not found.").to_json()

""" Updating the records of an account. """
@server_instance.route("/accounts/authentication", methods=["GET"])
def request_authentication():
	try:
		r_type = request.headers.get("Content-Type")
		if r_type == "application/json":
			json = request.json
			if json.get("username") and json.get("password"):
				hetch_account = db_client.hetchfund.accounts.find_one({ "username": json.get("username") })

				""" Confirm the account. """
				if hetch_account:
					""" Modelize the hetch_account """
					hetch_account = AccountModel(hetch_account)
					
					""" Defines if the login should persist forever for subsequent logins. """
					is_persist = False if json.get("is_persist") is None else json.get("is_persist")
					
					""" Use bcrypt to compare the login password with the signup password. """
					p_raw = bytes(json.get("password"), "utf-8")
					p_hashed = bytes(hetch_account.password, "utf-8")
					if checkpw(p_raw, p_hashed):
						time_now = datetime.utcnow()
						time_expiry = timedelta(days=7 if not is_persist else 365)
						generated_token = encode(
							{ "email_address": hetch_account.email_address, "exp": time_now + time_expiry },
							environ["SEED"],
							algorithm="HS256"
						)
						
						""" Return the generated token with account data. """
						return Response(cd=200, d={ **hetch_account.sanitize_soft(), "jwt_token": generated_token }).to_json()
					else:
						return Response(cd=403, msg="Incorrect password provided.").to_json()
				else:
					return Response(cd=404, msg="Account not found.").to_json()
			else:
				return Response(cd=400, msg="Incomplete request. \"username\" and \"password\" field can not be empty.").to_json()
		else:
			return Response(cd=400, msg="Invalid request. Request has to be made with JSON data as the body.").to_json()
	except:
		return Response(cd=500, msg="Oops something might have went wrong.").to_json()


""" Re-authenticates an authentication session to check it's expiry time """
@server_instance.route("/accounts/re-authenticate", methods=["GET"])
def re_authenticate_session():
	""" Extract and verify authentication token from the request data """
	previous_authorization = request.headers.get("Authorization")
	if previous_authorization and "Bearer " in previous_authorization:
		authorzation_data = previous_authorization.split(" ")[1]

		try:
			authorzation_data_decoded = decode(authorzation_data, environ["SEED"],
				options={"verify_exp": True},
				algorithms=["HS256"])
			return Response(cd=200, d={"p_a": previous_authorization}).to_json()
		except exceptions.ExpiredSignatureError:
			return Response(cd=403, d={"p_a": previous_authorization }, msg="Signature has expired.").to_json()
		except:
			return Response(cd=403, d={"p_a": previous_authorization }, msg="Invalid signature provided.").to_json()
		
		return authorzation_data
	else:
		return Response(cd=403, d={"p_a": previous_authorization }, msg="Invalid or no signature provided.").to_json()