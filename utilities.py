from flask import request, g
from functools import wraps
from traceback import format_exc

from models.response import Response

""" Decorator for reading the data fron the request sent. """
def parse_request(fn, *args, **kwargs):
	def decorator():
		content_type = request.headers.get("Content-Type")
		if content_type == None:
			return Response(cd=400, msg="Request body is empty, application/json is required.").to_json()
		elif content_type != "application/json":
			return Response(cd=400, msg=f"Content-Type {content_type} is not supported. Use application/json.").to_json()
		else:
			try:
				request.get_json()
				return fn(*args, **kwargs)
			except:
				print(format_exc())
				return Response(cd=400, msg="Error loading JSON data. Invalid JSON provided.").to_json()
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