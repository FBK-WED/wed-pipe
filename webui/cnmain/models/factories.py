""" factories for instantiating cnmain models, as well as django's
"""
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.utils.text import capfirst

import factory


class UserFactory(factory.Factory):
    """
    Factory for django.contrib.auth.models.User
    """
    FACTORY_FOR = User

    username = factory.Sequence('user{0}'.format)
    password = factory.lazy_attribute(lambda self: self.username)
    first_name = factory.lazy_attribute(lambda self: capfirst(self.username))
    last_name = 'Nasello'
    email = factory.lazy_attribute(
        lambda self: '{0}@example.com'.format(self.username)
    )

    @classmethod
    def _prepare(cls, create, **kwargs):
        kwargs['password'] = make_password(kwargs['password'])
        # pylint: disable=W0212
        return super(UserFactory, cls)._prepare(create, **kwargs)


class AdminFactory(UserFactory):
    """ Factory for an administrator
    """
    is_superuser = True
    is_staff = True

    username = 'admin'
    password = 'admin'
