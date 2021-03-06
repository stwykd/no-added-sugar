# coding=utf-8
import json
import os
import re
from datetime import datetime

import jinja2
import webapp2
from google.appengine.api import memcache
from google.appengine.ext import db

import hashing

templ_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templ_dir), autoescape=True)

class BlogPost(db.Model):
    title = db.StringProperty(required=True)
    message = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

    def render(self):
        return jinja_env.get_template('post.html').render(p=self, id=str(self.key().id()))

    def as_dict(self):
        return {'title': self.title, 'message': self.message, 'created': self.created.strftime('%c')}

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
        return cls.all().filter('name =', name).get()

    @classmethod
    def register(cls, name, pw, email=None):
        return cls(parent=users_key(), name=name, pw_hash=hashing.make_pw_hash(name, pw), email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and hashing.valid_pw(name, pw, u.pw_hash):
            return u

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        kw['user'] = self.user
        self.write(jinja_env.get_template(template).render(kw))

    def render_json(self, v):
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json.dumps(v))

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

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'


class MainPage(Handler):
    def get(self):
        self.redirect('/blog')


class BlogPage(Handler):
    def get(self):
        posts, age = get_posts()
        if self.format == 'html':
            self.render("blog.html", posts=posts, age=age_str(age))
        else:
            return self.render_json([post.as_dict() for post in posts])

class SubmitPage(Handler):
    def render_submit(self, title="", msg="", err=""):
        posts = list(db.GqlQuery("select * from BlogPost order by created desc"))
        self.render("submit.html", title=title, message=msg, error=err, posts=posts)

    def get(self):
        self.render_submit()

    def post(self):
        title = self.request.get("title")
        message = self.request.get("message")

        if title and message:
            bp = BlogPost(title=title, message=message)
            bp.put()
            self.redirect('%s' % str(bp.key().id()))
        else:
            self.render_submit(title, message, "both a title and a message are required!")


class PostPage(Handler):
    def get(self, post_id):
        post_key = 'POST_'+post_id
        post, age = memcache_get_age(post_key)
        if not post:
            key = db.Key.from_path('BlogPost', int(post_id))
            post = db.get(key)
            memcache_set_age(post_key, post)
            age = 0
        if not post:
            self.error(404)
            return
        if self.format == 'html':
            self.render("permalink.html", post=post, age=age_str(age))
        else:
            self.render_json(post.as_dict())

class SignupPage(Handler):  # users registering the same username at the same time. use memcache for locking
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASS_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

    def valid_username(self, username):
        return username and self.USER_RE.match(username)

    def valid_password(self, password):
        return password and self.PASS_RE.match(password)

    def valid_email(self, email):
        return not email or self.EMAIL_RE.match(email)

    def get(self):
        if self.user:
            self.render('loggedin.html')
        else:
            self.render("signup.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        have_error = False
        params = dict(username=username, email=email)
        if not self.valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        if User.by_name(username):
            params['error_username'] = 'This user already exists'
            have_error = True
        if not self.valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        if not self.valid_email(email):
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
            self.render('welcome.html')
        else:
            self.redirect('/signup')

class LoginPage(Handler):
    def get(self):
        if self.user:
            self.render('loggedin.html')
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
        self.render('loggedout.html')

class NotFoundPage(Handler):
    def get(self):
        self.error(404)
        self.render('404.html')


def memcache_set_age(key, val):  # sets the val with the current datetime in memcache
    memcache.set(key, (val, datetime.utcnow()))

def memcache_get_age(key):  # gets the value and the datetime of when the value was stored from memcache
    r = memcache.get(key)
    if r:
        val, save_time = r
        age = (datetime.utcnow()-save_time).total_seconds()
    else:
        val, age = None, 0
    return val, age

def add_post(ip, post):
    post.put()
    get_posts(update=True)
    return str(post.key().id())


def get_posts(update=False):
    q = BlogPost.all().order('-created').fetch(limit=10)
    mc_key = 'POSTS'
    posts, age = memcache_get_age(mc_key)
    if update or posts is None:
        posts = list(q)
        memcache_set_age(mc_key, posts)
    return posts, age

def age_str(age):
    s = 'db query %s seconds ago'
    age = int(age)
    if age == 1:
        s.replace('seconds', 'second')
    return s % age


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup/?', SignupPage),
    ('/login/?', LoginPage),
    ('/logout/?', LogoutPage),
    ('/welcome/?', WelcomePage),
    ('/blog(?:\\.json)?/?', BlogPage),
    ('/blog/submit/?', SubmitPage),
    ('/blog/([0-9]+)(?:\\.json)?/?', PostPage),
    ('/.*', NotFoundPage),
], debug=True)
