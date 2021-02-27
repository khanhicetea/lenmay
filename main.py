import click
import os
import sys
import json
import string
import random
import subprocess
from jinja2 import Environment, PackageLoader, select_autoescape

dryRun = False
home_dir = os.path.expanduser("~") + "/.lenmay"
settings_path = home_dir+'/settings.json'
jinja_env = Environment(
    loader=PackageLoader(__name__, 'templates'),
    autoescape=select_autoescape(['html'])
)

init_settings = None
if os.path.isfile(settings_path):
    with open(settings_path, 'r') as f:
        init_settings = json.load(f)

def render_script(filepath, **context):
    template = jinja_env.get_template(filepath)
    return template.render(context)

def write_to_file(filepath, content, chmod=0o600):
    with open(filepath, 'w') as f:
        f.write(content)
    os.chmod(filepath, chmod)

def run_script(script_content):
    tmp_file = "/tmp/lenmay-{}.sh".format(random.randint(10E9, 10E12))
    write_to_file(tmp_file, script_content)
    
    # i don't want to run on my dev computer
    endpoint_cmd = '/usr/bin/cat' if dryRun or os.uname()[1] == 'khanhicetea-xps' else '/usr/bin/sh'

    print("Running {} {}".format(endpoint_cmd, tmp_file))
    with subprocess.Popen([endpoint_cmd, tmp_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, universal_newlines=True) as proc:
        for l in proc.stdout:
            print(l, end='')
    return proc.returncode

def run_script_template(filepath, **context):
    return run_script(render_script(filepath, **context))

@click.group()
def cli():
    pass

@click.command()
@click.option('--default', is_flag=True, default=True, prompt='Default settings')
@click.option('--dry', is_flag=True, prompt='Dry run?')
def init(default, dry):
    if init_settings:
        return click.echo("Your system is already lenmay-ed, good luck!")

    settings = { 
        "timezone": "Asia/Ho_Chi_Minh",
        "nginx": True,
        "mysql": True,
        "redis": True,
        "nodejs": True,
        "php": True,
        "supervisor": True,
        "netdata": True,
    }

    dryRun = dry

    if not default:
        settings["timezone"] = click.prompt("Default timezone ? ", default=settings["timezone"])
        settings["nginx"] = click.confirm("NginX ?", settings["nginx"])
        settings["mysql"] = click.confirm("Mysql ?", settings["mysql"])
        settings["redis"] = click.confirm("Redis ?", settings["redis"])
        settings["nodejs"] = click.confirm("Nodejs ?", settings["nodejs"])
        settings["php"] = click.confirm("PHP ?", settings["php"])
        settings["supervisor"] = click.confirm("Supervisor ?", settings["supervisor"])
        settings["netdata"] = click.confirm("Netdata ?", settings["netdata"])

    # ensure homedir is existed
    if not os.path.exists(home_dir):
        os.mkdir(home_dir)

    mysql_random_password  = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(12))

    ret = run_script_template("init/main.sh.twig", **settings, mysql_root_password=mysql_random_password)
    
    if ret == 0:
        # write settings to home
        write_to_file(settings_path, json.dumps(settings))
        click.echo("DONE !")
    else:
        click.echo("FAILED !")

cli.add_command(init)

if __name__ == '__main__':
    cli()