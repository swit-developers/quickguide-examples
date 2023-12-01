import json

from flask import Flask, redirect, request
import requests
import urllib.parse

app = Flask(__name__)

# SETTINGS
YOUR_LOCALHOST_PORT = 'YOUR_PORT'
YOUR_CLIENT_ID = 'YOUR_CLIENT_ID'
YOUR_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
YOUR_USERS_SCOPE = 'channel:read message:write'
YOUR_APPS_SCOPE = 'app:install ' + YOUR_USERS_SCOPE

# This REDIRECT_URI should be registered to your app's management page
YOUR_REDIRECT_URI = 'YOUR_TUNNEL_URL/oauth'

@app.route('/')
def root():
	return "This is the root of Your app."


@app.route('/oauth')
def oauth():
	code = request.args.get('code')
	state = request.args.get('state')
	type = request.args.get('type')

	if code is None:
		# first step for Oauth: getting the code
		get_url = "https://openapi.swit.io/oauth/authorize"
		json_for_redirect = {
			"client_id": YOUR_CLIENT_ID,
			"redirect_uri": YOUR_REDIRECT_URI,
			"scope": YOUR_APPS_SCOPE if type == 'app' else YOUR_USERS_SCOPE,
			"response_type": "code",
			"state": type}
		get_params_for_query_string = urllib.parse.urlencode(json_for_redirect)

		return redirect(get_url + "?" + get_params_for_query_string)

	else:
		# second step for Oauth: getting the token
		post_url = "https://openapi.swit.io/oauth/token"
		post_headers = {
			"content-Type": "application/x-www-form-urlencoded"}
		post_body = {
			"client_id": YOUR_CLIENT_ID,
			"client_secret": YOUR_CLIENT_SECRET,
			"redirect_uri": YOUR_REDIRECT_URI,
			"code": code,
			"grant_type": "authorization_code"}

		response = requests.post(post_url, headers=post_headers, data=post_body)
		json_data = response.json()
		json_data['user_id'] = state

		# save token to json file
		json_file_name = 'sample_token_app.json' if state == 'app' else 'sample_token_user.json'
		with open(json_file_name, 'w', encoding='utf-8') as file:
			json.dump(json_data, file, indent=4, ensure_ascii=False)

		return response.json()


def token_refresh(refresh_token, json_file_name="sample_token_app.json"):
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
		with open(json_file_name, 'w', encoding='utf-8') as file:
			json_data = response.json()
			json.dump(json_data, file, indent=4, ensure_ascii=False)
		return response.json()["access_token"]
	else:
		raise Exception("Error in refreshing token", response.text)


def channel_info(token, channel_id):
	channel_info_url = "https://openapi.swit.io/v1/api/channel.info"
	channel_info_headers = {
		"authorization": "Bearer " + token}
	channel_info_params = {
		"id": channel_id}
	response = requests.get(channel_info_url, headers=channel_info_headers, params=channel_info_params)

	if response.status_code == 401:
		swit_refresh_token = ""
		with open('sample_token_app.json', 'r', encoding='utf-8') as file:
			json_data = json.load(file)
			swit_refresh_token = json_data['refresh_token']

		new_token = token_refresh(swit_refresh_token)
		return channel_info(new_token, channel_id)

	return response


def message_create(send_by, token, channel_id, content):
	message_create_url = "https://openapi.swit.io/v1/api/message.create"
	message_create_headers = {
		"content-type": "application/json",
		"authorization": "Bearer " + token}
	message_create_body = {
		"channel_id": channel_id,
		"content": content}
	response = requests.post(message_create_url, headers=message_create_headers, json=message_create_body)

	if response.status_code == 401:
		json_file_name = "sample_token_app.json" if send_by == "app" else "sample_token_user.json"
		swit_refresh_token = ""
		with open(json_file_name, 'r', encoding='utf-8') as file:
			json_data = json.load(file)
			swit_refresh_token = json_data['refresh_token']

		new_token = token_refresh(swit_refresh_token, json_file_name)
		return message_create(send_by, new_token, channel_id, content)

	return response


