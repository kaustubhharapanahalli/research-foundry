"""The user model.

Django's own ``User``, as a model this project owns. Adding a field later
is an ordinary migration; switching to a custom model after the first
migration is not, which is why it exists from the start.
"""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """A person who signs in."""
