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


class VSperSE(object):

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

    def GetSEData(self):
        resp = self.api.get('serviceengine')
        if resp.status_code in range(200, 299):
            logger.debug('SE Data grabbed')
        else:
            logger.debug('Error grabbing SE data : %s' % resp.text)
        return resp.json()['results']




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller_ip', help='controller ip')

    args = parser.parse_args()
    print('parsed args', args)
    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="20.1.3")
    
    vscount = VSperSE(api)
    json = {}
    for se in vscount.GetSEData():
        json[se['name']] = len(se['vs_refs'])
    print (json)

# Get virtual count of each SE:
# python virtualservice_count_per_se.py -c 10.206.114.131 -u admin -p Avi12
