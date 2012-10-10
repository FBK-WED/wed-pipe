# Django jenkins test settings.
# copy in /etc/ and symlink somewhere reachable

DATABASES = {
    'default' : {
        'ENGINE'   : 'django.db.backends.postgresql_psycopg2',
        'NAME'     : 'tomcat6',
        'USER'     : 'tomcat6',
        'PASSWORD' : 'tomcat6',
        'HOST'     : 'localhost',
        'PORT'     : '5432'
    }
}

