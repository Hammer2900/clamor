#########################################################
# Clamor Microforum Software                            #
# By Falling Duck (fallingduck.tk)                      #
# License: MIT                                          #
#########################################################


# Change these variables to set up your distro of Clamor
mysql_hostname = 'localhost'
mysql_username = 'root'
mysql_password = 'password'
mysql_database = 'clamor'
site_host = '0.0.0.0' # Leave this the way it is to serve on any server, make it specific to bind to a specific address
site_title = 'Clamor'
site_desc = 'Welcome to Clamor, a microforum where you can join in conversations anonymously.'


# Dependencies outside of normal Python 2.7 installation:
# Bottle (bottlepy.com)
# Paste (pythonpaste.org) (OPTIONAL, SEE VERY BOTTOM OF PROGRAM)
# MySQLdb (sourceforge.net/projects/mysql-python)
# Sessions (included in Clamor distro)
from bottle import route, run, request, error, abort, redirect
import MySQLdb as mysql, bottle
from hashlib import new
from sessions import Session
from cgi import escape
from time import time

# Uncomment the next line to setup the Paste server
# from paste import httpserver

# Constants (ok, variables) that will be used throughout the site
connect = "mysql.connect('{0}', '{1}', '{2}', '{3}')".format(mysql_hostname, mysql_username, mysql_password, mysql_database)
header = '''<!DOCTYPE html>
<html>
<head>
<title>''' + site_title + '''</title>
<style type="text/css">
body {width: 800px; margin-right: auto; margin-left: auto; margin-top: 25px;}
a {text-decoration: none; color: #00F;}
.headerlink {margin-left: 5px; text-decoration: none; font-family: Arial; font-size: 10pt; color: #FFF;}
.headerlink:hover {color: #FF0; text-decoration: none;}
header {position: fixed; top: 0px; width: 800px; background-color: #000; padding: 2px;}
a:hover {text-decoration: underline;}
.post {border: 1px solid #000; padding: 5px; margin-bottom: 5px;}
.date {color: #CCC; float: right;}
</style>
</head>
<body>
<header>
<a href="/" class="headerlink"><b>Home</b></a>
<a href="/admin" class="headerlink"><b>Admin</b></a>
</header>'''
footer = '''</body>
</html>'''
session = Session()

# Helpful 404 message
@error(404)
def filenotfound(error):
    global header, footer
    return header + '''<h1>Error 404: File not Found!</h1>
<p>It looks like you somehow got a bad URL! If you followed a link here, please contact the owner of the link to have it rectified!</p>''' + footer

# Helpful 500 message
@error(500)
def difficulties(error):
    global header, footer
    return header + '''<h1>Error 500: Internal Server Error</h1>
<p>It looks like we're experiencing some difficulties! If this problem persists contact the system administrator.</p>''' + footer

# Home page
# Shown here for everybody: index of all channels
# Shown here for mods: delete channels, create channels
@route('/')
def show_index():
    global connect, header, footer, session, site_title, site_desc
    session.start()
    content = header + '''<h1>''' + site_title.upper() + '''</h1>
<p>''' + site_desc + '''</p>
<hr />
<div style="float: left;">
<h4>All Channels</h4>'''
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT * FROM rooms;")
    for i in range(int(c.rowcount)):
        t = c.fetchone()
        content += '<div><a href="/' + str(int(t[0])) + '">' + t[1] + '</a>'
        if session.get('username'):
            content += '&nbsp;[<a href="/admin/delchan/' + str(int(t[0])) + '">Delete</a>]'
        content += '</div>'
    if session.get('username'):
        content += '<p><a href="/admin/add">Add Channel</a></p>'
    content += '''</div>
<div style="float: right;">
<h4>Recent Posts</h4>'''
    c.execute("SELECT room_id, nick, posting FROM posts ORDER BY date DESC LIMIT 10;")
    if int(c.rowcount):
        for i in range(int(c.rowcount)):
            t = list(c.fetchone())
            if len(t[2]) > 50:
                t[2] = t[2][:50] + '...'
            content += '<div><a href="/' + str(t[0]) + '">' + t[1] + ': ' + t[2] + '</div>'
    content += '</div>' + footer
    return content

