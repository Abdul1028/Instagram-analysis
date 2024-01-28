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





