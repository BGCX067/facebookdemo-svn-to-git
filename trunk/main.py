import cgi
import os
import string
import time
import wsgiref.handlers

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp

class MainController(webapp.RequestHandler):

	def get(self):
		template_values = { 'name' : 'test'}
		path = os.path.join(os.path.dirname(__file__), 'main.html')
		self.response.out.write(template.render(path, template_values))

def main():
	application = webapp.WSGIApplication([('/', MainController)])
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
