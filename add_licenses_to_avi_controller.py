#!/usr/bin/python3
import argparse
import json
import logging
import sys

from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
from avi.sdk.samples.common import get_sample_ssl_params
from requests.packages import urllib3

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(ch)

urllib3.disable_warnings()


class AviLicenses(object):

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

    def UploadLicenses(self, key):
        key_obj = {
            'serial_key': key
        }
        resp = self.api.put('licensing', data=json.dumps(key_obj))
        if resp.status_code in range(200, 299):
            logger.debug('License Key added successfully')
        else:
            logger.debug('Error adding License Key : %s' % resp.text)



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--option', choices=['UploadLicenses'], help='Upload Licenses', default='licenses')
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-k', '--keys', help='A single key or a list separated by comma', default='na')
    parser.add_argument('-c', '--controller_ip', help='controller ip')
    parser.add_argument('-f', '--file', help='File to import', default='na')

    args = parser.parse_args()
    print('parsed args', args)
    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="20.1.2")
    
    lic = AviLicenses(api)
    if args.option == 'UploadLicenses' and args.keys != 'na':
    	keys = args.keys.strip()
    	for key in keys.split(','):
    		print (key)
    		lic.UploadLicenses(key)

    elif args.option == 'UploadLicenses' and args.file != 'na':
    	keysf = open(args.file, 'r') 
    	keys = keysf.readlines()
    	keysf.close()
    	for key in keys:
    		print (key)
    		lic.UploadLicenses(key.rstrip())



# By license as a list or single:
# python3 deploy_certs.py -o 'UploadLicenses' -u 'admin' -p 'Avipassword1' -k '40SEF4-433H-88FE-E5353-SSD,SF-4323-FDSDF-KLUI-7898,KJJ-ILI-ULU-7898-JKLK' -c '10.10.10.10'
# By license file, separated by new lines:
# python3 deploy_certs.py  -o 'UploadLicenses' -u 'admin' -p 'Avipassword1' -f lics.txt -c '10.10.10.10'