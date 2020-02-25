# coding=utf-8
import os
import webapp2
import jinja2

from google.appengine.ext import db

templ_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templ_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(jinja_env.get_template(template).render(kw))


class MainPage(Handler):
    def render_front(self, title="", msg="", err=""):
        self.render("front.html", title=title, message=msg, error=err)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        message = self.request.get("message")

        if title and message:
            self.write("post submitted. yas! 🔥✌️")
        else:
            self.render_front(title, message, "both a title and a message are required!")


app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
