#############################################################
# The unofficial Sessions addon for Bottle (bottlepy.org)   #
# Made by Magnie (magnie.tk) and Ohaider (fallingduck.tk)   #
# License: MIT                                              #
#############################################################

#################
# DOCUMENTATION
#################
# Dependencies: Bottle (bottlepy.com)
# Commands:
#   sessions.Session()
#       This class should be initialized at the start of the server, and will run throughout the server's existence
#   Session.start()
#       Should be called on each page that uses sessions, it initializes the user's session, or if the user already has an active session, pulls the info to the front
#   Session.set(name, value)
#       Set a name and value pair for the user's current session
#   Session.get(name)
#       Returns the value for the name key, or None if key doesn't exist
#################
# EXAMPLE
#################
# from sessions import Session
# from bottle import route, run, redirect
#
# session = Session()
#
# @route('/')
# def hello():
#   global session
#   session.start()
#   session.set('name', 'World')
#   redirect('/hello')
#
# @route('/hello')
#   global session
#   session.start()
#   if not(session.get('name')):
#       redirect('/')
#   return 'Hello, ' + session.get('name') + '!'
#################

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