# Dynamic page for each channel
# Shown here for everybody: post new message, view the newest 50 messages, report a message
# Shown here for mods: view all posts from an IP, delete post
@route('/<chan:int>')
def show_channel(chan):
    global connect, header, footer, session
    session.start()
    content = header
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT name, description FROM rooms WHERE id=%s;", (chan,))
    if int(c.rowcount):
        t = c.fetchone()
        content += "<h1>" + t[0] + '''</h1>
<p>''' + t[1] + '''</p>
<hr />'''
        content += '''<form method="post" action="/''' + str(chan) + '''">
<table>
<tr><td><label for="nick">Name:</label></td><td><input type="text" name="nick" id="nick" maxlength="24" size="50" /></td></tr>
<tr><td><label for="posting">Post:</label></td><td><input type="text" name="posting" id="posting" maxlength="1000" size="50" />&nbsp;<input type="submit" value="Post" /></td></tr>
</table>
</form>'''
        c.execute("SELECT id, nick, posting, date, ip FROM posts WHERE room_id=%s ORDER BY date DESC LIMIT 20;", (chan,))
        if int(c.rowcount):
            for i in range(int(c.rowcount)):
                t = c.fetchone()
                content += '<div class="post"><b>' + t[1] + '</b><span class="date">' + str(t[3]) + '</span><span class="link">&nbsp;'
                if session.get('username'):
                    content += '<a href="/admin/delpost/' + str(t[0]) + '">Delete</a>&nbsp;<a href="/admin/viewip/' + t[4] + '">View IP</a>'
                else:
                    content += '<a href="/admin/report/' + str(t[0]) + '">Report</a>'
                content += '</span><br />' + t[2] + '</div>'
        else:
            content += "<p><i>No posts in this channel yet!</i></p>"
        db.close()
    else:
        db.close()
        abort(code=404, text='Invalid channel ID!')
    content += footer
    return content

# This handles the posting of a new message
@route('/<chan:int>', method='POST')
def record_post(chan):
    global connect, session
    session.start()
    nick = escape(request.forms.get('nick'))
    if session.get('username'):
        nick = '<i>' + nick + '</i>'
    posting = escape(request.forms.get('posting'))
    ip = request['REMOTE_ADDR']
    content = header
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id FROM rooms WHERE id=%s;", (chan,))
    if int(c.rowcount):
        c.execute("SELECT reason FROM bans WHERE ip=%s;", (ip,))
        if int(c.rowcount):
            db.close()
            return header + '<p style="color: #F00;">Your IP has been banned because: ' + c.fetchone()[0] + '</p>' + footer
        c.execute("SELECT UNIX_TIMESTAMP(date) FROM posts WHERE ip=%s ORDER BY date DESC LIMIT 1;", (ip,))
        if int(c.rowcount):
            t = c.fetchone()
            if int(time()) - int(t[0]) < 120:
                db.close()
                return header + '<p style="color: #F00;">At least 2 minutes must pass between posts. Please wait a while and try again!</p>' + footer
        c.execute("INSERT INTO posts (id, room_id, nick, posting, date, ip) VALUES (0, %s, %s, %s, NOW(), %s);", (chan, nick, posting, ip))
        db.commit()
        db.close()
        redirect('/' + str(chan))
    else:
        db.close()
        abort(code=404, text='Invalid channel ID!')

