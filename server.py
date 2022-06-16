"""
_________________________________
HETCH_ACCOUNTS
Server description goes here
_________________________________
"""
import urllib3
import jwt

from flask import Flask, request, Response as FlaskResponse
from flask_cors import CORS, cross_origin
from os import environ
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256
from traceback import format_exc
from utilities import (
	parse_request,
	validate_request,
	authenticate_request,
	generate_authentication_token )
from arango import ArangoClient

urllib3.disable_warnings() # temporarily disable any warnings

from models.response import Response as ResponseModel
from models.time_created import TimeCreatedModel
from models.account import AccountModel
from models.verification_code import VerificationCodeModel

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
""" Database connection """
try:
    # Note that ArangoDB Oasis runs deployments in a cluster configuration.
    # To achieve the best possible availability, your client application has to handle
    # connection failures by retrying operations if needed.
    arango_client = ArangoClient(hosts=environ["ARANGO_URL"], verify_override=False)
    arango_sys_db = arango_client.db(
        name="_system",
        username="root",
        password=environ["ARANGO_PASSWORD"])

    # Create the application database if it does not exist.
    if not arango_sys_db.has_database(environ["DATABASE_NAME"]):
        arango_sys_db.create_database(environ["DATABASE_NAME"])
    else:
        database = arango_client.db(
            environ["DATABASE_NAME"],
            username="root",
            password=environ["ARANGO_PASSWORD"])
    
    # """ Create the required collection """
    if not database.has_collection("accounts"):
        accounts = database.create_collection("accounts")
    else:
        accounts = database.collection("accounts")
	
    db_connection_failed = False
except:
    print("SOMETHING WENT WRONG WITH DB CONNECTION:", format_exc())
    db_connection_failed = True
	
"""
__________________________________
SERVER INSTANCE ROUTES
__________________________________
"""

""" Returns status of the server. """
@server_instance.route("/accounts/status", methods=["GET"])
@cross_origin()
def status() -> FlaskResponse:
	status = not db_connection_failed
	return ResponseModel(cd=200 if status == True else 500,
					msg="Running." if status == True else "Something's not right.").to_json()


""" Creating a new hetch account. """
@server_instance.route("/accounts/", methods=["POST"])
@cross_origin()
@parse_request
def create_new_hetch_account() -> FlaskResponse:
	try:
		json = request.json
		schema = { "email_address": str, "display_name": str, "password": str }
		v_errors = validate_request(d=json, schema=schema)
		if len(v_errors) == 0:
			hetch_account = AccountModel(params=json)
			existing_account = accounts.find({"email_address": hetch_account.email_address})
			if len(existing_account) == 0:
				accounts.insert(hetch_account.to_dict())
				return ResponseModel(cd=200, d=hetch_account.sanitize()).to_json()
			else:
				return ResponseModel(cd=208, msg=f'An account with email address "{hetch_account.email_address}" already exists.').to_json()
		else:
			return ResponseModel(cd=400, d={"errors": v_errors}).to_json()
	except:
		print(format_exc())
		return ResponseModel(cd=500).to_json()


"""Retrieving hetch account from record."""
@server_instance.route("/accounts/<username>/", methods=["GET"])
def get_hetch_account(username: str) -> str:
	hetch_accounts_cursor = accounts.find({"username": username})
	if len(hetch_accounts_cursor) != 0:
		for hetch_account in hetch_accounts_cursor:
			hetch_account = AccountModel(hetch_account)
			return ResponseModel(cd=200, d=hetch_account.sanitize()).to_json()
	return ResponseModel(cd=404, msg="Account not found.").to_json()


