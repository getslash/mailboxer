import os
import jinja2

_TEMPLATE_SUFFIX = ".jinja2"

def _load_all_templates():
    package_dir = os.path.dirname(__file__)
    for template_filename in os.listdir(os.path.dirname(__file__)):
        if template_filename.endswith(_TEMPLATE_SUFFIX):
            with open(os.path.join(package_dir, template_filename)) as template_file:
                globals()[template_filename[:-len(_TEMPLATE_SUFFIX)]] = jinja2.Template(template_file.read())
_load_all_templates()
