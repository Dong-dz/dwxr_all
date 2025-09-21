import urllib
import urllib.request
import json


def http_post(url_base, request_body):
    try:
        url = url_base
        json_s = json.dumps(request_body)
        f = urllib.request.urlopen(urllib.request.Request(url, json_s.encode(), {"Content-Type": "application/json"}))
        response = f.read().decode('utf-8')
        print(response)
        return response
    except Exception as err:
        print(err)
        return ""