""" Requesting an authentication of account user. """
@server_instance.route("/accounts/authentication", methods=["GET"])
def request_authentication() -> FlaskResponse:
	try:
		r_type = request.headers.get("Content-Type")
		if r_type == "application/json":
			json = request.json
			if json.get("username") and json.get("password"):
				hetch_accounts_cursor = accounts.find({ "username": json.get("username") })

				""" Confirm the account. """
				if len(hetch_accounts_cursor) != 0:
					for hetch_account in hetch_accounts_cursor:
						""" Modelize the hetch_account """
						hetch_account_model = AccountModel(hetch_account)
						
						""" Defines if the login should persist forever for subsequent logins. """
						is_persist = False if json.get("is_persist") is None else json.get("is_persist")
						
						""" Use PassLib to compare the login password with the signup password. """
						if pbkdf2_sha256.verify(json.get("password"), hetch_account_model.password):
							""" Verify if the user uses Two Factor Autentication. """
							if hetch_account_model.preferences.get("2fa_authentication"):
								# TODO: PRODUCE AN EXPIRING VERIFICATION CODE
								verification_code = VerificationCodeModel()
								verification_message = f"Your Hetchfund.Capital code is {verification_code.code}. Keep it safe and don't share it, expires in an hour."
								# TODO: SEND AN EMAIL TO THE USER TO VERIFY THEIR LOGIN
								print(verification_message)

								""" Save the verification code in record. """
								hetch_account["verification_codes"].append(verification_code.to_dict())
								accounts.update(hetch_account)

								return ResponseModel(cd=201, msg="Two-Factor Authentication required to continue.").to_json()
							else:							
								""" Return the generated token with account data. """
								return ResponseModel(cd=200, d={ **hetch_account_model.sanitize_soft(), "jwt": generate_authentication_token(hetch_account_model.email_address) }).to_json()
						else:
							return ResponseModel(cd=403, msg="Incorrect password provided.").to_json()
				else:
					return ResponseModel(cd=404, msg="Account not found.").to_json()
			else:
				return ResponseModel(cd=400, msg="Incomplete request. \"username\" and \"password\" field can not be empty.").to_json()
		else:
			return ResponseModel(cd=400, msg="Invalid request. Request has to be made with JSON data as the body.").to_json()
	except:
		print(format_exc())
		return ResponseModel(cd=500, msg="Oops something might have went wrong.").to_json()
		

""" Re-authenticates an authentication session to check it's expiry time """
@server_instance.route("/accounts/authentication/re", methods=["GET"])
def re_authenticate_session() -> FlaskResponse:
	""" Extract and verify authentication token from the request data """
	previous_authorization = request.headers.get("Authorization")
	if previous_authorization and "Bearer " in previous_authorization:
		authorzation_data = previous_authorization.split(" ")[1]
		try:
			authorzation_data_decoded = jwt.decode(authorzation_data, environ["SEED"],
				options={"verify_exp": True},
				algorithms=["HS256"])
			return ResponseModel(cd=200, d={ "p+a": previous_authorization, "p+d": authorzation_data_decoded}).to_json()
		except jwt.exceptions.ExpiredSignatureError:
			return ResponseModel(cd=403, d={ "p+a": previous_authorization }, msg="Signature has expired.").to_json()
		except:
			return ResponseModel(cd=403, d={ "p+a": previous_authorization }, msg="Invalid signature provided.").to_json()
	else:
		return ResponseModel(cd=403, d={ "p+a": previous_authorization }, msg="Invalid or no signature provided.").to_json()


""" Updating account records. """
@server_instance.route("/accounts/<username>", methods=["PATCH"])
def update_account_records(username: str) -> FlaskResponse:
	try:
		def update_account(auth_payload):
			auth_username = auth_payload["email_address"].split("@")[0]
			# check if the authenticated user is the one being updated
			if username == auth_username:
				# check if data contains unchangeble data if does, delete disallowed fields
				fields = request.json
				disallowed_fields = (
					"password", "verification_codes", "payment_tokens",
					"username", "eggs", "eggs_funded", "eggs_archived",
					"eggs_bookmarked", "interests", "comments", "followers",
					"follows", "previous_usernames", "transactions",
					"notifications", "preferences", "_schema_version_", "_id",
					"recent_searches")
					
				for disallowed_field in disallowed_fields:
					if fields.get(disallowed_field) != None:
						del fields[disallowed_field]
				print(fields)
				
				cursor = accounts.find({ "username": username })
				if len(cursor) != 0:
					for account in cursor:
						account = { **account, **fields }
						accounts.update(account)
					return ResponseModel(cd=200, msg="Account updated.",
										d=AccountModel({**account, **fields}).sanitize_soft()).to_json()
				else:
					return ResponseModel(cd=404, msg="Account not found.").to_json()
			else:
				return ResponseModel(cd=403, msg="Not allowed to manipulate resource.").to_json()
		return authenticate_request(server_instance.app_context, re_authenticate_session, update_account)
	except:
		print(format_exc())
		return ResponseModel(cd=500, msg="Something went wrong.").to_json()


""" Deleting account records. """
@server_instance.route("/accounts/<username>", methods=["DELETE"])
def delete_account_records(username: str):
	try:
		cred_validity = re_authenticate_session()
		if cred_validity.status == "200 OK":
			cursor = accounts.find({ "username": username })
			if len(cursor) != 0:
				for account in cursor:
					delete_result = accounts.delete(account["_key"])
					if delete_result:
						return ResponseModel(cd=200, msg="Account deleted.").to_json()
					else:
						return ResponseModel(cd=500, msg="Something went wrong.").to_json()
			else:
				return ResponseModel(cd=404, msg="Account not found.").to_json()
		else:
			return cred_validity
	except:
		print(format_exc())
		return ResponseModel(cd=500, msg="Something went wrong.").to_json()