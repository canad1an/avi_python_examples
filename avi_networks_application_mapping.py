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


class AviSearch(object):

    def getavicontent(self,request,params):
        pagesize = "200"
        nextpagination = 1
        datadic = []
        while nextpagination != 0:
            data = self.api.get(str(request)+ '?page_size=' + str(pagesize) + '&page=' + str(nextpagination) + '&' + params)
            if data.status_code in range(200, 299):
                logger.debug('Retrieved list of virtual services')
            else:
                logger.debug('Did not retrieve list of virtual services : %s' % data.text)
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

    def getVirtuals(self):
        resp = self.getavicontent('virtualservice','')
        return resp

    def getLogs(self,vsuuid):
        resp = self.getavicontent('analytics/logs','virtualservice=' + vsuuid + '&duration=2592000&udf=true&nf=true')
        print (resp)
        return resp

    def getLinkedVips(self):
        virtuals = self.getVirtuals()
        for vs in virtuals:
            logs = self.getLogs(vs["uuid"])
        return logs


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--option', choices=['AppMap'], help='Mapp Applications', default='licenses')
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='Avipassword1')


    args = parser.parse_args()
    print('parsed args', args)
    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="20.1.1", tenant="*", timeout=5)
    
    search = AviSearch(api)
    search.getLinkedVips()



# Get Links:
# python3 vip-request-id-mapping.py -u 'admin' -p 'Avipassword1' -c '10.10.10.10'