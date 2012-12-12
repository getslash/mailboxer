import subprocess
from ..test_utils.config_utils import get_config_boolean

def setup():
    if get_config_boolean("vagrant_enabled", True):
        _execute_assert_success("fab deploy_to_vagrant", shell=True)
def teardown():
    if get_config_boolean("vagrant_enabled", True) and not get_config_boolean("vagrant_leave_on", False):
        _execute_assert_success("fab vagrant:halt", shell=True)

def _execute_assert_success(cmd, **kwargs):
    p = subprocess.Popen(cmd, **kwargs)
    assert p.wait() == 0
    return p
