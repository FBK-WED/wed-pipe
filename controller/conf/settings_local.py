# Django local settings.
# copy in /etc/ and symlink somewhere reachable

ADMINS = (
    ('admin', 'admin@example.org'),
)

MANAGERS = ADMINS

DATABASES = {
    'default' : {
        'ENGINE'   : 'django.db.backends.postgresql_psycopg2',
        'NAME'     : 'controller',
        'USER'     : 'controller',
        'PASSWORD' : 'changeme',
        'HOST'     : 'localhost',
        'PORT'     : '5432'
    }
}

TIME_ZONE = 'Europe/Rome'
LANGUAGE_CODE = 'en-us'

# where to log
_log_path = '/var/log/controller/controller.log'

