# coding=utf-8
import os

import jinja2
import webapp2
from google.appengine.ext import db


class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    message = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


templ_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templ_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(jinja_env.get_template(template).render(kw))


class MainPage(Handler):
    def get(self):
        self.redirect('/blog')


class BlogPage(Handler):
    def render_blog(self):
        posts = db.GqlQuery("select * from BlogPost order by created desc")
        self.render("blog.html", posts=posts)

    def get(self):
        self.render_blog()


class SubmitPage(Handler):
    def render_submit(self, title="", msg="", err=""):
        posts = db.GqlQuery("select * from BlogPost order by created desc")
        self.render("submit.html", title=title, message=msg, error=err, posts=posts)

    def get(self):
        self.render_submit()

    def post(self):
        title = self.request.get("title")
        message = self.request.get("message")

        if title and message:
            b = BlogPost(title=title, message=message)
            b.put()
            self.write('post submitted. yas! 🔥✌️<br><a href="/blog">back to home</a>')
        else:
            self.render_submit(title, message, "both a title and a message are required!")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog', BlogPage),
    ('/blog/submit', SubmitPage),
], debug=True)
