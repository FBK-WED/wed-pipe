from fabric.context_managers import lcd
from fabric.decorators import task
from fabric.operations import local, prompt

from fabfile.helpers import say


@task
def compass_compile():
    with say('Local: compiling css'):
        with lcd('./webui/scss'):
            local('compass clean && compass compile')


@task
def reset_db():
    with say('Local: resetting DB'):
        local('python manage.py reset_db --router=default --noinput')
        local('python manage.py syncdb --migrate --noinput')


@task
def loaddata():
    with say('Local: loading data'):
        local('python manage.py loaddevdata')


@task
def makemessages():
    """ Update *.po in the LOCAL repository
    """
    for opts in ["-e html -e email -e txt",
                 "-d djangojs -i '*CACHE*'"]:
        local(
            'python ./manage.py makemessages {0} -l it'.format(opts)
        )


@task
def compilemessages():
    """ Compile translations, building *.mo from *.po files
    """
    local('python manage.py compilemessages')


@task
def silk_download():
    """ download silk single machine locally
    """
    import os
    from os.path import expanduser

    out_name = 'silk.jar'
    lib_zip_name = 'silk-lib.zip'
    url = 'https://dl.dropbox.com/s/e6d6c4u15xvo2q7/silk.jar'
    lib_url = 'https://dl.dropbox.com/s/ngwjkxv284osxb3/silk-lib.zip'
    out_dir = 'data_acquisition/silk/'
    with lcd(out_dir):
        # we still need to  use path.join here, 'cause "lcd" doesn't work
        if not os.path.isfile(os.path.join(out_dir, out_name)):
            local('curl -L "{}" -o "{}"'.format(url, out_name))
        if not os.path.isdir(os.path.join(out_dir, "lib")):
            local('curl -L "{}" -o "{}"'.format(lib_url, lib_zip_name))
            local('unzip {}'.format(lib_zip_name))
            local('rm {}'.format(lib_zip_name))

    plugin_name = 'VenturiTitanDataSource.jar'
    plugin_url = 'https://dl.dropbox.com/s/df6kwv037ecne47/' \
                 'VenturiTitanDataSource.jar'
    homedir = expanduser("~")
    silk_plugins = os.path.join(homedir, '.silk', 'plugins')

    if not os.path.isfile(os.path.join(silk_plugins, plugin_name)):
        res = prompt(
            "Now I'm gonna download the SD-silk plugin and place it in "
            "the Silk plugins directory, which is in your home directory ({})"
            ".\nThis operation should be performed by the user actually "
            "executing silk during the workflow, are you sure you want to "
            "continue? [y/n]".format(silk_plugins), validate='[yYnN]')

        if res.lower() == 'y':
            local('mkdir -p {}'.format(silk_plugins))
            finalname = os.path.join(silk_plugins, plugin_name)
            local('curl -L "{}" -o "{}"'.format(plugin_url, finalname))


@task
def install_virtuoso_extensions():
    """ execute the management command install_virtuoso_extensions
    """
    local('python ./manage.py install_virtuoso_extensions')


@task
def setup():
    setup_no_css()
    compass_compile()


@task
def setup_no_css():
    reset_db()
    loaddata()
    # compilemessages()