# Admin login
# If there are no admin accounts found, this page will display a registration form
# When the registration form is submitted, an admin account is created, with the rank of Owner
# Shown here for people not logged in: login page
# Shown here for people logged in: redirect to admin panel
@route('/admin')
def admin_login():
    global connect, header, footer, session
    session.start()
    if session.get('username'):
        redirect('/admin/')
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id FROM mods;")
    if int(c.rowcount):
        return header +'''<div style="text-align: center;">
<h1>Administrator Login</h1>
<form method="post" action="/admin">
<table style="margin-right: auto; margin-left: auto;">
<tr><td><label for="username">Username:</label></td><td><input type="text" name="username" id="username" /></td></tr>
<tr><td><label for="password">Password:</label></td><td><input type="password" name="password" id="password" /></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Login" /></td></tr>
</table>
</form>
</div>''' + footer
    else:
        return header + '''<div style="text-align: center;">
<h1>Welcome to the Admin Panel!</h1>
<p>You're almost ready to make your Clamor implementation available to the public! All you need to do now is create your admin account!</p>
<form method="post" action="/admin/registerfirst">
<input type="hidden" name="rank" value="3" />
<table style="margin-right: auto; margin-left: auto;">
<tr><td><label for="username">Username:</td><td><input type="text" name="username" id="username" /></td></tr>
<tr><td><label for="password">Password:</td><td><input type="password" name="password" id="password" /></td></tr>
<tr><td><label for="confirm">Confirm:</td><td><input type="password" name="confirm" id="confirm" /></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Create" /></td></tr>
</table>
</form>''' + footer

# Handles admin login form
@route('/admin', method='POST')
def admin_auth():
    global connect, session
    session.start()
    username = request.forms.get('username')
    password = new('sha512', request.forms.get('password')).hexdigest()
    ip = request['REMOTE_ADDR']
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT rank FROM mods WHERE usern=%s AND passw=%s;", (username, password))
    if int(c.rowcount):
        t = int(c.fetchone()[0])
        if t == 0:
            redirect('/admin')
        session.set('username', username)
        session.set('rank', t)
        c.execute("UPDATE mods SET ip=%s, last_login=NOW() WHERE usern=%s;", (ip, username))
        db.commit()
        db.close()
        redirect('/admin/')
    else:
        db.close()
        redirect('/admin')

# Admin control panel
# Non-admins are redirected to login
# For all ranks of mods: View User Reports, View/Add Banned IPs, View List of Admin Accounts
# For admins and owner: Create New Admin Account, Promote/Demote Admin
@route('/admin/')
def admin_home():
    global header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    content = header + '''<h1>Admin Panel</h1>
<p>Welcome back, ''' + session.get('username') + '''!</p>
<hr />
<div><a href="/admin/reports">View User Reports</a></div>
<div><a href="/admin/bans">View/Add Banned IPs</a></div>
<div><a href="/admin/accounts">View All Admin Accounts</a></div>'''
    if session.get('rank') > 1:
        content += '''<div><a href="/admin/register">Create New Admin Account</a></div>
<div><a href="/admin/promote">Promote/Demote Admin</a></div>'''
    content += footer
    return content

# Add new channel
# Non-admins are redirected to login
@route('/admin/add')
def channel_form():
    global header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    return header + '''<div style="text-align: center;">
<h1>Create a New Channel</h1>
<form method="post" action="/admin/add">
<table style="margin-right: auto; margin-left: auto;">
<tr><td><label for="name">Name:</label></td><td><input type="text" name="name" id="name" maxlength="28" /></td></tr>
<tr><td><label for="description">Description:</label></td><td><textarea name="description" id="description" maxlength="255"></textarea></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Create" /></td></tr>
</table>
</form>
</div>''' + footer

# Handles add channel form
@route('/admin/add', method='POST')
def add_channel():
    global connect, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    channel = request.forms.get('name')
    desc = request.forms.get('description')
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id FROM rooms WHERE name=%s;", (channel,))
    if int(c.rowcount):
        c.execute("UPDATE rooms SET description=%s WHERE name=%s;", (desc, channel))
        db.commit()
        db.close()
    else:
        c.execute("INSERT INTO rooms (id, name, description) VALUES (0, %s, %s);", (channel, desc))
        db.commit()
        db.close()
    redirect('/')

