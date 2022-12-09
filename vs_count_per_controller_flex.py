#!/usr/bin/python3
import argparse
import json
import logging
import sys

from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
from avi.sdk.samples.common import get_sample_ssl_params
from requests.packages import urllib3

# logger = logging.getLogger(__name__)
# ch = logging.StreamHandler(sys.stdout)
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.DEBUG)
# root_logger.addHandler(ch)

urllib3.disable_warnings()


class VSperController(object):

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

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

    def GetVSData(self):
        resp = self.getavicontent('virtualservice','')
        return resp



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller_ip', help='controller ip')
    parser.add_argument('-v', '--verbose', action="store_true")

    args = parser.parse_args()

    #Logging
    logger = logging.getLogger(__name__)
    ch = logging.StreamHandler(sys.stdout)
    root_logger = logging.getLogger()
    if (args.verbose):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.ERROR
    root_logger.setLevel(loglevel)
    root_logger.addHandler(ch)

    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="21.1.4")
    
    vscount = VSperController(api)
    vs_data = {}
    for vs in vscount.GetVSData():
        portlist = []
        try:
            for po in vs["services"]:
                portlist.append(po["port"])
        except:
            portlist.append("0")

        vs_data[vs['name']] = { "ports": portlist}

    #Count Totals
    vs_count=0
    vs_by_port_count=0
    totals_data = {}
    for vs in vs_data:
        vs_count += 1
        for po in vs_data[vs]["ports"]:
            vs_by_port_count += 1
    totals_data["Total"] = {
        "Virtual Services": vs_count,
        "Virtual Services by Port": vs_by_port_count
    }
    if (args.verbose):
        final_data = {**vs_data, **totals_data}
    else:
        final_data = totals_data
    print(json.dumps(final_data, indent=4, sort_keys=True))

# Get virtual count of each SE:
# python virtualservice_count_per_se.py -c 10.206.114.131 -u admin -p Avi12
