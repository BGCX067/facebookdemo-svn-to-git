import random
import re
import urllib
import gminifb

import cgi
import os
import string
import time
import logging

import wsgiref.handlers

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp

##################################################
# Complete code listing for "Hello MiniFB.py"
#
#

##################################################
# make sure to rename this file to "hello.py" after
# downloading it... it should NOT be named "hello.py.txt"
##################################################



##################################################
# "License" for this file.
#
# -----------------------------------
# [1] Let the code be free and unrestricted
#
# You are free to use this code (i.e the code for "Hello MiniFB.py") in your
# own projects in any way you choose, copy it or whatever without restrictions
# for free.  You don't have to mention Hello MiniFB or name your first
# born child "powered by Hello MiniFB" or anything. It is provided to help 
# you learn how to make Facebook Apps using python/minifb.
#
# -----------------------------------
# [2] One exception.  Don't be lame and rip me off
#
# The one exception is that you can NOT without my permission 
# redistribute / publish the doc strings or comments in this code
# If you're using this tutorial to learn/develop your own applications this 
# exception doesn't really apply to you since the doc strings and comments
# don't get served to your users anyways and just remain in your code.
#
# The reason for this restriction is to to keep people from copying / creating 
# another identical minifb / clone tutorial by simply copying my work.  If you'd 
# like to work with me to improve this tutorial that would be cool.  I'd like 
# do whatever we can to make it as helpful as I can even if that means 
# openning this up somehow for more people to contribute please contact me
# with how you think this should be done.  
#
# Basically, I'd be bummed if after I spent my time trying to help people, 
# someone just copied all my work and created "Hello MiniFB.py Clone" app. 
# That is why the doc strings and comments are protected under this section.
#
# -----------------------------------
# [3] Mention "Hello MiniFB.py" if you are moved to do so.
#
# If Hello MiniFB.py has helped you, it would be nice if you mention in
# your apps somewhere/link to it and add your apps to:
#
# http://apps.facebook.com/hellominifb/viewapps
# 
# It would be really cool to know that the time I spent putting this
# together helped someone.  Also let me know if you find bugs or
# have suggestions about this license and for improvements.  This is
# the first code tutorial I've written so please send me feedback on it.
#
# Steven Chow
# steven@warfish.net




##################################################
#
# You will need to download and install in your sys.path:
#   1. minifb v1.1
#   2. simplejson
#
# Organization of this file.  There are basically four sections of this file
#
# [1] app settings - These are 5 critical settings that you must set before
#	 this application will work.  
#
# [2] minifb helper functions - These are just wrappers to the actual minifb.py
#	 function calls to make them a little easier to use.
#
# [3] some utility functions - These are just some util functions like _genHeader
#	 that the actual url handlers rely on
#
# [4] url handlers - The actual functions that do the real work.



##################################################
# [1] app settings


_FbApiKey = ""
_FbSecret = gminifb.FacebookSecret("")
_canvas_url = "http://apps.facebook.com/hellominifbae"
_app_name = "Hello MiniFB.py in Appengine"
_userdb = "hellominifb.txt" # must be a file writable by the webserver

_google_analytics_id = None  # optional setting



##################################################
# [2] minifb helper functions

# General note about these wrappers.  The minifb calls
# will throw exceptions when there is an error returned
# from Facebook.  What I usually do is wrap all non-essential
# minifb calls in a catch all try: except: block so that
# if it fails it does not stop the user's process and
# since that particular code is "non-essential" it os ok.
# publisActionToUser is a good example of that.
#
#def _getSignedValues(cgiargs):
#	"""Validate signed cgi values using the minifb.validate call
#
#	_getSignedValues is a simple wrapper for validate that ensures that
#	only signed values are returned rather than a mix if unsigned and
#	signed values
#	"""
#	sig = "fb_sig" # signature prefix
#	return gminifb.validate(_FbSecret, dict([(k,v) for k,v in dict(cgiargs).items() if k[:len(sig)] == sig]))


def _getAppFriends(session_key):
	"""Retrieve friends of the logged in user who have installed this app """
	usersInfo = gminifb.call("facebook.friends.getAppUsers",
							_FbApiKey, _FbSecret,
							session_key=session_key)
	return usersInfo


