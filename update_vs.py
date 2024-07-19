#!/usr/bin/python3
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta

from avi.sdk.avi_api import ApiSession
from avi.sdk.utils.api_utils import ApiUtils
from avi.sdk.samples.common import get_sample_ssl_params
from requests.packages import urllib3

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(ch)

urllib3.disable_warnings()

##### Configuration #####

# modify_all_vs = False
# vs_modify_list = []
# vs_skip_list = [] #Only used if modify_all_vs is true

field_to_modify = "network_profile_ref"
previous_field = "hol-tcp-profile-custom"
new_field_uuid = "networkprofile-e435c43b-6b84-42c7-b4ca-1b2fbd4b60f3" # must be uuid, name won't work

##### End Configuration #####

class Avi(object):

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

    def GetVS(self,ctrl):
        resp = self.api.get('virtualservice?include_name=true&fields=name,tenant_ref,' + str(field_to_modify))
        if resp.status_code in range(200, 299):
            logger.info(ctrl+': VS Info retrieved successfully')
        else:
            logger.info(ctrl+': Error when getting VS info : {%s}' % resp.text)
        return resp.json()

    def UpdateVS(self,ctrl,vs,dryrun):
        if dryrun:
            logger.info(ctrl+': DRY RUN Enabled: ' + str(vs["name"]) + ' in tenant ' + str(vs["tenant_ref"].split("#")[1]) + ' will have the ' + str(field_to_modify) + ' modified from ' + str(previous_field) + ' to ' + str(new_field_uuid))
        elif not dryrun:
            try:
                updatedata = {"replace": { str(field_to_modify): str(new_field_uuid)} }
                resp = self.api.patch('virtualservice/%s' % vs['uuid'], data=updatedata)
                if resp.status_code in range(200, 299):
                    logger.info(ctrl+': VS Patched successfully')
                else:
                    logger.info(ctrl+': Error when patching VS : {%s}' % resp.text)
                return resp.json()    
            except Exception as e:
                print (e)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller', help='controller ip', required=True)
    parser.add_argument('-v', '--version', help='Avi Version', default="21.1.5")
    parser.add_argument('-d', '--dry_run', help='Test the above config, but dont change anything', action='store_true')

    args = parser.parse_args()   

    if args.dry_run is not False:
        dryrun = True
    else:
        dryrun = False

    api = ApiSession.get_session(args.controller, args.user, args.password, api_version=args.version, tenant="*")
    avicontroller = Avi(api)
    VSs = Avi.GetVS(avicontroller,args.controller)
    vsmatch=0
    if not VSs:
        logger.info(args.controller+': No VSs were found on this controller')
    else:
        for VS in VSs["results"]:
            try:
                # print (VS[field_to_modify].split("#")[1])
                if VS[field_to_modify].split("#")[1] == previous_field:
                    vsmatch += 1
                    VSUpdate = Avi.UpdateVS(avicontroller,args.controller,VS,dryrun)
            except:
                pass
    if vsmatch == 0:
        logger.info(args.controller+': No VS matches were found based on search criteria')
    else:
        if dryrun:
            logger.info(args.controller+': DRY RUN Enabled: ' + str(vsmatch) + 'VSs were updated successfully')
        else:
            logger.info(args.controller+': ' + str(vsmatch) + ' VS were updated successfully')



# To use this file:
# python3 update_vs.py -u 'admin' -p 'Avipassword1' -c 10.10.10.10 -v 21.1.5 -d
