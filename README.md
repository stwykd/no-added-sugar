# no added sugar

no-added-sugar is a blog built for fun.

It is live at https://no-added-sugar.appspot.com

Users can sign up https://no-added-sugar.appspot.com/signup, login https://no-added-sugar.appspot.com/login, and submit blog posts https://no-added-sugar.appspot.com/blog/submit.

The frontend is simply HTML+CSS, and it is dynamically generated using jinja2 templates.

It exposes JSON API through at endpoints `blog.json` to fetch the main page, and `blog/(post_id).json` to fetch the post with id `post_id`.

It is built using Google App Engine. It uses Google Datastore to store users and blogposts and memcache to cache static content and least recent DB queries made.
Most of the code is hacked inside blog.py. hashing.py contains utilities for password hasing (using a salt) and cookie hashing (using a secret).