# View all user reports here
# Non-admins are redirected to login
# Admins can see the reporter's IP, the reason for the report, and the post itself
@route('/admin/reports')
def view_reports():
    global connect, header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    content = header + '<h1>Posts Reported by Users</h1>'
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id, post_id, reason, reporter_ip FROM reports;")
    if int(c.rowcount):
        r = []
        for i in range(int(c.rowcount)):
            t = c.fetchone()
            r.append([t[0], t[1], t[2], t[3]])
        for i in r:
            c.execute("SELECT nick, posting, date, ip FROM posts WHERE id=%s;", (i[1],))
            t = c.fetchone()
            content += '''<hr />
<a href="/admin/delreport/''' + str(i[0]) + '''">Delete</a>
<table>
<tr><td>Reporter:</td><td><a href="/admin/viewip/''' + i[3] + '''">''' + i[3] + '''</a></td></tr>
<tr><td>Because:</td><td>''' + i[2] + '''</td></tr>
</table>'''
            if not(int(c.rowcount)):
                continue
            content += '<div class="post"><b>' + str(t[0]) + '</b><span class="date">' + str(t[2]) + '</span><span class="link">&nbsp;<a href="/admin/delpost/' + str(i[1]) + '">Delete</a>&nbsp;<a href="/admin/viewip/' + str(t[3]) + '">View IP</a></span><br />' + str(t[1]) + '</div>' + footer
    else:
        content += '<hr /><p><i>Hooray! There are no reported posts!</i></p>' + footer
    db.close()
    return content

# Delete a report
@route('/admin/delreport/<report:int>')
def delete_report(report):
    global header, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    db = eval(connect)
    c = db.cursor()
    c.execute("DELETE FROM reports WHERE id=%s;", (report,))
    db.commit()
    db.close()
    redirect('/admin/reports')

# Delete a channel confirm, in case "Delete" is hit automatically
@route('/admin/delchan/<chan:int>')
def confirm_delete_chan(chan):
    global header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    return header + '''<div style="text-align: center;">
<h1>Confirm Channel Deletion</h1>
<p>Are you sure you want to delete this channel?&nbsp;
<form method="post" action="/admin/delchan/''' + str(chan) + '''">
<input type="submit" value="Delete" />&nbsp;
</form>
<a href="/">NO! Take me back!</a></p>
</div>''' + footer

# Delete a channel and all of its posts
@route('/admin/delchan/<chan:int>', method='POST')
def delete_chan(chan):
    global connect, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    db = eval(connect)
    c = db.cursor()
    c.execute('DELETE FROM rooms WHERE id=%s;', (chan,))
    c.execute('DELETE FROM posts WHERE room_id=%s;', (chan,))
    db.commit()
    db.close()
    redirect('/')

# Register new admin account
# Only owners and admins can reach this page, not mods
@route('/admin/register')
def new_admin_form():
    global header, footer, session
    session.start()
    if not(session.get('username')) or session.get('rank') < 2:
        redirect('/admin')
    return header + '''<div style="text-align: center;">
<h1>Create New Admin Account</h1>
<form method="post" action="/admin/register">
<table style="margin-right: auto; margin-left: auto;">
<tr><td><label for="username">Username:</td><td><input type="text" name="username" id="username" /></td></tr>
<tr><td><label for="password">Password:</td><td><input type="password" name="password" id="password" /></td></tr>
<tr><td><label for="confirm">Confirm:</td><td><input type="password" name="confirm" id="confirm" /></td></tr>
<tr><td>Rank:</td><td><input type="checkbox" name="rank" value="1" id="mod" /><label for="mod">Moderator</label><input type="checkbox" name="rank" value="2" id="admin" /><label for="admin">Admin</label></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Create" /></td></tr>
</table>
</form>''' + footer

# Register new admin account form handling
@route('/admin/register', method='POST')
def create_account():
    global connect, session
    session.start()
    if not(session.get('username')) or session.get('rank') < 2:
        redirect('/admin')
    username = request.forms.get('username')
    password = new('sha512', request.forms.get('password')).hexdigest()
    confirm = new('sha512', request.forms.get('confirm')).hexdigest()
    rank = int(request.forms.get('rank'))
    if password != confirm:
        redirect('/admin/register')
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id FROM mods WHERE usern=%s;", (username,))
    if int(c.rowcount):
        redirect('/admin/register')
    c.execute("INSERT INTO mods (id, usern, passw, ip, last_login, rank) VALUES (0, %s, %s, %s, NOW(), %s);", (username, password, '0.0.0.0', rank))
    db.commit()
    db.close()
    redirect('/admin')