def _sendNotification(session_key, note, toIdList):
	"""Send a basic facebook notification to one or more users

	Watch out for the return value of this function.  If retInfo
	is a URL, i.e. retInfo[:4] == "http" you will need to redirect
	the user's browser to it for the user to manually confirm the
	sending of these notifications.  You can provide a &next= parameter
	to the url which the user will be sent to after the confirmation.
	If retInfo is not a url the notifications will be sent without
	manual confirmation.

	Notifications can also include an email component check the
	Facebook wiki for more information on this.
	"""
	retInfo = gminifb.call("facebook.notifications.send",
							_FbApiKey, _FbSecret,
							session_key=session_key,
							notification=note,
							to_ids="%s" % ",".join(["%s" % i for i in toIdList]) )
	return retInfo

def _publishUserAction(session_key, note):
	gminifb.call("facebook.feed.publishActionOfUser",
				_FbApiKey, _FbSecret,
				session_key=session_key,
				title=note)

def _getFriends(session_key):
	usersInfo = [int(i) for i in gminifb.call("facebook.friends.get",
											 _FbApiKey, _FbSecret,
											 session_key=session_key)] 
	return usersInfo

def _sendRequest(session_key, toIdList, content, appname = "hellominifb",
				 image = "http://keepnix.com/images/firestorms_trans_big.gif"):
	retInfo = gminifb.call("facebook.notifications.sendRequest",
							_FbApiKey, _FbSecret,
							session_key=data['minifb.validate']['session_key'],
							to_ids = ",".join(["%s" % j for j in toIdList]),
							type = appname,
							content = content,
							image = image,
							invite = "0") 
	return retInfo

def _setProfileFBML(session_key, fbml):
	gminifb.call("facebook.profile.setFBML",
				_FbApiKey, _FbSecret, session_key=session_key,
				markup=fbml)


def _getUsersInfo(session_key, uidList):
	# Lookup username and details

	usersInfo = gminifb.call("facebook.users.getInfo",
							_FbApiKey, _FbSecret, session_key=session_key,
							fields="name,pic_square",
							uids=",".join(["%s" % j for j in uidList])) # uids can be comma separated list
	
	return usersInfo

def _getSessionKeyFromAuthToken(auth_token):
	"""Get the session key from the auth_token

	For certain apis such as postadd and postremove instead of being given
	the standard signed values we are given the auth_token which we are
	to use to get the session key using a call to getSession
	"""
	
	result = gminifb.call("facebook.auth.getSession",
						 _FbApiKey, _FbSecret, auth_token=auth_token)
	uid = result["uid"]
	session_key = result["session_key"]

	return (session_key, uid)




##################################################
# [3] some utility functions

def _genDumpHashHtml(d, title):
	output = "<h2>%s</h2>" % title
	for (k, v) in d.items(): output += "%s = %s<br>" % (k,v)
	return output



def _genHeader(page, added= False):
	tabslist = [ ("Home","."),
				 ("View Users","viewusers"),
				 ("View Apps","viewapps"),
				 ("Dump Variables","dumpvars"),
				 ("Invite Friends","invitefriends"),
				 ("Help","help") ]

	output = """<fb:dashboard>"""
	for i in tabslist:
		if i[1] == "help": output += """<fb:help href="%s">%s</fb:help>""" % (i[1],i[0])
		else: output += """<fb:action href="%s">%s</fb:action>""" % (i[1],i[0])

	if added:
		output += """<fb:create-button href="http://keepnix.com/articles/hellominifb.html">%s</fb:create-button>""" % "View tutorial"
	else:
		output += """<fb:create-button href="http://www.facebook.com/add.php?api_key=%s">%s</fb:create-button>""" % (_FbApiKey, "Add Application")
	output += """</fb:dashboard>"""

	if _google_analytics_id != None:
		output += """<fb:google-analytics uacct="%s" page="%s" />""" % (_google_analytics_id, page)

	output += """<style> body {font-family: sans-serif;} .content { margin: 10px 10px 10px 10px; }</style>"""

	return output


def _readDatabase():
	"""Just a quicky working db as a placeholder for a real datastore that
	you might use like mysql.

	This way this app will function and be able to store data without
	us having to deal with the issue if depending on other libraries
	or dealing with the intracacies of setting up an RDBMS system"""
	
	try:
		f = open(_userdb,'r')
		data = [map(int,i.split(',')) for i in f.read().split('\n') if len(i) > 5]
		f.close()
	except:
		data = []
	return data


def _addUserToDatabase(uid):
	"""Just a quicky db as a placeholder for a real datastore that
	you might use like mysql"""

	userdb = dict(_readDatabase())

	if not userdb.has_key(int(uid)):
		f = open(_userdb,'a')
		import time
		f.write("%s,%s\n" % (uid,int(time.time())))
		f.close()

	return userdb


