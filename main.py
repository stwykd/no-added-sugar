# coding=utf-8
import os
import time

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

class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    message = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class FrontPage(Handler):
    def render_front(self, title="", msg="", err=""):
        posts = db.GqlQuery("select * from BlogPost order by created desc")
        self.render("front.html", title=title, message=msg, error=err, posts=posts)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        message = self.request.get("message")

        if title and message:
            b = BlogPost(title=title, message=message)
            b.put()
            self.write('post submitted. yas! 🔥✌️<br><a href="/">back to front page</a>')
        else:
            self.render_front(title, message, "both a title and a message are required!")


app = webapp2.WSGIApplication([('/', FrontPage)], debug=True)
