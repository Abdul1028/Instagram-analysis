import json
import codecs
import os.path
import datetime
from geopy.geocoders import Nominatim
import pandas as pd
import streamlit as st
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


class InstagramHelper:
    api = None
    target = ""
    user_id = None
    target_id = None
    is_private = True
    following = False
    geolocator = Nominatim(user_agent="http")

    def __init__(self, u, p, target):
        self.login(u, p)
        self.setTarget(target)

    def login(self, username, password):
        try:
            # Initialize the Instagram API client
            device_id = None
            settings_file = 'settings.json'  # Change this to your desired file name

            if not os.path.isfile(settings_file):
                # Settings file does not exist, perform a new login
                self.api = Client(
                    username, password,
                    on_login=lambda x: self.onlogin_callback(x, settings_file))
            else:
                # Reuse cached settings
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=from_json)
                device_id = cached_settings.get('device_id')
                self.api = Client(username, password, settings=cached_settings)

            return self.api  # Return the API object if login is successful

        except ClientLoginError as e:
            raise Exception('Invalid username or password. Please try again.')
        except Exception as e:
            raise Exception(f'Unexpected Exception: {e}')

    def onlogin_callback(self, api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=to_json)

    def setTarget(self, target):
        self.target = target
        user = self.get_user(target)
        self.target_id = user['id']
        self.is_private = user['is_private']
        self.following = self.check_following()

    def change_target(self, new_target):
        print("Insert new target username: ")
        self.setTarget(new_target)
        return

    def check_following(self):
        if str(self.target_id) == self.api.authenticated_user_id:
            return True
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        return self.api._call_api(endpoint)['user_detail']['user']['friendship_status']['following']

    def __get_feed__(self):
        data = []

        result = self.api.user_feed(str(self.target_id))
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.user_feed(str(self.target_id), max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        return data

    def __get_comments__(self, media_id):
        comments = []

        result = self.api.media_comments(str(media_id))
        comments.extend(result.get('comments', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.media_comments(str(media_id), max_id=next_max_id)
            comments.extend(results.get('comments', []))
            next_max_id = results.get('next_max_id')

        return comments

    def get_user_info(self, target_username):
        try:
            # Fetch the user's info
            user_info = self.api.username_info(target_username)
            return user_info['user']
        except ClientError as e:
            raise Exception(f'Error fetching user information: {e}')

    def get_followers(self, target_username):
        try:
            user_info = self.api.username_info(target_username)
            user_id = user_info['user']['pk']
            followers = self.api.user_followers(user_id)
            return followers.get('users', [])
        except ClientError as e:
            raise Exception(f'Error fetching followers: {e}')

    def get_addrs(self):
        st.write("Searching for target localizations...\n")

        # Replace this with your actual data retrieval logic
        data = self.__get_feed__()

        locations = {}

        for post in data:
            if 'location' in post and post['location'] is not None:
                if 'lat' in post['location'] and 'lng' in post['location']:
                    lat = post['location']['lat']
                    lng = post['location']['lng']
                    locations[str(lat) + ', ' + str(lng)] = post.get('taken_at')

        address = {}
        for k, v in locations.items():
            details = self.geolocator.reverse(k)
            unix_timestamp = datetime.datetime.fromtimestamp(v)
            address[details.address] = unix_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        sort_addresses = sorted(address.items(), key=lambda p: p[1], reverse=True)

        if len(sort_addresses) > 0:
            # Create a Pandas DataFrame from the sorted addresses
            df = pd.DataFrame(sort_addresses, columns=['Address', 'Time'])

            # Display the DataFrame as a table
            st.table(df)

        else:
            st.write("Sorry! No results found :-(\n")

    def getmy_followings(self, id):
        _followings = []

        rank_token = self.api.generate_uuid()
        data = self.api.user_following(id, rank_token=rank_token)

        _followings.extend(data.get('users', []))

        next_max_id = data.get('next_max_id')
        while next_max_id:
            print("\rCatched %i followings" % len(_followings))

            results = self.api.user_following(id, rank_token=rank_token, max_id=next_max_id)
            _followings.extend(results.get('users', []))
            next_max_id = results.get('next_max_id')

        print("\n")

        # Create a DataFrame from the list of followers
        followings_df = pd.DataFrame({
            'User ID': [user['pk'] for user in _followings],
            'Username': [user['username'] for user in _followings],
            'Full Name': [user['full_name'] for user in _followings]
        })

        return followings_df

    def get_info(self, target_username):
        try:
            # Fetch the user's info
            user_info = self.api.username_info(target_username)
            # Display user information

            return user_info
            # st.subheader('User Information')
            # st.write(f"User ID: {user_info['user']['pk']}")
            # st.write(f"Username: {user_info['user']['username']}")
            # st.write(f"Full Name: {user_info['user']['full_name']}")
            # st.write(f"Bio: {user_info['user']['biography']}")
            # st.write(f"Followers: {user_info['user']['follower_count']}")
            # st.write(f"Following: {user_info['user']['following_count']}")
            # st.write(f"Posts: {user_info['user']['media_count']}")

        except ClientError as e:
            print('Error')
            print(f'Client Error: {e}')

    def get_user(self, username):
        try:
            content = self.api.username_info(username)
            if self.writeFile:
                file_name = self.output_dir + "/" + self.target + "_user_id.txt"
                file = open(file_name, "w")
                file.write(str(content['user']['pk']))
                file.close()

            user = dict()
            user['id'] = content['user']['pk']
            user['is_private'] = content['user']['is_private']

            return user
        except ClientError as e:
            print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response),
                  )
            error = json.loads(e.error_response)
            if 'message' in error:
                print(error['message'])
            if 'error_title' in error:
                print(error['error_title'])
            if 'challenge' in error:
                print("Please follow this link to complete the challenge: " + error['challenge']['url'])








