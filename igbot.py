import pandas as pd
import streamlit as st
import json
import codecs
import os.path
import argparse
import logging
import datetime
from prettytable import PrettyTable
import pandas as df

from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError,
    __version__ as client_version
)

# Add your existing functions here, such as `onlogin_callback`, `get_followers`, etc.

# Helper functions for JSON serialization/deserialization
def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes', '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        st.write('SAVED: {0!s}'.format(new_settings_file))

def login(username,password):
    try:
        # Initialize the Instagram API client
        device_id = None
        settings_file = "settings.json"
        if not os.path.isfile(settings_file):
            api = Client(
                username, password,
                on_login=lambda x: onlogin_callback(x, settings_file)
            )
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            device_id = cached_settings.get('device_id')
            api = Client(
                username, password,
                settings=cached_settings
            )

        # Show when login expires
        cookie_expiry = api.cookie_jar.auth_expires
        st.write('Cookie Expiry: {0!s}'.format(
            datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ'))
        )

        return api

        # Call the API, you can replace '2958144170' with the user ID you want to fetch data for
        results = api.user_feed('2958144170')
        assert len(results.get('items', [])) > 0
        st.success('Login successful!')

    except Exception as e:
        st.error(e)



# Add a title and description
st.title("Instagram Bot")
st.write("A bot to fetch Instagram followers and more!")

# Add a sidebar for user input
st.sidebar.header("User Input")
settings_file_path = st.sidebar.text_input("Settings File Path", "settings.json")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
target_user_id = st.sidebar.text_input("Target User ID")

if st.sidebar.button("Login"):
    st.write("Logging in...")
    api = login(username,password)


def __get_feed__(id):
    data = []

    result = api.user_feed(id)
    data.extend(result.get('items', []))

    next_max_id = result.get('next_max_id')
    while next_max_id:
        results = api.user_feed(id, max_id=next_max_id)
        data.extend(results.get('items', []))
        next_max_id = results.get('next_max_id')

    return data

    import pandas as pd

def getmy_followings(id):
    _followings = []

    rank_token = api.generate_uuid()
    data = api.user_following(id, rank_token=rank_token)

    _followings.extend(data.get('users', []))

    next_max_id = data.get('next_max_id')
    while next_max_id:
        print("\rCatched %i followings" % len(_followings))

        results = api.user_following(id, rank_token=rank_token, max_id=next_max_id)
        _followings.extend(results.get('users', []))
        next_max_id = results.get('next_max_id')

    print("\n")

    # Create a DataFrame from the list of followers
    followings_df = pd.DataFrame({
        'User ID': [user['pk'] for user in _followings],
        'Username': [user['username'] for user in _followings],
        'Full Name': [user['full_name'] for user in _followings]
    })

    # Display the DataFrame using Streamlit
    st.table(followings_df)


    def get_followings(id):
        _followings = []
        followings = []

        rank_token = api.generate_uuid()
        data = api.user_following(id, rank_token=rank_token)

        _followings.extend(data.get('users', []))

        next_max_id = data.get('next_max_id')
        while next_max_id:
            print("\rCatched %i followings" % len(_followings))

            results = api.user_following(id, rank_token=rank_token, max_id=next_max_id)
            _followings.extend(results.get('users', []))
            next_max_id = results.get('next_max_id')

        print("\n")

        for user in _followings:
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followings.append(u)

        for follwing in followings:
            print(follwing)

    def get_followers(id):

        _followers = []
        followers = []

        rank_token = api.generate_uuid()
        data = api.user_followers(id, rank_token=rank_token)

        _followers.extend(data.get('users', []))

        next_max_id = data.get('next_max_id')
        while next_max_id:
            print("\rCatched %i followers" % len(_followers))

            results = api.user_followers(id, rank_token=rank_token, max_id=next_max_id)
            _followers.extend(results.get('users', []))
            next_max_id = results.get('next_max_id')

        print("\n")

        for user in _followers:
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followers.append(u)

        for follower in followers:
            print(follower)


    def get_followings_email(id):

        print("Searching for emails of users followed by target... this can take a few minutes\n")

        followings = []

        rank_token = api.generate_uuid()
        data = api.user_following(id, rank_token=rank_token)

        for user in data.get('users', []):
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followings.append(u)

        next_max_id = data.get('next_max_id')

        while next_max_id:
            results = api.user_following(id, rank_token=rank_token, max_id=next_max_id)

            for user in results.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followings.append(u)

            next_max_id = results.get('next_max_id')

        results = []

        print("Do you want to get all emails? y/n: ")
        value = input()

        if value == str("y") or value == str("yes") or value == str("Yes") or value == str("YES"):
            value = len(followings)
        elif value == str(""):
            print("\n")
            exit()
        elif value == str("n") or value == str("no") or value == str("No") or value == str("NO"):
            while True:
                try:
                    print("How many emails do you want to get? ", )
                    new_value = int(input())
                    value = new_value - 1
                    break
                except ValueError:
                    print("Error! Please enter a valid integer!")
                    print("\n")
                    exit()
        else:
            print("Error! Please enter y/n :-)")
            print("\n")
            exit()

        for follow in followings:
            print("\rCatched %i followings email" % len(results))
            user = api.user_info(str(follow['id']))
            if 'public_email' in user['user'] and user['user']['public_email']:
                follow['email'] = user['user']['public_email']
                if len(results) > value:
                    break
                results.append(follow)

            for a in results:
                print(a)

    def get_followings_number(id):

        print("Searching for phone numbers of users followers... this can take a few minutes\n")

        followings = []

        rank_token = api.generate_uuid()
        data = api.user_following(id, rank_token=rank_token)

        for user in data.get('users', []):
            u = {
                'id': user['pk'],
                'username': user['username'],
                'full_name': user['full_name']
            }
            followings.append(u)

        next_max_id = data.get('next_max_id')

        while next_max_id:
            results = api.user_following(id, rank_token=rank_token, max_id=next_max_id)

            for user in results.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followings.append(u)

            next_max_id = results.get('next_max_id')

        results = []

        print("Do you want to get all phone numbers? y/n: ")
        value = input()

        if value == str("y") or value == str("yes") or value == str("Yes") or value == str("YES"):
            value = len(followings)
        elif value == str(""):
            print("\n")
            exit()
        elif value == str("n") or value == str("no") or value == str("No") or value == str("NO"):
            while True:
                try:
                    print("How many phone numbers do you want to get? ")
                    new_value = int(input())
                    value = new_value - 1
                    break
                except ValueError:
                    print("Error! Please enter a valid integer!")
                    print("\n")
                    exit()
        else:
            print("Error! Please enter y/n :-)")
            print("\n")
            exit()

        for follow in followings:
            print("\rCatched %i followers phone numbers" % len(results))

            user = api.user_info(str(follow['id']))
            if 'contact_phone_number' in user['user'] and user['user']['contact_phone_number']:
                follow['contact_phone_number'] = user['user']['contact_phone_number']
                if len(results) > value:
                    break
                results.append(follow)

        for a in results:
            print(results)

    def get_tagged_users(id):
        print("Searching for users who tagged target...\n")

        posts = []

        result = api.usertag_feed(id)
        posts.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = api.user_feed(id, max_id=next_max_id)
            posts.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        if len(posts) > 0:
            print("\nWoohoo! We found " + str(len(posts)) + " photos\n")

            users = []

            for post in posts:
                if not any(u['id'] == post['user']['pk'] for u in users):
                    user = {
                        'id': post['user']['pk'],
                        'username': post['user']['username'],
                        'full_name': post['user']['full_name'],
                        'counter': 1
                    }
                    users.append(user)
                else:
                    for user in users:
                        if user['id'] == post['user']['pk']:
                            user['counter'] += 1
                            break

            ssort = sorted(users, key=lambda value: value['counter'], reverse=True)

            t = PrettyTable()

            t.field_names = ['Photos', 'ID', 'Username', 'Full Name']
            t.align["Photos"] = "l"
            t.align["ID"] = "l"
            t.align["Username"] = "l"
            t.align["Full Name"] = "l"

            for u in ssort:
                t.add_row([str(u['counter']), u['id'], u['username'], u['full_name']])

            print(t)

    def get_captions(id):
        print("Searching for target captions...\n")


        captions = []

        data = __get_feed__(id)
        counter = 0

        try:
            for item in data:
                if "caption" in item:
                    if item["caption"] is not None:
                        text = item["caption"]["text"]
                        captions.append(text)
                        counter = counter + 1
                        print("\rFound %i" % counter)

            for c in captions:
                print(c)

        except AttributeError:
            pass

        except KeyError:
            pass

def main():
    # Add buttons for other functionalities
    if st.button("Fetch Followers"):
        try:
            pass
        except Exception as e:
            st.error(f"Error fetching followers: {e}")

    if st.button("Fetch Followings"):
        try:
            getmy_followings(target_user_id)
            # Add your fetch followings code here

        except Exception as e:
            st.error(f"Error fetching followings: {e}")

    if st.button("Fetch Captions"):
        try:
            # Add your fetch captions code here
            pass
        except Exception as e:
            st.error(f"Error fetching captions: {e}")

    if st.button("Fetch Tagged Users"):
        try:
            # Add your fetch tagged users code here
            pass
        except Exception as e:
            st.error(f"Error fetching tagged users: {e}")

if __name__ == "__main__":
    main()
