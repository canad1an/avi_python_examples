#!/usr/bin/python3
import argparse
import json
import logging
import sys
import socket

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

class GSLBSERVICE(object):

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

    def getGSLBCLUSTER(self,site_name):
        gsdic = {}
        cluster_uuid = ''
        resp = self.getavicontent('gslb','')
        gslb_sites = resp[0]["sites"]
        for gslbsite in gslb_sites:
            if site_name == gslbsite["name"]:
                cluster_uuid = gslbsite["cluster_uuid"] 

        return cluster_uuid

    def getGSLBSERVICES(self):
        resp = self.getavicontent('gslbservice','')
        self.storeSTATE(json.dumps(resp))
        return resp

    def disableGSLBSERVICES(self,site_name,dryrun):
        cluster_uuid = self.getGSLBCLUSTER(site_name)
        gsdic = self.getGSLBSERVICES()
        gsdic_new = gsdic
        gsc=0
        print (dryrun)
        for gs in gsdic:
            grc=0
            for group in gs["groups"]:
                mmc=0
                for member in group["members"]:
                    try:
                        if member["cluster_uuid"] == cluster_uuid:
                            if dryrun:
                                logger.debug('DRYRUN: Gslbservice: %s VS: %s' % (gsdic[gsc]["name"], gsdic[gsc]["groups"][grc]["members"][mmc]["vs_uuid"]))
                            else:
                                gsdic_new[gsc]["groups"][grc]["members"][mmc]["enabled"] = False
                        mmc += 1
                    except Exception as e:
                        mmc += 1
                        continue
                grc += 1
            gsc += 1
        if not dryrun:
            for gs in gsdic_new:
                gs.pop('_last_modified', None)
                resp = self.api.put('gslbservice/%s' % gs['uuid'], data=gs)
                if resp.status_code in range(200, 299):
                    logger.debug('GSLBService Pool member disabled: %s' % gs['uuid'])
                else:
                    logger.debug('GSLBService Pool member disabled: %s' % resp.text)

    def storeSTATE(self,gsdic):
        file = open("gslbservice_state", "w") 
        file.write(gsdic) 
        file.close() 

    def restoreSTATE(self):
        with open('gslbservice_state', 'r') as file:
            gsdic = json.load(file)
        for gs in gsdic:
            gs.pop('_last_modified', None)
            resp = self.api.put('gslbservice/%s' % gs['uuid'], data=gs)
            if resp.status_code in range(200, 299):
                logger.debug('GSLBService Restored: %s' % gs['uuid'])
            else:
                logger.debug('GSLBService not Restored: %s' % resp.text)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller_ip', help='controller ip')
    parser.add_argument('-n', '--site_name', help='Name of the current Site')
    parser.add_argument('-o', '--option', help='[disable|restore]')
    parser.add_argument('-d', '--dry_run', help='Test the above config, but dont change anything', action='store_true')

    args = parser.parse_args()
    print('parsed args', args)

    api = ApiSession.get_session(args.controller_ip, args.user, args.password, api_version="20.1.2")
    gslbservice = GSLBSERVICE(api)

    if args.dry_run is not False:
        dryrun = True
    else:
        dryrun = False

    if args.option == "restore":
        gslb_services = gslbservice.restoreSTATE(dryrun)
    elif args.option == "disable":
        gslb_services = gslbservice.disableGSLBSERVICES(args.site_name,dryrun)

# Example Call:
# python3 gslb_site_maintenance.py -u 'admin' -p 'Avipassword1' -c '10.10.10.10' -d -o disable -n site1