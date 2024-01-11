#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2016
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Main module where application-specific tasks are defined. The main procedure
is dependent on the fabfileTemplate module.

The complete installation is executing the following steps:

0) Create an instance (if a cloud installation is requested)
1) Install required system packages (as specified in this file below)
2) Create the application user (same name as APP defined here)
3) Execute any requested addition sudo functions (as specified in this file below)
4) copy the APP sources from the current directory to the target host/user
5) Create a virtual environment under the user's home directory
6) Install extra python packages (as specified in this file below)
7) Run the APP specific build command (as specified in this file below)
8) Run the build function if defined (as specified in this file below)
"""
import os, sys
from fabric.state import env
from fabric.colors import red, green
from fabric.operations import local
from fabric.decorators import task
from fabric.context_managers import settings

from fabfileTemplate.utils import home

if sys.version_info.major == 3:
    import urllib.request as urllib2
else:
    import urllib2

# The following variable will define the Application name as well as directory
# structure and a number of other application specific names.
APP = "geckos"

# The username to use by default on remote hosts where APP is being installed
# This user might be different from the initial username used to connect to the
# remote host, in which case it will be created first
APP_USER = APP.lower()

# Name of the directory where APP sources will be expanded on the target host
# This is relative to the APP_USER home directory
APP_SRC_DIR_NAME = APP.lower() + "_src"

# Name of the directory where APP root directory will be created
# This is relative to the APP_USER home directory
APP_ROOT_DIR_NAME = APP.upper()

# Name of the directory where a virtualenv will be created to host the APP
# software installation, plus the installation of all its related software
# This is relative to the APP_USER home directory
APP_INSTALL_DIR_NAME = APP.lower() + "_rt"

# Sticking with Python3.6 because that is available on AWS instances.
APP_PYTHON_VERSION = "3.11"

# URL to download the correct Python version
APP_PYTHON_URL = "https://www.python.org/ftp/python/3.11.7/Python-3.11.7.tgz"

# NOTE: Make sure to modify the following lists to meet the requirements for
# the application.
APP_DATAFILES = []

# AWS specific settings
env.AWS_REGION = "us-east-1"
env.AWS_AMI_NAME = "Amazon"
env.AWS_INSTANCES = 1
env.AWS_INSTANCE_TYPE = "t2.micro"
# env.AWS_INSTANCE_TYPE = "r5a.8xlarge"  # !!!!! careful with this one !!!!!
env.AWS_KEY_NAME = "icrar_eagle"
env.AWS_SEC_GROUP = "NGAS"  # Security group allows SSH and other ports
env.AWS_SUDO_USER = "ec2-user"  # required to install init scripts.

env.APP_NAME = APP
env.APP_USER = APP_USER
env.APP_INSTALL_DIR_NAME = APP_INSTALL_DIR_NAME
env.APP_ROOT_DIR_NAME = APP_ROOT_DIR_NAME
env.APP_SRC_DIR_NAME = APP_SRC_DIR_NAME
env.APP_PYTHON_VERSION = APP_PYTHON_VERSION
env.APP_PYTHON_URL = APP_PYTHON_URL
env.APP_DATAFILES = APP_DATAFILES
env.APP_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Alpha-sorted packages per package manager
env.pkgs = {
    "YUM_PACKAGES": [
        "python3.11.x86_64",
        "python3.11-devel.x86_64",
        "python3.11-wheel.noarch",
        "python3.11-pip-wheel.noarch",
        "python3.11-setuptools-wheel.noarch",
        "gcc",
        "g++",
        "make",
        "zlib-devel",
        "openssl-devel",
        "libffi-devel",
        "git",
    ],
    "APT_PACKAGES": [
        "tar",
        "wget",
        "gcc",
        "git",
        "zlib-devel",
    ],
    "SLES_PACKAGES": [
        "wget",
        "zlib",
        "zlib-devel",
        "gcc",
    ],
    "BREW_PACKAGES": [
        "wget",
    ],
    "PORT_PACKAGES": [
        "wget",
    ],
    "APP_EXTRA_PYTHON_PACKAGES": [
        "extinction",
    ],
}

# This dictionary defines the visible exported tasks.
__all__ = []

# >>> The following imports need to be after the definitions above!!!

from fabfileTemplate.utils import sudo, info, success, default_if_empty
from fabfileTemplate.system import check_command
from fabfileTemplate.APPcommon import (
    virtualenv,
    APP_doc_dependencies,
    APP_source_dir,
    APP_root_dir,
)
from fabfileTemplate.APPcommon import (
    extra_python_packages,
    APP_user,
    build,
    APP_install_dir,
)


def APP_build_cmd():
    # >>>> NOTE: This function potentially needs heavy customisation <<<<<<
    build_cmd = []
    # linux_flavor = get_linux_flavor()

    env.APP_INSTALL_DIR = os.path.abspath(os.path.join(home(), APP_INSTALL_DIR_NAME))
    env.APP_ROOT_DIR = os.path.abspath(os.path.join(home(), APP_ROOT_DIR_NAME))
    env.APP_SRC_DIR = os.path.abspath(os.path.join(home(), APP_SRC_DIR_NAME))
    build_cmd.append("cd {0} ;".format(APP_source_dir()))
    build_cmd.append("pip install . ;")
    build_cmd.append(
        "cd .. ;git clone https://github.com/geckos-survey/gist-geckos-supp-public.git ;"
    )

    return " ".join(build_cmd)


def extra_sudo():
    """
    nothing to do here
    """
    pass


def install_sysv_init_script(nsd, nuser, cfgfile):
    """
    nothing to do here
    """
    pass


def dummy(*args, **kwargs):
    """
    Eat all args and kwargs provided, but do nothing
    """
    pass


env.build_cmd = APP_build_cmd
env.APP_init_install_function = dummy
env.sysinitAPP_start_check_function = dummy
env.APP_extra_sudo_function = dummy
