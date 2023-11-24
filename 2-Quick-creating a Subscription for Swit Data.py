import json

from flask import Flask, redirect, request
import requests
import urllib.parse

app = Flask(__name__)

# SETTINGS
YOUR_LOCALHOST_PORT = '8282'
YOUR_CLIENT_ID = 'pq5ES2KwR3uJBTSbUblOk6Crb5P8pw9J'
YOUR_CLIENT_SECRET = 'KvHP4dnV5HhctyQvByOaJNnd'
YOUR_APPS_SCOPE = 'task:write subscriptions:write subscriptions:read channels.messages:read'

# This REDIRECT_URI should be registered to your app's management page
YOUR_REDIRECT_URI = 'https://devrel.ngrok.io/oauth'

# This is the project ID of the project you want to create tasks in.
YOUR_PROJECT_ID = '230516082780M3cyZtU'

@app.route('/')
def root():
	return "This is the root of Your app."


@app.route('/oauth')
def oauth():
	code = request.args.get('code')

	if code is None:
		# redirect to GET request for authorization confirmation
		get_url = "https://openapi.swit.io/oauth/authorize"
		get_params_for_query_string = urllib.parse.urlencode({"client_id": YOUR_CLIENT_ID,
		                                                      "redirect_uri": YOUR_REDIRECT_URI,
		                                                      "scope": YOUR_APPS_SCOPE,
		                                                      "response_type": "code"})
		return redirect(get_url + "?" + get_params_for_query_string)

	else:
		# POST request to issue the token.
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


@app.route('/subscription/create/<workspace_id>/<channel_id>')
def subscription_create(workspace_id, channel_id):
	swit_access_token = ""
	with open('sample_token.json', 'r', encoding='utf-8') as file:
		json_data = json.load(file)
		swit_access_token = json_data['access_token']

	subscription_url = "https://openapi.swit.io/v2/subscriptions"
	subscription_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + swit_access_token}
	subscription_body = {
		"event_source": "/workspaces/" + workspace_id + "/channels/" + channel_id,
		"resource_type": "channels.messages"}
	response = requests.post(subscription_url, headers=subscription_headers, json=subscription_body)

	return response.json()


@app.route('/subscription/delete/<subscription_id>')
def subscription_delete(subscription_id):
	swit_access_token = ""
	with open('sample_token.json', 'r', encoding='utf-8') as file:
		json_data = json.load(file)
		swit_access_token = json_data['access_token']

	subscription_url = "https://openapi.swit.io/v2/subscriptions/" + subscription_id
	subscription_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + swit_access_token}
	response = requests.delete(subscription_url, headers=subscription_headers)

	return response.text


@app.route('/subscription/read/<subscription_id>')
def subscription_read(subscription_id):
	swit_access_token = ""
	with open('sample_token.json', 'r', encoding='utf-8') as file:
		json_data = json.load(file)
		swit_access_token = json_data['access_token']

	subscription_url = "https://openapi.swit.io/v2/subscriptions"
	subscription_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + swit_access_token}

	if subscription_id != "all":
		subscription_url = "https://openapi.swit.io/v2/subscriptions/" + subscription_id

	response = requests.get(subscription_url, headers=subscription_headers)
	return response.json()


@app.route('/subscription/read')
def subscription_read_all():
	swit_access_token = ""
	with open('sample_token.json', 'r', encoding='utf-8') as file:
		json_data = json.load(file)
		swit_access_token = json_data['access_token']

	subscription_url = "https://openapi.swit.io/v2/subscriptions"
	subscription_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + swit_access_token}
	response = requests.get(subscription_url, headers=subscription_headers)
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

	if response.status_code == 200:
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
