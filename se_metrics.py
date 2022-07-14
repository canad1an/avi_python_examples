#!/usr/bin/python3
import argparse
import json
import logging
import sys
import math
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

metrics_to_use = {
    "se_if.avg_bandwidth": {
        "nice_name": "Throughput",
        "format": "data"
        },
    "se_stats.avg_cpu_usage": {
        "nice_name": "Average CPU",
        "format": "percentage"
        },
    "se_stats.avg_mem_usage": {
        "nice_name": "Average Memory",
        "format": "percentage"
        },
}

##### End Configuration #####

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_bytes = size_bytes/8
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

class AviMetrics(object):

    def __init__(self, api):
        self.api = api
        self.api_utils = ApiUtils(api)

    def GetVS(self,ctrl):
        resp = self.api.get('virtualservice')
        if resp.status_code in range(200, 299):
            logger.info(ctrl+': VS Info retrieved successfully')
        else:
            logger.info(ctrl+': Error when getting VS info : {%s}' % resp.text)
        return resp.json()

    def GetSEs(self,ctrl):
        resp = self.api.get('serviceengine-inventory')
        if resp.status_code in range(200, 299):
            logger.info(ctrl+': SE Info retrieved successfully')
        else:
            logger.info(ctrl+': Error when getting SE info : {%s}' % resp.text)
        return resp.json()

    def GetSEUsage(self,ctrl,se,ctime):
        starttime = (datetime.now() - timedelta(hours = ctime)).strftime('%Y-%m-%d %H:%M:%S')
        resp = self.api.get('analytics/metrics/serviceengine/{}?metric_id={}&step={}&start={}'.format(se,",".join(metrics_to_use.keys()),ctime*60*10,starttime))
        if resp.status_code in range(200, 299):
            logger.info(ctrl+': SE Usage retrieved successfully')
        else:
            logger.info(ctrl+': Error when getting SE Usage : %s' % resp.text)
        return resp.json()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help='controller user', default='admin')
    parser.add_argument('-p', '--password', help='controller user password', default='avi123')
    parser.add_argument('-c', '--controller', nargs='+', help='controller ip', required=True)
    parser.add_argument('-t', '--time', type=int, help='Timeframe for query, default is past 24hrs. Time in hours', default='24')

    args = parser.parse_args()   

    data = {}
    for ctrl in args.controller:
        #Get List of all SEs
        api = ApiSession.get_session(ctrl, args.user, args.password, api_version="21.1.3")
        avicontroller = AviMetrics(api)
        SEs = AviMetrics.GetSEs(avicontroller,ctrl)
        selist = []
        for SE in SEs["results"]:
            #Get Metrics for SEs
            metricdata = {}
            Metrics = AviMetrics.GetSEUsage(avicontroller,ctrl,SE["config"]["uuid"],args.time)
            for metric in Metrics["series"]:
                if metrics_to_use[metric["header"]["name"]]["format"] == "percentage":
                    metricdata[metrics_to_use[metric["header"]["name"]]["nice_name"]] = "{}%".format(metric["header"]["statistics"]["mean"])
                if metrics_to_use[metric["header"]["name"]]["format"] == "data":
                    metricdata[metrics_to_use[metric["header"]["name"]]["nice_name"]] = convert_size(metric["header"]["statistics"]["mean"])
            selist.append({"SE Name": SE["config"]["name"], "SE uuid": SE["config"]["uuid"], "SE Metrics": metricdata })
        #Get VS count per controller
        VS_count = AviMetrics.GetVS(avicontroller,ctrl)
        data[ctrl] = {
            "VS Count": VS_count["count"],
            "SEs": selist
        }
    print(json.dumps(data, indent=4, sort_keys=True))



# To use this file:
# python3 license_count_from_controller.py -u 'admin' -p 'Avipassword1' -c 10.10.10.10 10.10.10.11 10.10.10.12 -t 24
