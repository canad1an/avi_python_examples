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
