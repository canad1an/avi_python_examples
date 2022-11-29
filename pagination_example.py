#!/usr/bin/python3.6
import requests
import urllib3
from avi.sdk.avi_api import ApiSession
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#############################################################################
################################ AVI Login ##################################
#############################################################################

faileddevices = ['']
def avi(dev):
	api = ApiSession.get_session(dev, "serviceuser", "password  ", tenant="*", timeout=5, api_version="18.2.8")
	return api

def getavicontent(request):
    pagesize = "5"
    nextpagination = 1
    datadic = []
    api = avi(device)
    while nextpagination != 0:
        data = api.get(str(request)+ '?page_size=' + str(pagesize) + '&page=' + str(nextpagination))
        datai = data.json()['results']
        for i in datai:
            datadic.append(i)
        if 'next' in data.json():
            nextpagination += 1
        else:
            nextpagination = 0

    return datadic

def delete(request):
    api = avi(device)
    data = api.delete(str(request))
    datai = data.json()['results']
    return datai
devices=['10.206.114.19']


#############################################################################
######################## Update SE Virtual Services #########################
#############################################################################

for device in devices: ############ LOOP DEVICES ############
	if device in faileddevices:
		continue
	try:	
		virtuals = getavicontent('virtualservice')
		
		for vs in virtuals
			deleteme = delete(vs["uuid"])
			print (deleteme)
	except Exception as e:
		faileddevices.append(device)

#############################################################################
########################### Update SE Pool Groups ###########################
#############################################################################

for device in devices: ############ LOOP DEVICES ############
	if device in faileddevices:
		continue
	try:
		poolgroups = getavicontent('poolgroup')
		print (poolgroups)
	except Exception as e:
		faileddevices.append(device)

#############################################################################
############################### Update SE Pools #############################
#############################################################################

for device in devices: ############ LOOP DEVICES ############
	if device in faileddevices:
		continue
	try:
		pools = getavicontent('pool')
		print (pools)
	except Exception as e:
		faileddevices.append(device)
