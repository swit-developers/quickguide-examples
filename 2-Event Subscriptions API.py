from flask import Flask, redirect, request
import requests
import urllib.parse
import json

app = Flask(__name__)

# SETTINGS
YOUR_LOCALHOST_PORT = 'YOUR_PORT'
YOUR_CLIENT_ID = 'YOUR_CLIENT_ID'
YOUR_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
YOUR_APPS_SCOPE = 'task:write'

# This REDIRECT_URI should be registered to your app's management page
YOUR_REDIRECT_URI = 'YOUR_APP_SERVER_URL' + '/oauth'

# This is the project ID of the project you want to create tasks in.
YOUR_PROJECT_ID = 'THE_SWIT_PROJECT_ID_YOU_WANT'


@app.route('/')
def root():
	return "This is the root of your app."


@app.route('/oauth')
def oauth():
	'''
	1. redirect to GET request for authorization confirmation
	2. POST request to issue the token.
	'''
	code = request.args.get('code')

	if code is None:
		get_url = "https://openapi.swit.io/oauth/authorize"

		get_params_for_query_string = urllib.parse.urlencode({
			"client_id": YOUR_CLIENT_ID,
			"redirect_uri": YOUR_REDIRECT_URI,
			"scope": YOUR_APPS_SCOPE,
			"response_type": "code"})

		return redirect(get_url + "?" + get_params_for_query_string)

	else:
		post_url = "https://openapi.swit.io/oauth/token"
		post_headers = {
			"content-Type": "application/x-www-form-urlencoded"}
		post_body = {
			"client_id": YOUR_CLIENT_ID,
			"client_secret": YOUR_CLIENT_SECRET,
			"redirect_uri": YOUR_REDIRECT_URI,
			"code": code,
			"grant_type": "authorization_code", }
		response = requests.post(post_url, headers=post_headers, data=post_body)

		# Save the token to a file
		with open('sample_token.json', 'w', encoding='utf-8') as file:
			json_data = response.json()
			json.dump(json_data, file, indent=4, ensure_ascii=False)

		return response.json()


def token_refresh(refresh_token):
	token_url = "https://openapi.swit.io/oauth/token"
	token_headers = {
		"content-Type": "application/x-www-form-urlencoded"}
	token_data = {
		"grant_type": "refresh_token",
		"client_id": YOUR_CLIENT_ID,
		"client_secret": YOUR_CLIENT_SECRET,
		"refresh_token": refresh_token}
	response = requests.post(token_url, headers=token_headers, data=token_data)

	if response.ok:
		with open('sample_token.json', 'w', encoding='utf-8') as file:
			json_data = response.json()
			json.dump(json_data, file, indent=4, ensure_ascii=False)
		return response.json()["access_token"]
	else:
		raise Exception("Error in refreshing token", response.text)


def task_create(token, project_id, task_title):
	task_create_url = "https://openapi.swit.io/v1/api/task.create"
	task_create_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + token}
	task_create_body = {
		"project_id": project_id,
		"title": task_title}
	response = requests.post(task_create_url, headers=task_create_headers, json=task_create_body)

	if response.status_code == 401:
		swit_refresh_token = ""
		with open('sample_token.json', 'r', encoding='utf-8') as file:
			json_data = json.load(file)
			swit_refresh_token = json_data['refresh_token']

		new_token = token_refresh(swit_refresh_token)
		return task_create(new_token, project_id, task_title)

	return response


@app.route('/event', methods=['POST'])
def event():
	event_data = request.json
	print(json.dumps(event_data, indent=4, ensure_ascii=False))

	content = event_data['details']['message']['content']
	if content[:6] == "[task]":
		swit_access_token = ""
		with open('sample_token.json', 'r', encoding='utf-8') as file:
			json_data = json.load(file)
			swit_access_token = json_data['access_token']

		response = task_create(swit_access_token, YOUR_PROJECT_ID, content[6:])
		print(json.dumps(response.json(), indent=4, ensure_ascii=False))

	return ""


if __name__ == '__main__':
	app.run(debug=True, host='localhost', port=YOUR_LOCALHOST_PORT)