def _genFBComments(xid, title, added = False):
	if added: canpost = "true"
	else: canpost = "false"
	
	return """<fb:comments callbackurl="%s/addcomment?xid=%s" canpost="%s" candelete="false" xid="%s"><fb:title>%s</fb:title></fb:comments>""" % (_canvas_url, xid, canpost, xid, title)	



##################################################
# [4] url handlers
class MainController(webapp.RequestHandler):
	def get(self):
		logging.info('path:' + str(self.request.path) + ' params:' + str(self.request.params))
		path = string.lstrip(self.request.path,  '/hellominifb')
		path = string.strip(path, '/')
		path = string.replace(path, '/', '_')
		method = getattr(self, path, self.index)
		html = method(self.request)
		self.response.out.write(html)
	
	def post(self):
		self.get()

	def index(self, req):
		return """
		<html>
		<head>
		<style> body {font-family: sans-serif;} p { width: 480px; }</style>
		</head>
		<h1>%s Application</h1>
		<p class=ptext>
		This page is never actually accessed through Facebook UI.  It is provided just
		so that you can verify that your server's mod_python configuration is
		working and that "Hello MiniFB.py" can import minifb.py and simplejson.py
		properly.
		</p>
		<p class=ptext>
		If you're seeing this page is being displayed you can
		move on, since it looks like its working.
		</p>
		<p class=ptext>

		Now you can move onto <b>"Step 4. Set up your Facebook Application on Facebook.com"</b> using the Facebook <a href="http://www.facebook.com/developers">Developers Application</a>
		</p>
		<p class=ptext>
		<a href="http://keepnix.com/articles/hellominifb.html">View Hello MiniFB.py Tutorial</a><p>
		<a href="http://apps.facebook.com/hellominifb">View Hello MiniFB.py App</a>	
		</p>

		</html>
		""" % _app_name

		
	def callback(self, req):
		"""FBML Main Canvas page called when _canvas_url is viewed"""

		#signed = _getSignedValues(req.params)
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		#	redir = "http://www.facebook.com/add.php?api_key=%s&next=%%3fret%%3d%s" % (_FbApiKey, _canvas_url)
		#	return """<fb:redirect url="%s" />""" % redir

		output = ""
		output += _genHeader(page = "home", added = added)
		
		# Delete this line to remove the grey box messaging from your app
		output += """<P><div class="content" style="background: #dddddd; padding: 10px 10px 10px 10px;">This is an installed version of the tutorial code provided by <a href="http://apps.facebook.com/hellominifb">Hello MiniFB.py App</font></a> (view <a href="http://keepnix.com/articles/hellominifb.html"><font size=+1><b>Tutorial</b></font></a> or <a href="http://keepnix.com/articles/hello.py.txt"><font size=+1><b>Source Code</b></font></a>).  If you are not the developer who is working through the tutorial please visit the original <a href="http://apps.facebook.com/hellominifb"><font size=+1><b>Original Hello MiniFB.py App</b></font></a> for more info.</div><p><div class=content><h1>Welcome to %s</h1><p>This is a simple "Hello World" application written in Python (Apache2/mod_python) using minifb.py.  It was written to help provide a starting point for people to write their own Facebook applications using minifb/python and therefore contains code to demonstrate most of the APIs you will need.  I'm no expert but hopefully this code/tutorial will help you avoid some of the confusion I initially had.  <i>Note:</i> I did not write <a href="http://code.google.com/p/minifb/">minifb.py</a> nor am I affiliated with its authors.</p><p>All the <a href="http://keepnix.com/articles/hellominifb_code.html"><font size=+1><b>source code</b></font></a> for this actual application is available as well as a <a href="http://keepnix.com/articles/hellominifb.html"><font size=+1><b>tutorial</b></font></a>to help you get it setup. </p><p> Probably the best way to get started is to explore the features of this application (it is pretty basic) so that you are familiar with what you'll be seeing in the tutorial and in the code.  While viewing most of the app doesn't require you to install it, you may want to do so anyhow to see how it works.  Once you're familiar with the app you can follow the <a href="http://keepnix.com/articles/hellominifb.html"><b>tutorial</b></a> and use the code to create your own app. </p><p>Hello MiniFB.py is designed for folks who like to hit the ground running... you're basically spending a couple minutes copying Hello FiniFB.py into your own account and then spending the rest of your time adding your own functionality and you're done. </p>""" % _app_name

		# this fb:comments tag can be used to attach a message board to any "object" in
		# you application.  If you had icons or images you were displaying you can simply
		# have a message board attached to each by using your identifier for your icon
		# as the first parameter to this function, i.e. the xid


		output += "<p>"

		output += "<i>(you have to add this app before you will be able to write messages here)</i>"
		
		output += _genFBComments("home", "%s Testimonials/Comments" % _app_name, added)
		output += "</div>"
		return output

	# a back end call back url only for fb:comment
	def callback_addcomment(self, req, xid):
		data = {}

		signed = _getSignedValues(req.params)
		added = signed.get('added',"0") == "1"	

		if added:
			# comments callback
			if signed.has_key('xid_action') and signed['xid_action']:
				if signed['xid_action'] == 'post':
					# update your own data store if you want to keep track of the fact that a
					# comment was stored.  I used this just to store how many comments were left by each user
					# signed['user'] is contains the userid

					# post on this users mini-feed that the commented on this message board
					note = """%s <a href="%s">%s</a>""" % ("commented on", _canvas_url, _app_name)
					_publishUserAction(signed['session_key'], note)

					# you could also send a notification to all users who have commented on this
					# if you've been storing the list of users
					# to_ids = __not_implemented_get_all_comments_from_datastore
					#_sendNotification(signed['session_key'], note, to_ids)					
							   
				elif signed['xid_action'] == 'delete':

					# if you're maintaining a local datastore you can
					# maintain it here by removing or decrementing the appropriate values
					# when a comment is deleted
					pass

		if xid == "home": title = "%s Testimonials/Comments" % _app_name
		elif xid == "apps": title = "Applications based on/helped by Hello MiniFB.py"
		else: title = "Unknown"
				
		return _genFBComments(xid,title, added)
		


	def callback_viewusers(self, req, page = "0"):
		#signed = _getSignedValues(req.params)
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		userdata = _readDatabase()
		userdata.reverse()
		
		numusers = len(userdata)
		ppage = 50
		if numusers  < int(page) * ppage: page = "0"
		start = ppage * int(page)
		displayusers = userdata[start:start+ppage]
		next = False
		if numusers > (int(page) + 1) * ppage: next = True
		previous = False
		if int(page) > 0: previous = True

		output = _genHeader("users", added)

		output += "<div class=content>"
		output += "<h1>Users who have ever installed Hello MiniFB</h1>"

		output += "<table>"
		for ix, (uid,t) in enumerate(displayusers):
			if ix == 0: output += "<tr>"
			elif ix % 5 == 0: output += "</tr><tr>"
			output += """<td><fb:profile-pic size=thumb uid="%s" /><br><fb:name useyou="false" ifcantsee="(private)" uid="%s" /><br><fb:time t="%s" /></td>""" % (uid, uid, t)
			if ix == len(displayusers) - 1: output += "</tr>"
		output += "</table>"

		output += "<p>"
		if previous: output += """[<a href="viewusers?page=%s">%s</a>]""" % ( (int(page) - 1), "Previous")
		if next: output += """[<a href="viewusers?page=%s">%s</a>]""" % ( (int(page) + 1), "Next")
			

		output += "</div>"

		return output

	def callback_viewapps(self, req):
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		output = _genHeader("dumpvars",added)

		output += "<div class=content>"

		output += "<h1>Hello MiniFB.py Based Applications</h1>"
		output += "<p>"

		output += "If this tutorial / the Hello MiniFB.py code helped you get your application started or if your app is based on the Hello MiniFB.py code, please add it to this list and mention Hello MiniFB.py in your application somewhere (no need to blast your users with this fact, but plesae mention it somewhere).  It would be really cool to know that the time I spent putting this together helped someone."

		output += "<p>"

		output += "<i>(you have to add this app before you will be able to add your app here)</i>"

		output +=  _genFBComments("apps","Applications based on/helped by Hello MiniFB.py", added)

		output += "</div>"
		return output 
		


	def callback_dumpvars(self, req):
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		output = _genHeader("dumpvars",added)
		output += "<div class=content>"
		output += "<h1>A dump of all the variables</h1>"

		if added: output += "<i>(You currently have this app added)</i>"
		else: output += "<i>(You currently do NOT have this app added)</i>"
		output += "<p>"
		output += """This page is designed to get your oriented in terms of which values are being
		passed to your application and how minifb plays the role of validating the signed values"""
		output += "<p>"
		output += _genDumpHashHtml(dict(req.params), "Cgi Variables")
		output += "<p>"
		output += _genDumpHashHtml(signed, "Signed Variables")
		output += "</div>"

		return output


	def callback_invitefriends(self, req):
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		if not added:
			redir = "http://www.facebook.com/add.php?api_key=%s&next=%%3fret%%3d%s" % (_FbApiKey, "%s/invitefriends")
			return """<fb:redirect url="%s" />""" % redir		

		excludeIds = _getAppFriends(signed['session_key'])

		output = _genHeader("invitefriends", added = True)

		output += """<fb:request-form content='%s <fb:req-choice url="%s" label="%s" />' image=hello type="%s">""" % ("You have been invited to check out the %s application" % _app_name, _canvas_url, "View Application", "invitation")
		output += """<fb:multi-friend-selector exclude_ids="%s" max=20 actiontext="%s" />""" % (",".join(["%s" % x for x in excludeIds]),"Tell your friends who haven't heard about %s yet." % _app_name)
		output += "</fb:request-form>"	

		return output
		
		
			

	def callback_null(self, req):
		"""Called when your return from the multi-friend selector when the user clicks on skip this step """

		
		#Just redirect back to canvas page
		#
		#return """<fb:redirect url="%s" />""" % _canvas_url

		
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		output = _genHeader("skipstep", added)
		output += "<div class=content>"
		output += """<h1>Hello MiniFB: Invite Friends - Skip this step</h1><p>In my apps I just redirect this page to the main canvas page using a &lt;fb:redirect url="%s" /&gt; (see "def callbacknull" in the code), but in this tutorial it is included so that you can more easily see where "skip this step" ends up.<p><a href="%s">Back to canvas page</a>""" % (_canvas_url, _canvas_url)
		output += "</div>"
		return output

	def callback_help(self, req):
		signed = gminifb.validate(_FbSecret, self.request)

		added = signed.get('added',"0") == "1"	

		output = _genHeader("help", added)

		output += "<div class=content>"

		output += """
		<h1>Help Page</h1>
	<p>
	<b>[1]</b> Check out the <a href="http://keepnix.com/articles/hellominifb.html">Hello MiniFB Tutorial</a>
	<p>
	<b>[2]</b> Check out the <a href="http://www.facebook.com/apps/application.php?api_key=%s">Application Page / Message Boards</a> for Hello MiniFB.py
	<p>
	<b>[3]</b> If you found the %s app / tutorial helpful please <a href="http://www.facebook.com/inbox/?compose&id=716361400">let me know</a>.  I'd be happy to develop this tutorial further if it is helpful.

		""" % (_FbApiKey,_app_name)

		
		
		
		output += "</div>"
		return output
		

		
	def postadd(self, req, auth_token, ret = None):
		'''Facebook callback when user has added application
		gets an auth_token through post that must be converted
		into a session_key. Then lookup and send stuff to Facebook

		NOTE: this url can not contain FBML since it is accessed directly by the
		user's browser'''
		# Parse and validate posted values

		# Request session_key from auth_token instead of the regular
		# _getSignedValues.. postadd and postremove use the auth_token method
		(session_key, uid) =  _getSessionKeyFromAuthToken(auth_token)

		_addUserToDatabase(uid)		

		# these three lines are not used for anything and were actually
		# saved from a previous piece of sample code from minifb itself.
		# However you are not allowed to store these values according
		# to Facebook terms of service (only the UID)
		usersInfo = _getUsersInfo(session_key, [uid])
		name = usersInfo[0]["name"]
		photo = usersInfo[0]["pic_square"]
			

		# You may want to set the user's profile module FBML
		# with a call to.  This is just a silly demo.
		_setProfileFBML(session_key, "Hello from %s" % _app_name)

		#if ret == None: ret = _canvas_url
		#util.redirect(req, str(ret))

		return """<html><h1>Postadd called</h1>This page does not contain FBML notice that it is going to your webserver directly.  I use this url to perform some local data store updates (for example keeping track of how many users have added my app see "def postadd" in the code) and then just redirecting this back to the main canvas page.  However in Hello MiniFB.py I'm inserting this intermediate landing page to make the flow more clear.<p><a href="%s">Back to Canvas Page</a></html>""" % (_canvas_url,)


	def postremove(self, req):
		signed = gminifb.validate(_FbSecret, self.request)

		return """<html><h1>Postremove called</h1>This page does not contain FBML notice that it is going to your webserver directly.  I've been using this url to perform some data store updates and then just redirecting this back to the main canvas page<a href="%s">Back to Canvas Page</a></html>""" % _canvas_url	


def main():
	application = webapp.WSGIApplication([('/hellominifb.*', MainController)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()