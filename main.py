# coding=utf-8
import os
import re

import jinja2
import webapp2
from google.appengine.ext import db

import hashing


class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    message = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def render(self):
        return jinja_env.get_template('post.html').render(p=self)

def users_key(group='default'):  # creates the ancestor element in the database to store all users
    return db.Key.from_path('users', group)
class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = hashing.make_pw_hash(name, pw)
        return cls(parent=users_key(), name=name, pw_hash=pw_hash, email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and hashing.valid_pw(name, pw, u.pw_hash):
            return u


templ_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templ_dir), autoescape=True)
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(jinja_env.get_template(template).render(kw))

    def set_cookie(self, name, val):
        cookie_val = hashing.make_hash(val)
        # Add `expire` to allow cookies to persist
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))

    def read_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and hashing.check_hash(cookie_val)

    def login(self, user):
        self.set_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):  # initialize() is called before every request
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


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
        if User.by_name(username):
            params['error_username'] = 'this user already exists'
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
            u = User.register(username, password, email)
            u.put()
            self.login(u)
            self.redirect('/welcome')


class WelcomePage(Handler):
    def get(self):
        if self.user:
            self.render('welcome.html', username=self.user.name)
        else:
            self.redirect('/signup')

class LoginPage(Handler):
    def get(self):
        if self.user:
            self.write('already logged in, yas! 🔥✌️<br><a href="/blog">back to home</a>')
        else:
            self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            self.render('login.html', error='invalid login')

class LogoutPage(Handler):
    def get(self):
        self.logout()
        self.write('logged out! ✌️<br><a href="/blog">back to home</a>')

class NotFoundPage(Handler):
    def get(self):
        self.error(404)
        self.render('404.html')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', SignupPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    ('/welcome', WelcomePage),
    ('/blog', BlogPage),
    ('/blog/submit', SubmitPage),
    ('/blog/([0-9]+)', PostPage),
    ('/.*', NotFoundPage),
], debug=True)
