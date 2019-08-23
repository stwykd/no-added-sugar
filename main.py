import webapp2
import cgi

home = '''
<form method="get">
    <input name="q">
    <input type="submit">
</form>
'''
signup = '''
Signup
<form method="get" action="/welcome">
    <label>Username<input name="username" type="text"></label><br>
    <label>Password<input name="password" type="password"></label><br>
    <label>Password<input name="pass-verify" type="password"></label><br>
    <label>Email<input name="email" type="email"></label><br>
    <input type="submit">
</form>
'''
welcome = '''
Welcome %s!
'''


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(home)


class SignupPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(signup)


class WelcomePage(webapp2.RedirectHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write(welcome % self.request.get("username"))


app = webapp2.WSGIApplication([('/', MainPage), ('/signup', SignupPage), ('/welcome', WelcomePage)], debug=True)