# Delete a post confirm
@route('/admin/delpost/<post:int>')
def confirm_delete_post(post):
    global header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    return header + '''<div style="text-align: center;">
<h1>Confirm Post Deletion</h1>
<p>Are you sure you want to delete this post?&nbsp;
<form method="post" action="/admin/delpost/''' + str(post) + '''">
<input type="submit" value="Delete" />&nbsp;
</form>
<a href="/">NO! Take me back!</a></p>
</div>''' + footer

# Delete a post
@route('/admin/delpost/<post:int>', method='POST')
def delete_post(post):
    global connect, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    db = eval(connect)
    c = db.cursor()
    c.execute('DELETE FROM posts WHERE id=%s;', (post,))
    db.commit()
    db.close()
    redirect('/')

# Anybody can technically report a post for a moderator to see
# A reason must be given, and the IP will be recorded
@route('/admin/report/<post:int>')
def report_form(post):
    global header, footer
    return header + '''<div style="text-align: center;">
<h1>Report a Post</h1>
<p>If a post offends you, you can report it to alert a mod. Keep in mind your IP will be recorded, but will not be shared.</p>
<form method="post" action="/admin/report/''' + str(post) + '''">
<label for="reason">Reason:</label><input type="text" name="reason" id="reason" size="20" maxlength="255" /><br />
<input type="submit" value="Report" />
</form></div>''' + footer

# Report the post
@route('/admin/report/<post:int>', method='POST')
def report_post(post):
    global connect
    db = eval(connect)
    c = db.cursor()
    reason = request.forms.get('reason')
    ip = request['REMOTE_ADDR']
    c.execute('INSERT INTO reports (id, post_id, reason, reporter_ip) VALUES (0, %s, %s, %s);', (post, reason, ip))
    db.commit()
    db.close()
    redirect('/')

# View all posts by an IP
# Useful to see if a user is who they say they are and to see if they have a history of trolling
@route('/admin/viewip/<ip>')
def view_ip(ip='0.0.0.0'):
    global connect, header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    content = header + '<h1>Posts by ' + ip + '</h1><hr />'
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id, nick, posting, date FROM posts WHERE ip=%s ORDER BY date DESC LIMIT 20;", (ip,))
    if int(c.rowcount):
        for i in range(int(c.rowcount)):
            t = c.fetchone()
            content += '<div class="post"><b>' + t[1] + '</b><span class="date">' + str(t[3]) + '</span><span class="link">&nbsp;<a href="/admin/delpost/' + str(t[0]) + '">Delete</a></span><br />' + t[2] + '</div>'
    else:
        content += '<p><i>No posts by this IP found!</i></p>'
    db.close()
    content += footer
    return content

# Promote admin form
# Only admins and owners have this ability
# The Owner cannot be demoted
@route('/admin/promote')
def promotion_form():
    global header, footer, session
    session.start()
    if not(session.get('username')) or session.get('rank') < 2:
        redirect('/admin')
    return header + '''<div style="text-align: center;">
<h1>Promote a Mod</h1>
<form method="post" action="/admin/promote">
<table style="margin: auto;">
<tr><td><label for="username">Username:</label></td><td><input type="text" name="username" id="username" /></td></tr>
<tr><td>New Rank:</td><td><input type="radio" name="rank" value="0" id="delete" /><label for="delete">Delete Account</label><input type="radio" name="rank" value="1" id="mod" /><label for="mod">Moderator</label><input type="radio" name="rank" value="2" id="admin" /><label for="admin">Admin</label></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Change Rank" /></td></tr>
</table>
</form>
</div>''' + footer

