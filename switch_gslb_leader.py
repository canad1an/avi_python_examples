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

class GSLB(object):

    def getavicontent(self,request,params):
        pagesize = "200"
        nextpagination = 1
        datadic = []
        while nextpagination != 0:
            data = self.api.get(str(request)+ '?page_size=' + str(pagesize) + '&page=' + str(nextpagination) + '&' + params)
            if data.status_code in range(200, 299):
                logger.debug('Retrieved list')
            else:
                logger.debug('Did not retrieve list: %s' % data.text)
            datai = data.json()['results']
            for i in datai:
                datadic.append(i)
            if 'next' in data.json():
                nextpagination += 1
            else:
                nextpagination = 0  
        return datadic

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

    def getGSLB(self,controller_ip):
        resp = self.getavicontent('gslb','')
        gslb_leader_uuid = resp[0]["leader_cluster_uuid"]
        gslb_sites = resp[0]["sites"]
        for gslbsites in resp[0]["sites"]:
            for ip in gslbsites["ip_addresses"]:
                if controller_ip in ip["addr"]:
                    current_cluster_uuid = gslbsites["cluster_uuid"]
        return gslb_leader_uuid, current_cluster_uuid

    def switchGSLB(self, cluster_id):
        gslb_obj = {
            'new_leader': cluster_id
        }
        resp = self.api.post('gslbsiteops/changeleader', data=json.dumps(gslb_obj))
        if resp.status_code in range(200, 299):
            logger.debug('Leader change successful')
        else:
            logger.debug('Leader change unsuccessful : %s' % resp.text)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller_ip', help='controller ip')

    args = parser.parse_args()
    print('parsed args', args)
    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="20.1.2")
    
    gslb = GSLB(api)
    gslb_leader_uuid, current_cluster_uuid = gslb.getGSLB(args.controller_ip)
    if (current_cluster_uuid != gslb_leader_uuid):
        logger.debug('Current controller cluster is already the gslb leader')
    else:
        logger.debug('Current controller cluster is not already the gslb leader')
        gslb.switchGSLB(current_cluster_uuid)

# Example Call:
# python3 switch_gslb_leader.py -u 'admin' -p 'Avipassword1' -c '10.10.10.10'