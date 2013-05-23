#!/bin/sh
# shell helper to run some lint on python and javascript code

REPORTS="$2"
PROGRAMNAME="$(basename $0)"

PROJECTNAME="$1"

PWD=$(pwd)

usage () {
    echo "Usage: ${PROGRAMNAME} django-project" 1>&2
}

if [ -z "${PROJECTNAME}" ]; then
    usage
    exit 1
fi

# override exit on errors
set +e

# run pylint
pylint --rcfile=.pylintrc -f parseable "${PROJECTNAME}" > "${REPORTS}/pylint.report"

# run pep8
pep8 --exclude=migrations,static "${PROJECTNAME}" > "${REPORTS}/pep8.report"

# jshint
# requires a nodejs called 'node' in PATH
if which jshint >/dev/null ; then
    find "${PROJECTNAME}" -name "*.js" -wholename "*static*" \! -wholename "*deps*" \! -wholename "*fc/static*" -print0 | xargs -0 jshint --jslint-reporter > "${REPORTS}/jshint.report" || true
fi

# run scss-lint
/usr/local/bin/scss-lint -x "${PWD}/${PROJECTNAME}"/scss/src/* > "${REPORTS}/scss-lint.report" || true