# Promote admin handler
@route('/admin/promote', method='POST')
def promote():
    global connect, session
    session.start()
    if not(session.get('username')) or session.get('rank') < 2:
        redirect('/admin')
    username = request.forms.get('username')
    rank = int(request.forms.get('rank'))
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT rank FROM mods WHERE usern=%s;", (username,))
    if int(c.rowcount):
        if int(c.fetchone()[0]) == 3:
            redirect('/admin/promote')
    if not(rank):
        c.execute("DELETE FROM mods WHERE usern=%s;", (username,))
    else:
        c.execute("UPDATE mods SET rank=%s WHERE usern=%s;", (rank, username))
    db.commit()
    db.close()
    redirect('/admin/')

# View a list of all admin accounts
# Verify if the admin was really promoted, etc.
@route('/admin/accounts')
def view_accounts():
    global connect, header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    content = header + '''<h1>Admin Accounts</h1>
<hr />
<table>'''
    ranks = ['Inactive', 'Moderator', 'Administrator', 'Awesome Owner']
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT usern, rank FROM mods;")
    if int(c.rowcount):
        for i in range(int(c.rowcount)):
            t = c.fetchone()
            content += '<tr><td>' + t[0] + '</td><td><i>' + ranks[int(t[1])] + '</i></td></tr>'
    db.close()
    content += '</table>' + footer
    return content

# First time admin registration form handler
# Come here from '/admin' after you fill out the form to register for the first time
@route('/admin/registerfirst', method='POST')
def register_first():
    global connect, session
    username = request.forms.get('username')
    password = new('sha512', request.forms.get('password')).hexdigest()
    confirm = new('sha512', request.forms.get('confirm')).hexdigest()
    if password != confirm:
        redirect('/admin/register')
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT id FROM mods;")
    if int(c.rowcount):
        redirect('/admin')
    c.execute("INSERT INTO mods (id, usern, passw, ip, last_login, rank) VALUES (0, %s, %s, '0.0.0.0', NOW(), 3);", (username, password))
    db.commit()
    db.close()
    redirect('/admin')

# View, ban, unban IPs
# Gives you a reminder about why the person was banned
# A person with a banned IP will no longer be able to post
@route('/admin/bans')
def ip_bans():
    global connect, header, footer, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    content = header + '''<h1>Banned IPs</h1>
<hr />
<table>'''
    db = eval(connect)
    c = db.cursor()
    c.execute("SELECT * FROM bans;")
    if int(c.rowcount):
        for i in range(int(c.rowcount)):
            t = c.fetchone()
            content += '<tr><td>' + t[1] + '</td><td><i>' + t[2] + '</i></td><td><a href="/admin/unban/' + str(t[0]) + '">Unban</a></td></tr>'
    db.close()
    content += '''</table>
<form method="post" action="/admin/bans">
<table>
<tr><td><label for="ip">IP:</label></td><td><input type="text" name="ip" id="ip" size="39" maxlength="39" /></td></tr>
<tr><td><label for="reason">Reason:</label></td><td><input type="text" name="reason" id="ip" size="100" maxlength="100" /></td></tr>
<tr><td>&nbsp;</td><td><input type="submit" value="Ban" /></td></tr>
</table>
</form>''' + footer
    return content

# Processes a new ban
@route('/admin/bans', method='POST')
def ban_ip():
    global connect, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    ip = request.forms.get('ip')
    reason = request.forms.get('reason')
    db = eval(connect)
    c = db.cursor()
    c.execute("INSERT INTO bans (id, ip, reason) VALUES (0, %s, %s);", (ip, reason))
    db.commit()
    db.close()
    redirect('/admin/bans')

# Processes an unban
@route('/admin/unban/<entry:int>')
def unban_ip(entry):
    global connect, session
    session.start()
    if not(session.get('username')):
        redirect('/admin')
    db = eval(connect)
    c = db.cursor()
    c.execute("DELETE FROM bans WHERE id=%s;", (entry,))
    db.commit()
    db.close()
    redirect('/admin/bans')

run(host=site_host, port=80)
# Uncomment the next line and the Paste import function at the beginning of the file, and comment out the line above this to switch to a production server using Paste
# httpserver.serve(bottle.default_app(), host=site_host, port=80)
