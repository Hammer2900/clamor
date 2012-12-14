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
        if not(request.get_cookie('PYSESSID')) or not(self.data.has_key(new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest())):
            self.data[new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()] = {}
    def set(self, n, v):
        try:
            sid = new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()
            self.data[sid][n] = v
        except KeyError:
            pass
    def get(self, n):
        sid = new('sha1', request.get_cookie('PYSESSID') + request['REMOTE_ADDR']).hexdigest()
        try:
            return self.data[sid][n]
        except KeyError:
            return None
