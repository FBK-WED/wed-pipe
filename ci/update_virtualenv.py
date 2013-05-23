#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
from os import path

PROJECT_ROOT = path.abspath(path.dirname(path.dirname(__file__)))
REQUIREMENTS = [path.join(PROJECT_ROOT, req)
                for req in ['requirements.txt', 'requirements-test.txt']]
VE_ROOT = path.join(PROJECT_ROOT, '.env')
PIP_CACHE_ROOT = '/var/cache/jenkins_pip/'
VE_TIMESTAMP = path.join(VE_ROOT, 'timestamp')
VE_BIN = path.join(VE_ROOT, 'bin')
VE_PIP = path.join(VE_BIN, 'pip')

environment_modified_time = path.getmtime(VE_TIMESTAMP) \
    if path.exists(VE_TIMESTAMP) else 0
requirements_modified_time = max([path.getmtime(req) for req in REQUIREMENTS])


def main():
    if not requirements_modified_time > environment_modified_time:
        print 'Environment already up-to-date'
        return

    import virtualenv
    import subprocess

    if path.exists(VE_ROOT):
        shutil.rmtree(VE_ROOT)
    virtualenv.logger = virtualenv.Logger(consumers=[])
    virtualenv.create_environment(VE_ROOT, site_packages=False)

    # check requirements
    if not path.exists(PIP_CACHE_ROOT):
        os.mkdir(PIP_CACHE_ROOT)

    PIP_BASE = [VE_PIP, 'install', '-q', '-i',
                'https://simple.crate.io/',
                '--extra-index-url', 'http://e.pypi.python.org/simple',
                '--download-cache=%s' % (PIP_CACHE_ROOT,),]
    for req in REQUIREMENTS:
        subprocess.call(PIP_BASE + ['-r', req])

    file(VE_TIMESTAMP, 'w').close()


if __name__ == "__main__":
    main()
