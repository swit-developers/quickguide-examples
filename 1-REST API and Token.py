from flask import Flask, redirect, request
import requests
import urllib.parse

app = Flask(__name__)

## SETTINGS
# If you change this, you should change the Allowed redirect URLs
YOUR_LOCALHOST_PORT = '8282'

# These are copied from your app's management page
YOUR_CLIENT_ID = 'YOUR_CLIENT_ID'
YOUR_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
YOUR_APPS_SCOPE = 'task:write'

# This REDIRECT_URI should be registered to your app's management page
YOUR_REDIRECT_URI = 'http://localhost:' + YOUR_LOCALHOST_PORT + '/oauth/callback'


@app.route('/')
def root():
	return "This is the root of your app."


@app.route('/oauth')
def oauth():
	'''redirect to GET request for authorization confirmation'''
	get_url = "https://openapi.swit.io/oauth/authorize"

	get_params_for_query_string = urllib.parse.urlencode({
		"client_id": YOUR_CLIENT_ID,
		"redirect_uri": YOUR_REDIRECT_URI,
		"scope": YOUR_APPS_SCOPE,
		"response_type": "code"})

	return redirect(get_url + "?" + get_params_for_query_string)


@app.route('/oauth/callback')
def oauth_callback():
	'''POST request to issue the token.'''
	code = request.args.get('code')

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

	return response.json()


if __name__ == '__main__':
	app.run(debug=True, host='localhost', port=YOUR_LOCALHOST_PORT)
