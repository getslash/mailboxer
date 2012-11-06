import os
import glob
from fabric.api import *

def compile_css():
    _reset_bootstrap()
    _patch_bootstrap()
    _build_bootstrap()
    _reset_bootstrap() # restore to original state

STYLE_SRC_ROOT = os.path.abspath("www/styles/src")
BOOTSTRAP_SRC_ROOT = os.path.abspath(os.path.join(STYLE_SRC_ROOT, "_bootstrap"))
RESULT_CSS = os.path.abspath("www/static/css/style.css")

def _reset_bootstrap():
    local("git submodule update --init --recursive")
    with lcd(BOOTSTRAP_SRC_ROOT):
        local("git reset --hard")
        local("git clean -fdx")

def _patch_bootstrap():
    for patch in sorted(glob.glob("{0}/bootstrap_patches/*.patch".format(STYLE_SRC_ROOT))):
        patch = os.path.abspath(patch)
        with lcd(BOOTSTRAP_SRC_ROOT):
            local("git apply < {0}".format(patch))

def _build_bootstrap():
    local("lessc --verbose --compress {0}/root.less {1}".format(STYLE_SRC_ROOT, RESULT_CSS))
