import json
import codecs
import os.path
import argparse
import logging
import datetime
from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError,
    __version__ as client_version
)
from prettytable import PrettyTable
from geopy.geocoders import Nominatim


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
        print('SAVED: {0!s}'.format(new_settings_file))

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch Instagram followers')
    parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-o', '--output', dest='output_file', type=str, required=False, default=None, help='Output file for followers')
    parser.add_argument('-debug', '--debug', action='store_true')
    args = parser.parse_args()

    # Set the logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Initialize the Instagram API client
    device_id = None
    try:
        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # Settings file does not exist, perform a new login
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            # Reuse cached settings
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            device_id = cached_settings.get('device_id')
            api = Client(
                args.username, args.password,
                settings=cached_settings)
    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))
    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)


    def __get_feed__():
        data = []

        result = api.user_feed("5440632738")
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = api.user_feed("5440632738", max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        return data


    try:

        print("Searching for target localizations...\n")

        data = __get_feed__()

        geolocator = Nominatim(user_agent="http")

        locations = {}

        for post in data:
            if 'location' in post and post['location'] is not None:
                if 'lat' in post['location'] and 'lng' in post['location']:
                    lat = post['location']['lat']
                    lng = post['location']['lng']
                    locations[str(lat) + ', ' + str(lng)] = post.get('taken_at')

        address = {}
        for k, v in locations.items():
            details = geolocator.reverse(k)
            unix_timestamp = datetime.datetime.fromtimestamp(v)
            address[details.address] = unix_timestamp.strftime('%Y-%m-%d %H:%M:%S')

        sort_addresses = sorted(address.items(), key=lambda p: p[1], reverse=True)

        if len(sort_addresses) > 0:
            t = PrettyTable()

            t.field_names = ['Post', 'Address', 'time']
            t.align["Post"] = "l"
            t.align["Address"] = "l"
            t.align["Time"] = "l"
            print("\nWoohoo! We found " + str(len(sort_addresses)) + " addresses\n")

            i = 1

            json_data = {}
            addrs_list = []

            for address, time in sort_addresses:
                t.add_row([str(i), address, time])

            print(t)

        # print("Retrieving all comments, this may take a moment...\n")
        # data = __get_feed__()
        #
        # _comments = []
        # t = PrettyTable(['POST ID', 'ID', 'Username', 'Comment'])
        # t.align["POST ID"] = "l"
        # t.align["ID"] = "l"
        # t.align["Username"] = "l"
        # t.align["Comment"] = "l"
        #
        # for post in data:
        #     post_id = post.get('id')
        #     comments = api.media_n_comments(post_id)
        #     for comment in comments:
        #         t.add_row([post_id, comment.get('user_id'), comment.get('user').get('username'), comment.get('text')])
        #         comment = {
        #             "post_id": post_id,
        #             "user_id": comment.get('user_id'),
        #             "username": comment.get('user').get('username'),
        #             "comment": comment.get('text')
        #         }
        #         _comments.append(comment)
        #
        # print(t)

        # target_username = input("Enter username: ")
        #
        # # Fetch the user's info within the authenticated context
        # user_info = api.username_info(target_username)
        #
        # # Print the user's basic information
        # print(f"User ID: {user_info['user']['pk']}")
        # print(f"Username: {user_info['user']['username']}")
        # print(f"Full Name: {user_info['user']['full_name']}")
        # print(f"Bio: {user_info['user']['biography']}")
        # print(f"Followers: {user_info['user']['follower_count']}")
        # print(f"Following: {user_info['user']['following_count']}")
        # print(f"Posts: {user_info['user']['media_count']}")



    except ClientError as e:
        print('Error fetching user info: {0!s}'.format(e))
