import click
import requests
import os
import sys
import pwd
import json
import string
import random
import subprocess
from jinja2 import Environment, PackageLoader, select_autoescape
from psutil import virtual_memory
from math import floor, ceil, log2

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

def current_ip_address():
    r = requests.get('https://wtfismyip.com/text')
    return r.text.strip() if r.status_code == 200 else None

def resolve_dns(domain):
    payload = {'name': domain, 'type': 'A'}
    r = requests.get("https://dns.google/resolve", params=payload)
    
    if r.status_code == 200:
        res = r.json()
        if 'Answer' in res and 'data' in res['Answer'][0]:
            return res['Answer'][0]['data']

    return None

def render_script(filepath, **context):
    template = jinja_env.get_template(filepath)
    return template.render(context)

def write_to_file(filepath, content, chmod=0o600):
    with open(filepath, 'w') as f:
        f.write(content)
    os.chmod(filepath, chmod)

def run_script(script_content):
    global dryRun

    tmp_file = "/tmp/lenmay-{}.sh".format(random.randint(10E9, 10E12))
    write_to_file(tmp_file, script_content)
    
    # i don't want to run on my dev computer, sorry for hard-code
    endpoint_cmd = '/usr/bin/cat' if dryRun or os.uname()[1] == 'khanhicetea-xps' else '/usr/bin/sh'

    print("Running {} {}".format(endpoint_cmd, tmp_file))
    with subprocess.Popen([endpoint_cmd, tmp_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, universal_newlines=True) as proc:
        for l in proc.stdout:
            print(l, end='')
    return proc.returncode

def run_script_template(filepath, **context):
    return run_script(render_script(filepath, **context))

def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(length))

def innodb_buffer_pool_size():
    mem = virtual_memory()
    if mem.total < (1 * 1024 * 1024 * 1024):
        return 128
    instances = max(1, floor(mem.total / (128 * 1024 * 1024) * 0.40))
    return instances * 128

def is_user_exists(username):
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

@click.group()
def cli():
    pass

@click.command()
@click.option('--dry', is_flag=True, prompt='Dry run?')
@click.option('--default', is_flag=True, default=True, prompt='Default settings')
def init(dry, default):
    global dryRun
    dryRun = dry

    if init_settings:
        return click.echo("Your system is already lenmay-ed, good luck!")

    settings = { 
        "timezone": "Asia/Ho_Chi_Minh",
        "nginx": True,
        "mysql": True,
        "redis": True,
        "nodejs": True,
        "php": True,
        "php_ver": "7.4",
        "supervisor": True,
        "jobber": True,
        "email": "",
    }

    if not default:
        settings["email"] = click.prompt("Email (for LetsEncrypt) ?")
        settings["timezone"] = click.prompt("Default timezone ?", default=settings["timezone"])
        settings["nginx"] = click.confirm("NginX ?", settings["nginx"])
        settings["mysql"] = click.confirm("Mysql ?", settings["mysql"])
        settings["redis"] = click.confirm("Redis ?", settings["redis"])
        settings["nodejs"] = click.confirm("Nodejs ?", settings["nodejs"])
        settings["php"] = click.confirm("PHP ?", settings["php"])
        settings["supervisor"] = click.confirm("Supervisor ?", settings["supervisor"])
        settings["jobber"] = click.confirm("Jobber (cron alternative) ?", settings["jobber"])

        if settings["php"]:
            settings["php_ver"] = click.prompt("PHP Version ?", type=click.Choice(["7.4", "8.0"]), default=settings["php_ver"])

    # ensure homedir is existed
    if not os.path.exists(home_dir):
        os.mkdir(home_dir)

    pool_size = innodb_buffer_pool_size()
    mysql_random_password = random_string(12)

    ret = run_script_template("init/main.sh.j2", **settings, mysql_root_password=mysql_random_password, innodb_pool_size=pool_size)
    
    if ret == 0:
        # write settings to home
        write_to_file(settings_path, json.dumps(settings))
        click.echo("DONE !")
    else:
        click.echo("FAILED !")

@click.command()
@click.option('--dry', is_flag=True, prompt='Dry run?')
def web(dry):
    global dryRun
    dryRun = dry

    username = click.prompt("Username ? ")
    domains = click.prompt("Domain (multi domains separated by space)")
    list_domains = domains.split()
    main_domain = list_domains[0]
    le_email = click.prompt("Email for LetsEncrypt", init_settings["email"])
    root_dir = click.prompt("Document Root", "/home/{}/{}/public".format(username, main_domain))
    mysql_db = click.prompt("DB Name (without prefix {}_ ,leave blank if no need)".format(username), default='')

    current_ip = current_ip_address()
    for d in list_domains:
        if resolve_dns(d) != current_ip:
            return click.echo("Oops ! Please point the domain {} to {}".format(d, current_ip))

    mysql_random_password = random_string(12)
    user_existed = is_user_exists(username)
    ret0 = 0 if user_existed else run_script_template("web/create_user.sh.j2", **init_settings, username=username, mysql_password=mysql_random_password)
    
    if ret0 == 0:
        ret1 = run_script_template("web/create_site.sh.j2", **init_settings, username=username, list_domains=list_domains,
            domains=domains, main_domain=main_domain, le_email=le_email, root_dir=root_dir, mysql_db=mysql_db)
        if ret1 == 0:
            click.echo("===================================================================")
            click.echo("Created domain {} inside {} user home".format(main_domain, username))
            if not user_existed:
                click.echo("Your MySQL user / password is : {} / {}".format(username, mysql_random_password))
            click.echo("===================================================================")
            return click.echo("DONE !")

    click.echo("FAILED !")

cli.add_command(init)
cli.add_command(web)

if __name__ == '__main__':
    cli()