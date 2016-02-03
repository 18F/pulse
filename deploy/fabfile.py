import time
from fabric.api import run, execute, env

# Will default to staging, override with "fab [command] --set environment=production"

environment = env.get('environment', None)

env.use_ssh_config = True
env.hosts = ["site@pulse2"]

repo = "https://github.com/18F/pulse"

if environment == "production":
  branch = "production"
  port = 3000
else:
  environment = "staging"
  branch = "accessibility_page"
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
  execute(dependencies)
  execute(make_current)
  execute(restart)
  execute(cleanup)



# import time
# from fabric.api import run, execute, env, cd

# """
# Manage auto-deploy webhooks remotely.

# Production hook:

#   forever start -l $HOME/pulse/hookshot.log -a deploy/hookshot.js -p 5000 -b production -c "cd $HOME/pulse/production/current && git pull && bundle exec jekyll build >> $HOME/pulse/hookshot.log"
#   forever restart deploy/hookshot.js -p 5000 -b production -c "cd $HOME/pulse/production/current && git pull && bundle exec jekyll build >> $HOME/pulse/hookshot.log"
#   forever stop deploy/hookshot.js -p 5000 -b production -c "cd $HOME/pulse/production/current && git pull && bundle exec jekyll build >> $HOME/pulse/hookshot.log"
# """

# environment = "production"
# branch = "production"
# port = 5000

# env.use_ssh_config = True

# home = "/home/site/pulse"
# log = "%s/hookshot.log" % home
# current = "%s/%s/current" % (home, environment)

# # principal command to run upon update
# command = "cd %s && git pull && bundle exec jekyll build >> %s" % (current, log)

# def start():
#   run(
#     "cd %s && forever start -l %s -a deploy/hookshot.js -p %i -b %s -c \"%s\""
#     % (current, log, port, branch, command)
#   )

# def stop():
#   run(
#     "cd %s && forever stop deploy/hookshot.js -p %i -b %s -c \"%s\""
#     % (current, port, branch, command)
#   )

# def restart():
#   run(
#     "cd %s && forever restart deploy/hookshot.js -p %i -b %s -c \"%s\""
#     % (current, port, branch, command)
#   )
