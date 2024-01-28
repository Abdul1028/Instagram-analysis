import json
import codecs
import os.path
from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError,
    __version__ as client_version
)

# Helper functions for JSON serialization/deserialization
def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')

def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)

def main():
    username = "your_username"
    password = "your_password"

    try:
        # Initialize the Instagram API client
        device_id = None
        settings_file = 'settings.json'

        if not os.path.isfile(settings_file):
            # Settings file does not exist, perform a new login
            api = Client(
                username, password,
                on_login=lambda x: onlogin_callback(x, settings_file))
        else:
            # Reuse cached settings
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            device_id = cached_settings.get('device_id')
            api = Client(username, password, settings=cached_settings)

        # Get the user's own media (posts)
        user_id = api.authenticated_user_id
        media = api.user_feed(user_id)

        # Find the latest post and its ID
        latest_post = media['items'][0]
        latest_post_id = latest_post['id']

        # Fetch comments on the latest post
        comments = api.media_n_comments(latest_post_id)

        # Check each comment for "nice post" and get the username of the commenter
        nice_post_commenters = []
        for comment in comments:
            if "nice post" in comment['text'].lower():
                nice_post_commenters.append(comment['user']['username'])

        if len(nice_post_commenters) > 0:
            print("Users who commented 'nice post' on your latest post:")
            for commenter in nice_post_commenters:
                print(commenter)

            # Comment "nice pic" on the latest posts of these users
            for commenter in nice_post_commenters:
                # Find the user's ID
                user_info = api.username_info(commenter)
                user_id = user_info['user']['pk']

                # Get the user's latest post
                user_media = api.user_feed(user_id)
                latest_user_post = user_media['items'][0]
                latest_user_post_id = latest_user_post['id']

                # Comment "nice pic" on the user's latest post
                api.post_comment(latest_user_post_id, "nice pic")

            print("Commented 'nice pic' on the latest posts of these users.")

        else:
            print("No one commented 'nice post' on your latest post.")

    except ClientLoginError as e:
        print('Login Failed: Invalid username or password. Please try again.')
    except ClientError as e:
        print(f'Client Error: {e}')
    except Exception as e:
        print(f'Unexpected Exception: {e}')

if __name__ == '__main__':
    main()
