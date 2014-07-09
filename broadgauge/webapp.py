import web
import json

from . import account
from . import oauth
from . import forms
from .models import Trainer, User, Organization
from .template import render_template, context_processor
from .flash import flash_processor, flash, get_flashed_messages

#web.config.debug = False

urls = (
    "/", "home",
    "/logout", "logout",
    "/login", "login",
    "/dashboard", "dashboard",
    "/trainers/signup", "trainer_signup",
    "/settings/profile", "edit_trainer_profile",
    "(/trainers/signup|/orgs/signup|/login)/reset", "signup_reset",
    "(/trainers/signup|/orgs/signup|/login)/(github|google)", "signup_redirect",
    "/oauth/(github|google)", "oauth_callback",
    "/orgs/signup", "org_signup",
    "/orgs/(\d+)", "org_view",
    "/orgs", "org_list",
    "/trainers", "trainers_list",
    "/trainers/(\d+)", "trainer_view",
)
app = web.application(urls, globals())
app.add_processor(flash_processor)

@context_processor
def inject_user():
    user_email = account.get_current_user()
    # User could be either a trainer or org admin
    # The current DB schema is not flexible enough to handle that.
    # TODO: Fix the schema
    user = user_email and User.find(email=user_email)
    return {
        'user': user,
        'site_title': web.config.get('site_title', 'Broad Gauge'),
        'get_flashed_messages': get_flashed_messages
    }

class home:
    def GET(self):
        email = account.get_current_user()
        user = User.find(email=email)
        if user:
            raise web.seeother("/dashboard")
        else:
            return render_template("home.html")

class dashboard:
    def GET(self):
        user = account.get_current_user()
        if not user:
            raise web.seeother("/")
        return render_template("dashboard.html")

class logout:
    def POST(self):
        account.logout()
        referer = web.ctx.env.get('HTTP_REFERER', '/')
        raise web.seeother(referer)

class oauth_callback:
    def GET(self, service):
        i = web.input(code=None, state="/")
        if i.code:
            redirect_uri = get_oauth_redirect_url(service)
            client = oauth.oauth_service(service, redirect_uri)
            userdata = client.get_userdata(i.code)
            if userdata:
                # login or signup
                t = Trainer.find(email=userdata['email'])
                if t:
                    account.set_login_cookie(t.email)
                    raise web.seeother("/dashboard")
                else:
                    web.setcookie("oauth", json.dumps(userdata))
                    raise web.seeother(i.state)

        flash("Authorization failed, please try again.", category="error")
        raise web.seeother(i.state)


def get_oauth_data():
    userdata_json = web.cookies().get('oauth')
    if userdata_json:
        try:
            return json.loads(userdata_json)
        except ValueError:
            pass

class login:
    def GET(self):
        userdata = get_oauth_data()
        if userdata:
            user = User.find(email=userdata['email'])
            if user:
                account.set_login_cookie(user.email)
                raise web.seeother("/dashboard")
            else:
                return render_template("login.html", userdata=userdata, error=True)
        else:
            return render_template("login.html", userdata=None)

class trainer_signup:
    FORM = forms.TrainerSignupForm
    TEMPLATE = "trainers/signup.html"

    def GET(self): 
        form = self.FORM()
        userdata = get_oauth_data()
        if userdata:
            # if already logged in, send him to dashboard
            user = self.find_user(email=userdata['email'])
            if user:
                account.set_login_cookie(user.email)
                raise web.seeother("/dashboard")

            form.name.value = userdata['name']
        return render_template(self.TEMPLATE, form=form, userdata=userdata)

    def POST(self):
        userdata = get_oauth_data()
        if not userdata:
            return self.GET()

        i = web.input()
        form = self.FORM(i)
        if not form.validate():
            return render_template(self.TEMPLATE, form=form)
        return self.signup(i, userdata)

    def signup(self, i, userdata):
        user = Trainer.new(
            name=i.name,
            email=userdata['email'],
            phone=i.phone,
            city=i.city,
            github=userdata.get('github'))
        account.set_login_cookie(user.email)
        raise web.seeother("/dashboard")

    def find_user(self, email):
        return Trainer.find(email=email)

class edit_trainer_profile:
    FORM = forms.TrainerEditProfileForm
    TEMPLATE = "trainers/edit-profile.html"
    def GET(self):
        form = self.FORM()
        email = account.get_current_user()
        user = User.find(email=email)
        trainer = Trainer.find(user_id = user.id)
        return render_template(self.TEMPLATE, form=form, user=user, trainer=trainer)

    def POST(self):
        email = account.get_current_user()
        user = User.find(email=email)
        trainer = Trainer.find(user_id = user.id)
        i = web.input()
        form = self.FORM(i)
        if not form.validate():
            return render_template(self.TEMPLATE, form=form, user=user, trainer=trainer)
        else:
            trainer.update(user.id, city=form.city.data, bio=form.bio.data, website=form.website.data)

        
class org_signup(trainer_signup):
    FORM = forms.OrganizationSignupForm
    TEMPLATE = "orgs/signup.html"

    def find_user(self, email):
        # We don't limit numer of org signups per person
        return None

    def signup(self, i, userdata):
        user = User.find(email=userdata['email']) or User.new(name=userdata['name'], email=userdata['email'])
        org = Organization.new(name=i.name, city=i.city, admin_user=user, role=i.role)
        account.set_login_cookie(user.email)
        raise web.seeother("/orgs/{}".format(org.id))

def get_oauth_redirect_url(provider):
    home = web.ctx.home
    if provider == 'google' and home == 'http://0.0.0.0:8080':
        # google doesn't like 0.0.0.0
        home = 'http://127.0.0.1:8080'
    return "{home}/oauth/{provider}".format(home=home, provider=provider)

class signup_redirect:
    def GET(self, base, provider):
        redirect_uri = get_oauth_redirect_url(provider)
        client = oauth.oauth_service(provider, redirect_uri)
        url = client.get_authorize_url(state=base)
        raise web.seeother(url)

class signup_reset:
    def GET(self, base):
        # TODO: This should be a POST request, not GET
        web.setcookie("oauth", "", expires=-1)
        raise web.seeother(base)

class org_list:
    def GET(self):
        orgs = Organization.findall()
        return render_template("orgs/index.html", orgs=orgs)

class org_view:
    def GET(self, id):
        org = Organization.find(id=id)
        if not org:
            raise web.notfound()
        return render_template("orgs/view.html", org=org)

class trainers_list:
    def GET(self):
        trainers = Trainer.findall()
        return render_template("trainers/index.html", trainers=trainers)

class trainer_view:
    def GET(self, id):
        trainer = Trainer.find(user_id=id)
        if not trainer:
            raise web.notfound()
        return render_template("trainers/view.html", trainer=trainer)