@app.route('/guide_app', methods=['POST'])
def guide_app():
	# print request body from swit server
	event_data = request.json
	print(json.dumps(event_data, indent=4, ensure_ascii=False))

	# get data from request body
	user_action_type = event_data['user_action']['type']
	user_action_id = event_data['user_action']['id']
	user_id = event_data['user_info']['user_id']
	channel_id = event_data['context']['channel_id']

	# get app access token from json file
	swit_access_token_app = ""
	with open('sample_token_app.json', 'r', encoding='utf-8') as file:
		json_data = json.load(file)
		swit_access_token_app = json_data['access_token']

	# get user access token and id from json file
	swit_access_token_user = ""
	swit_user_id = ""
	try:
		with open('sample_token_user.json', 'r', encoding='utf-8') as file:
			json_data = json.load(file)
			swit_access_token_user = json_data['access_token']
			swit_user_id = json_data['user_id']
	except:
		pass

	# first user action in swit
	if "current_view" not in event_data:

		# check if bot is in the channel
		response_invite_check = channel_info(swit_access_token_app, channel_id)
		if response_invite_check.json()['data']['channel']['id'] == '':
			modal_bot_invite = {
				"callback_type": "bot.invite_prompt",
				"destination": {
					"type": "channel",
					"id": channel_id}}
			return modal_bot_invite

		# check if user has signed in
		if user_id != swit_user_id:
			modal_user_oauth = {
				"callback_type": "views.open",
				"new_view": {
					"view_id": "modal_sign_in",
					"header": {
						"title": "Sign in",
						"subtitle": "This is a Guide app."},
					"body": {
						"elements": [
							{
								"type": "sign_in_page",
								"title": "Try It!",
								"description": "Sign in to Guide App.",
								"button": {
									"type": "button",
									"label": "Sign in",
									"action_id": "button_sign_in",
									"static_action": {
										"action_type": "open_oauth_popup",
										"link_url": YOUR_REDIRECT_URI + "?type=" + user_id}},
								"integrated_service": {
									"icon": {
										"type": "image",
										"image_url": "https://developers.swit.io/assets/images/developers/main/main_visual.png"},
									"title": "Guide app",
									"description": "This is a Guide app."}}]}}}
			return modal_user_oauth

		# first modal popup after check above: bot is in the channel and user has signed in
		if "command_id_guide_app" in user_action_id:
			modal_first_popup = {
				"callback_type": "views.open",
				"new_view": {
					"state": channel_id,
					"view_id": "modal_first_popup",
					"header": {
						"title": "This is the title of the first modal",
						"subtitle": "This is the subtitle of the first modal"},
					"body": {
						"elements": [
							{
								"type": "text",
								"markdown": True,
								"content": "**Type a message to send**\nThe guide app will create a message in this channel."},
							{
								"type": "text_input",
								"action_id": "message_content_typed_by_user"},
							{
								"type": "select",
								"options": [
									{
										"label": "Send by App",
										"action_id": "app"},
									{
										"label": "Send by User",
										"action_id": "user"}],
								"value": [
									"app"]}]},
					"footer": {
						"buttons": [
							{
								"type": "button",
								"label": "Abort",
								"style": "primary",
								"static_action": {
									"action_type": "close_view"}},
							{
								"type": "button",
								"label": "Send a message",
								"style": "primary_filled",
								"action_id": "button_send_a_message"}]}}}
			return modal_first_popup

	# second user action in swit
	else:
		# user oauth complete
		if user_action_type == "view_actions.oauth_complete":
			return {
				"callback_type": "views.close"}

		# second modal popup after creating a message
		elif user_action_type == "view_actions.submit":
			if user_action_id == "button_send_a_message":
				current_view = event_data["current_view"]

				send_by = current_view["body"]["elements"][2]["value"][0]
				swit_access_token = swit_access_token_user if send_by == "user" else swit_access_token_app

				channel_id = current_view["state"]
				message_content = current_view["body"]["elements"][1]["value"]

				message_create(send_by, swit_access_token, channel_id, message_content)
				modal_second_popup = {
					"callback_type": "views.open",
					"new_view": {
						"state": channel_id,
						"view_id": "modal_second_popup",
						"header": {
							"title": "This is the title of the second modal"},
						"body": {
							"elements": [
								{
									"type": "text",
									"markdown": True,
									"content": "**" + message_content + "**"},
								{
									"type": "text",
									"content": "Message has successfully sent by " + send_by + "."}]},
						"footer": {
							"buttons": [
								{
									"type": "button",
									"label": "Got it",
									"style": "primary_filled",
									"static_action": {
										"action_type": "close_view"}}]}
					}
				}
				return modal_second_popup


if __name__ == '__main__':
	app.run(debug=True, host='localhost', port=YOUR_LOCALHOST_PORT)
