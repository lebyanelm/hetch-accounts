from jwt import PyJWT
from flask import request
from functools import wraps
from traceback import format_exc
from os import environ
from datetime import datetime, timedelta

from models.response import Response as ResponseModel

""" Refactor PyJWT methods """
jwt = PyJWT()

""" Decorator for reading the data fron the request sent. """
def parse_request(fn, *args, **kwargs):
	def decorator():
		content_type = request.headers.get("Content-Type")
		if content_type == None:
			return ResponseModel(cd=400, msg="Request body is empty, application/json is required.").to_json()
		elif content_type != "application/json":
			return ResponseModel(cd=400, msg=f"Content-Type {content_type} is not supported. Use application/json.").to_json()
		else:
			try:
				request.get_json()
				return fn(*args, **kwargs)
			except:
				print(format_exc())
				return ResponseModel(cd=400, msg="Error loading JSON data. Invalid JSON provided.").to_json()
	return decorator


""" Parsing information to make sure proper data is being provided in request. """
def validate_request(d: dict, schema: dict) -> list:
	schema_keys = schema.keys()
	errors = []
	for schema_key in schema_keys:
		if d.get(schema_key):
			if type(d.get(schema_key)) != schema[schema_key]:
				errors.append({ "error": f'Invalid data type "{type(d.get(schema_key)).__name__}" used. "{schema[schema_key].__name__}" required instead.', "type": "Invalid."})
		else:
			errors.append({ "error": f"Attribute {schema_key} required in request body.", "type": "Undefined." })
	return errors

def authenticate_request(ctxt, auth_req, cb):
	with ctxt():
		# send a authentication request to the re-authenticate server route within the app
		authentication_validity = auth_req()
		if authentication_validity.status == "200 OK":
			# run the callback function when authentication successful
			return cb(authentication_validity.json["data"]["p+d"])
		else:
			# if failed, return the authentication response
			return authentication_validity


def generate_authentication_token(payload, is_persist=True):
	time_now = datetime.utcnow()
	time_expiry = timedelta(days=7 if not is_persist else 365)
	
	return jwt.encode(
		{
			"email_address": payload,
			"exp": time_now + time_expiry
		},

		environ["SEED"],
		algorithm="HS256"
	)
	