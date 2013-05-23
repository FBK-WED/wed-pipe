#!/bin/sh
# django application deploy script
# it deploys only new commits on master branch
# run this script as $APP (sudo -u ${APP} utils/deploy.sh)

PROGRAM="$(basename $0)"

if [ -n "$1" ]; then
    APP="${1}"
    if [ -n "$2" ]; then
        APPSITE="${2}"
    else
        APPSITE="${APP}_site"
    fi
else
    echo "Usage: ${PROGRAM} <application> [site dir basename]" 1>&2
    echo "e.g: ${PROGRAM} controller webui" 1>&2
    exit 1
fi

HOMEDIR="/var/lib/${APP}"

# export latest master
git archive --format=tar --prefix=${APP}_new/ origin/master | (cd "${HOMEDIR}" && tar xf -)

# update environment
cd "${HOMEDIR}/${APP}_new"

. ../.virtualenvs/${APP}/bin/activate

export PIP_DOWNLOAD_CACHE=/var/cache/pip_cache
pip install --exists-action w -q -r requirements.txt

# fix db, i18n and static files
cd ${APPSITE}
./manage.py syncdb --migrate --noinput || true
./manage.py compilemessages || true
compass compile ${APP}/static || true
./manage.py collectstatic --noinput
deactivate

# move in position and restart service
sudo supervisorctl stop ${APP}

cd "${HOMEDIR}"
rm -rf ${APP}_previous
mv ${APP} ${APP}_previous
mv ${APP}_new ${APP}

sudo supervisorctl start ${APP}

