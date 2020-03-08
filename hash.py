import hmac
import random
import string
import hashlib

secret = 'hashsecretly!'  # don't publish `secret`

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()  # use bcrypt instead
    return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split('|')[1]
    return h == make_pw_hash(name, pw, salt)

def hash_str(s):
    return hmac.new(secret, s).hexdigest()

def make_hash(val):
    return "%s|%s" % (val, hash_str(val))

def check_hash(s):
    cookie = s.split('|')[0]
    if cookie == make_hash(s):
        return cookie
