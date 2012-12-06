import os

##################################### Tasks ####################################
from deployment.debug import debug
from deployment.deployment import (
    deploy_to_server,
    deploy_to_vagrant,
    vagrant,
)
from deployment.assets import (
    compile_css,
)
