from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def render_config(vendor: str, data: dict):
    template_name = f"{vendor.lower()}_baseline.j2"
    template = env.get_template(template_name)
    return template.render(data)
