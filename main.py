# coding=utf-8
import os
import re

import jinja2
import webapp2
from google.appengine.ext import db


class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    message = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def render(self):
        return jinja_env.get_template('post.html').render(p=self)


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
            bp = BlogPost(title=title, message=message)
            bp.put()
            # self.write('post submitted. yas! 🔥✌️<br><a href="/blog">back to home</a>')
            self.redirect('%s' % str(bp.key().id()))
        else:
            self.render_submit(title, message, "both a title and a message are required!")


class PostPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path('BlogPost', int(post_id))
        post = db.get(key)

        if not post:
            self.error(404)
        else:
            self.render("permalink.html", post=post)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)


class SignupPage(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        have_error = False
        params = dict(username=username, email=email)
        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            self.redirect('/welcome?username=' + username)


class WelcomePage(Handler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username=username)
        else:
            self.redirect('/signup')


class NotFoundPage(Handler):
    def get(self):
        self.error(404)
        self.render('404.html')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', SignupPage), ('/signup/', SignupPage),
    ('/welcome', WelcomePage), ('/welcome/', SignupPage),
    ('/blog', BlogPage), ('/blog/', BlogPage),
    ('/blog/submit', SubmitPage), ('/blog/submit/', SubmitPage),
    ('/blog/([0-9]+)', PostPage), ('/blog/([0-9]+)/', PostPage),
    ('/.*', NotFoundPage),
], debug=True)
