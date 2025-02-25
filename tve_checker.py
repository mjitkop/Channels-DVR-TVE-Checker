"""
Author: Gildas Lefur (a.k.a. "mjitkop" in the Channels DVR forums)

Description: This module contains the main code that performs the connection checks. 

Disclaimer: this is an unofficial script that is NOT supported by the developers of Channels DVR.

Version History:
- 2025.02.24.2052: Started internal development.
"""

################################################################################
#                                                                              #
#                                   IMPORTS                                    #
#                                                                              #
################################################################################

import argparse, requests, sys, time

################################################################################
#                                                                              #
#                                  CONSTANTS                                   #
#                                                                              #
################################################################################

API_CHANNELS        = 'api/v1/channels'
DEFAULT_PORT_NUMBER = '8089'
DEFAULT_IP_ADDRESS  = '127.0.0.1'
MINIMUM_FREQUENCY   = 60 # minutes
VERSION             = '2025.02.24.2052'

################################################################################
#                                                                              #
#                                  FUNCTIONS                                   #
#                                                                              #
################################################################################

def test_video_stream(url):
    test_ok = False
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            # Make sure the link is valid
            if response.status_code == 200:
                # Read a chunk of the stream to verify it's working
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        test_ok = True
                        break
                    else:
                        print('Link valid but no video received.')
            else:
                print("The video stream is not working. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
    return test_ok

################################################################################
#                                                                              #
#                                   CLASSES                                    #
#                                                                              #
################################################################################

class ChannelsDVRServer:
    '''Attributes and methods to interact with a Channels DVR server.'''
    def __init__(self, ip_address=DEFAULT_IP_ADDRESS, port_number=DEFAULT_PORT_NUMBER):
        '''Initialize the server attributes.'''
        self.ip_address  = ip_address
        self.port_number = port_number

    def get_tve_channels(self):
        '''
        Return the list of non-hidden channels from all TVE sources.

        The output will be a JSON dictionary:
            keys   = channel numbers
            values = channel names
        '''
        api_channels = f'http://{self.ip_address}:{self.port_number}/{API_CHANNELS}'
        tve_channels = {}

        channels = requests.get(api_channels).json()

        for channel in channels:
            hidden = channel.get('hidden', False)

            if not hidden and channel['source_id'].startswith('TVE'):
                tve_channels[channel['number']] = channel['name']

        return tve_channels

        
################################################################################
#                                                                              #
#                                     MAIN                                     #
#                                                                              #
################################################################################

if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(
                description = "Test the connections of all non-hidden TVE channels.")

    # Add the input arguments
    parser.add_argument('-f', '--frequency', type=int, default=MINIMUM_FREQUENCY, \
            help='Frequency of queries sent to the Channels DVR server, in minutes. Default = minimum: 60 minutes.')
    parser.add_argument('-i', '--ip_address', type=str, default=DEFAULT_IP_ADDRESS, \
                        help='IP address of the Channels DVR server. Default: 127.0.0.1')
    parser.add_argument('-p', '--port_number', type=str, default=DEFAULT_PORT_NUMBER, \
                        help='Port number of the Channels DVR server. Default: 8089')
    parser.add_argument('-v', '--version', action='store_true', help='Print the version number and exit the program.')

    # Parse the arguments
    args = parser.parse_args()

    # Access the values of the arguments
    frequency         = args.frequency
    ip_address        = args.ip_address
    port_number       = args.port_number
    version           = args.version

    # If the version flag is set, print the version number and exit
    if version:
        print(VERSION)
        sys.exit()

    # Sanity check of the provided arguments.
    if frequency < MINIMUM_FREQUENCY:
        print(f'Minimum frequency of {MINIMUM_FREQUENCY} minutes! Try again.')
        sys.exit()
        
    # All good. Let's go!

    DVR = ChannelsDVRServer(ip_address, port_number)

    while True:
        tve_channels = DVR.get_tve_channels()

        if not tve_channels:
            print(f'No TVE channels received from the Channels DVR server at http://{ip_address}:{port_number}!')
            sys.exit()

        sorted_channels = list(tve_channels.keys())
        sorted_channels.sort()

        print(f'Testing the connections of {len(sorted_channels)} TVE channels...')
        for ch_number in sorted_channels:
            ch_name = tve_channels[ch_number]
            stream_url = f'http://{ip_address}:{port_number}/devices/ANY/channels/{ch_number}/stream.mpg'

            print(f'  #{ch_number} ({ch_name}):', end=' ')
            if test_video_stream(stream_url):
                print('OK')

        print(f'Next check in {frequency} minutes.\n')
        time.sleep(frequency)
        