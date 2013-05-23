# Django local settings.
# copy in /etc/ and symlink somewhere reachable

ADMINS = (
    ('Marco Amadori', 'amadori@fbk.eu'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql_psycopg2',
        'NAME'    : 'controller',
        'USER'    : 'controller',
        'PASSWORD': 'changeme',
        'HOST'    : 'localhost',
        'PORT'    : '5432'
    }
}

TIME_ZONE = 'Europe/Rome'
LANGUAGE_CODE = 'en-us'

# where to log
_log_path = '/var/log/controller/controller.log'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'put_a_good_key_here*******************************'

#REFINE_EXTERNAL_HOST = 'localhost'
#REFINE_EXTERNAL_PORT = '3333'

#SCRAPERWIKI_APP             = 'http://vpn.venturi.fbk.eu'
#REFINE_RDF_MAPPING_BASE_URI = 'http://data.venturi.fbk.eu/'
