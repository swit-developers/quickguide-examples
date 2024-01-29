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
	return "This is the root of Your app."


@app.route('/oauth')
def oauth():
	'''redirect to GET request for authorization confirmation'''
	swit_oauth_get_url = "https://openapi.swit.io/oauth/authorize"

	params_for_query_string = {
		"client_id": YOUR_CLIENT_ID,
		"redirect_uri": YOUR_REDIRECT_URI,
		"scope": YOUR_APPS_SCOPE,
		"response_type": "code"
	}
	swit_oauth_get_query_string = urllib.parse.urlencode(params_for_query_string)

	return redirect(swit_oauth_get_url + "?" + swit_oauth_get_query_string)


@app.route('/oauth/callback')
def oauth_callback():
	'''POST request to issue the token.'''
	code = request.args.get('code')

	swit_oauth_post_url = "https://openapi.swit.io/oauth/token"
	swit_oauth_post_headers = {
		"content-Type": "application/x-www-form-urlencoded"
	}

	swit_oauth_post_body = {
		"client_id": YOUR_CLIENT_ID,
		"client_secret": YOUR_CLIENT_SECRET,
		"redirect_uri": YOUR_REDIRECT_URI,
		"code": code,
		"grant_type": "authorization_code",
	}

	response = requests.post(swit_oauth_post_url,
	                         headers=swit_oauth_post_headers,
	                         data=swit_oauth_post_body)

	return response.json()


if __name__ == '__main__':
	app.run(debug=True, host='localhost', port=YOUR_LOCALHOST_PORT)
