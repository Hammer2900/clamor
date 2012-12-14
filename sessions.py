# The unofficial Sessions addon for Bottle (bottlepy.org)
# Made by Magnie (magnie.tk) and Ohaider (fallingduck.tk)
# License: MIT

from random import randint
from time import time
from hashlib import new
from bottle import request, response

class Session(object):
    def __init__(self):
        self.data = {}
    def start(self):
        if not(request.get_cookie('PYSESSID')):
            sid = new('sha1', str(int(time() * 1000)) + str(randint(0, 4596))).hexdigest()
            response.set_cookie('PYSESSID', sid)
            sid = new('sha1', sid + request['REMOTE_ADDR']).hexdigest()
            self.data[sid] = {}
        try:
            if not(self.data.has_key(new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest())):
                self.data[new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()] = {}
        except:
            pass
    def set(self, n, v):
        try:
            sid = new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()
            self.data[sid][n] = v
        except:
            pass
    def get(self, n):
        try:
            sid = new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()
            return self.data[sid][n]
        except:
            return None
