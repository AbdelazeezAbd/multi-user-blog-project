# impot webqpp2 library
import webapp2
# import time module
import time
# import all from models folder
from models import *
# import all from utility file
from utility import *

# BlogHandler class is the administrator


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        kw['user'] = self.user
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

# this class redirect you to the main page that contains all posts


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.redirect('/blog')

# this class render to front.html file that is in templates folder


class BlogFront(BlogHandler):
    def get(self):
        posts = Post.by_limit(10)
        self.render("front.html", posts=posts)

# this class was created to be the page that contains the post


class PostPage(BlogHandler):
    @post_exists
    def get(self, post):
        liked = self.user and self.user.user_likes.filter(
            "post =", post).count() > 0
        comments = post.post_comments.order('-created')
        self.render(
            "permalink.html",
            post=post, user=self.user, liked=liked, comments=comments)

# this class to enable the users to like the posts
# the user cannot like the post more than once and cannot like his post
# and cannot like if he is logged of


class LikeBtn(BlogHandler):
    @user_logged_in
    @post_exists
    def post(self, post):
        like_btn = self.request.get('like-btn')
        like = self.user.user_likes.filter("post =", post).get()
        if like_btn == 'like' and not like:
            like = Like.create(self.user, post)
            like.put()
        elif like_btn == 'unlike' and like:
            like.delete()
        time.sleep(0.1)
        self.redirect('/blog/' + str(post.key().id()))

# this class to enable the users to comment on the posts
# logged of users cannot comment


class NewComment(BlogHandler):
    @user_logged_in
    @post_exists
    def get(self, post):
        self.render('newcomment.html')

    @user_logged_in
    @post_exists
    def post(self, post):
        content = self.request.get('comment')
        if content:
            comment = Comment.create(content, self.user, post)
            comment.put()
            time.sleep(0.1)
            self.redirect('/blog/' + str(post.key().id()))
        else:
            error = "Complete content of comment, please!"
            self.render('newcomment.html', comment=content, error=error)

# this class to enable the user to edit his comment
# the user cannot edit other users comments


class EditComment(BlogHandler):
    @user_logged_in
    @comment_exists
    @user_owns_comment
    def get(self, post, comment):
        self.render(
            'editcomment.html',
            comment=comment.content, post_id=post.key().id())

    @user_logged_in
    @comment_exists
    @user_owns_comment
    def post(self, post, comment):
        content = self.request.get('comment')
        if content:
            comment.content = content
            comment.put()
            time.sleep(0.1)
            self.redirect('/blog/' + str(post.key().id()))
        else:
            error = "Complete content of comment, please!"
            self.render(
                'editcomment.html',
                comment=content, post_id=post.key().id(), error=error)

# this class to enable the user to delete his comment
# the user cannot delete other users comments


class DeleteComment(BlogHandler):
    @user_logged_in
    @comment_exists
    @user_owns_comment
    def post(self, post, comment):
        comment.delete()
        time.sleep(0.1)
        self.redirect('/blog/' + str(post.key().id()))

# this class to enable the users to post in the blog
# logged of users cannot post


class NewPost(BlogHandler):
    @user_logged_in
    def get(self):
        self.render("newpost.html")

    @user_logged_in
    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        if subject and content:
            post = Post.create(subject, content, self.user)
            post.put()
            self.redirect('/blog/' + str(post.key().id()))
        else:
            error = "Complete subject or content, please!"
            self.render(
                "newpost.html", subject=subject,
                content=content, error=error, user=self.user)

# this class to enable the users to edit his posts
# logged of users cannot edit and the user cannot edit others posts


class EditPost(BlogHandler):
    @user_logged_in
    @post_exists
    @user_owns_post
    def get(self, post):
        self.render(
            "editpost.html", subject=post.subject,
            content=post.content, post_id=post.key().id())

    @user_logged_in
    @post_exists
    @user_owns_post
    def post(self, post):
        subject = self.request.get('subject')
        content = self.request.get('content')
        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/' + str(post.key().id()))
        else:
            error = "Complete subject or content, please!"
            self.render(
                "editpost.html", subject=subject, content=content,
                post_id=post.key().id(), error=error)


# this class to enable the users to delete his posts
# logged of users cannot delete and the user cannot delete others posts


class DeletePost(BlogHandler):
    @user_logged_in
    @post_exists
    @user_owns_post
    def post(self, post):
        post.delete()
        time.sleep(0.1)
        self.redirect('/blog')

# this class for who want to register in the website


class Signup(BlogHandler):
    def get(self):
        self.render("signup.html")

    def post(self):
        self.username = self.request.get("username")
        self.password = self.request.get("password")
        self.verify = self.request.get("verify")
        self.email = self.request.get("email")

        params = dict(username=self.username, email=self.email)
        passed = True
        if not valid_username(self.username):
            params["error_username"] = "Invalid username!"
            passed = False
        else:
            user = User.by_name(self.username)
            if user:
                params["error_username"] = "User already exists!"
                passed = False
        if not valid_password(self.password):
            params["error_password"] = "Invalid password!"
            passed = False
        elif self.password != self.verify:
            params["error_verify"] = "Two passwords not same!"
            passed = False
        if self.email and not valid_email(self.email):
            params["error_email"] = "Invalid email!"
            passed = False

        if passed:
            user = User.register(self.username, self.password, self.email)
            user.put()
            self.login(user)
            self.redirect('/welcome')
        else:
            self.render("signup.html", **params)

# if user successfully register this class will
# redirect him to the welcome page
# else the user will recieve error message


class Welcome(BlogHandler):
    def get(self):
        if self.user:
            username = self.user.name
            self.render("welcome.html", username=username)
        else:
            self.redirect('/signup')

# the users who registered can log in to their accounts


class Login(BlogHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        user = User.login(username, password)
        if user:
            self.login(user)
            self.redirect('/welcome')
        else:
            self.render(
                "login.html", error="Username and password don't match!")

# if user want to log out from his account this class for this


class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

# now we store all the previous functions with the different paths
app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/([0-9]+)/like', LikeBtn),
                               ('/blog/([0-9]+)/comment/newcomment',
                               NewComment),
                               ('/blog/([0-9]+)/comment/([0-9]+)/delete',
                               DeleteComment),
                               ('/blog/([0-9]+)/comment/([0-9]+)/edit',
                               EditComment),
                               ('/blog/newpost', NewPost),
                               ('/blog/([0-9]+)/edit', EditPost),
                               ('/blog/([0-9]+)/delete', DeletePost),
                               ('/signup', Signup),
                               ('/welcome', Welcome),
                               ('/login', Login),
                               ('/logout', Logout),
                               ],
                              debug=True)
