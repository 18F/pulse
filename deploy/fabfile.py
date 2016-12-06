import time
from fabric.api import run, execute, env

# Will default to staging, override with "fab [command] --set environment=production"

environment = env.get('environment', None)

env.use_ssh_config = True
env.hosts = ["site@pulse"]

repo = "https://github.com/18F/pulse"

if environment == "production":
  branch = "master"
  port = 3000
else:
  environment = "staging"
  branch = "master"
  port = 6000

home = "/home/site/pulse/%s" % environment
shared_path = "%s/shared" % home
versions_path = "%s/versions" % home
version_path = "%s/%s" % (versions_path, time.strftime("%Y%m%d%H%M%S"))
current_path = "%s/current" % home

virtualenv = "pulse-%s" % environment

pid_file = "%s/gunicorn.pid" % shared_path
log_file = "%s/gunicorn.log" % shared_path

wsgi = "pulse:app"

# Keep the last 5 deployed versions around for easy rollback.
keep = 5


def checkout():
  run('git clone -q -b %s %s %s' % (branch, repo, version_path))

def dependencies():
  run('cd %s && workon %s && pip install -r requirements.txt' % (version_path, virtualenv))

def make_current():
  run('rm -f %s && ln -s %s %s' % (current_path, version_path, current_path))

def links():
  run("ln -s %s/data/db.json %s/data/db.json" % (shared_path, version_path))
  run("ln -s %s/config.env %s/data/config.env" % (shared_path, version_path))
  run("ln -s %s/data/output %s/data/output" % (shared_path, version_path))

# Only done on cold deploy.
def init():
  run("mkdir -p %s/data/output" % shared_path)
  run("rmvirtualenv %s" % virtualenv)
  run("mkvirtualenv %s" % virtualenv)
  run("cd %s && make data_init" % version_path)

def cleanup():
  versions = run("ls -x %s" % versions_path).split()
  destroy = versions[:-keep]

  for version in destroy:
    command = "rm -rf %s/%s" % (versions_path, version)
    run(command)


## can be run on their own

def start():
  run(
    (
      "cd %s && workon %s && PORT=%i gunicorn %s -D --log-file=%s --pid %s"
    ) % (current_path, virtualenv, port, wsgi, log_file, pid_file), pty=False
  )

def stop():
  run("kill `cat %s`" % pid_file)

def restart():
  run("kill -HUP `cat %s`" % pid_file)


def deploy():
  execute(checkout)
  execute(links)
  execute(dependencies)
  execute(make_current)
  execute(restart)
  execute(cleanup)

def deploy_cold():
  execute(checkout)
  execute(links)
  execute(init)
  execute(dependencies)
  execute(make_current)
  execute(start)

# Will affect production and staging environments.
def update_crontab():
  run("cat %s/deploy/crontab | crontab" % (current_path))

# Update the environment with the latest S3 data.
def data_init():
  run("cd %s && workon %s && make data_init" % (current_path, virtualenv))
