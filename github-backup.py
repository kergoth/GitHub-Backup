#!/usr/bin/env python

# Author: Anthony Gargiulo (anthony@agargiulo.com)
# Created Fri Jun 15 2012

from pygithub3 import Github
from argparse import ArgumentParser
import os
import sys
import subprocess

def run(cmd):
    stdout, stderr = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    return stdout.rstrip()

def main():
   # A sane way to handle command line args.
   # Now actually store the args
   parser = init_parser()
   args = parser.parse_args()

   try:
      user = run(['git', 'config', 'github.user'])
   except Exception:
      user = os.environ.get('GITHUB_USER', os.environ.get('LOGNAME'))

   try:
      password = run(['git', 'config', 'github.password'])
   except Exception:
      password = os.environ.get('GITHUB_PASSWORD')

   try:
      token = run(['git', 'config', 'github.token'])
   except Exception:
      token = None

   if not user:
      sys.exit("Unable to determine github username, please set github.user or export GITHUB_USER")

   if not password:
      sys.stderr.write("Unable to determine github password. To access private repositories, set github.password or export GITHUB_PASSWORD\n")
      user = None

   # Make the connection to Github here.
   gh = Github(login=user, password=password, token=token)

   # Get all of the given user's repos
   repos = gh.repos.list_by_org(args.username).all()
   if not repos:
      repos = gh.repos.list(args.username).all()
   for repo in repos:
      process_repo(repo, args)

def init_parser():
   """
   set up the argument parser
   """
   parser = ArgumentParser(
   description="makes a backup of all of a github user's repositories")
   parser.add_argument("username", help="A Github username, default to GITHUB_USER or LOGNAME")
   parser.add_argument("backupdir",
      help="The folder where you want your backups to go")
   parser.add_argument("-c","--cron", help="Use this when running from a cron job",
      action="store_true")
   return parser


def process_repo(repo, args):
   if args.cron:
      git_args = "-q"
   else:
      git_args = ""

   if not args.cron:
      print("Processing repo: {}".format(repo.full_name))

   if os.access('{}/{}/.git'.format(args.backupdir,repo.name),os.F_OK):
      if not args.cron:
         print("Repo already exists, let's try to update it instead")
      os.system('cd {}/{};git pull {}'.format(args.backupdir, repo.name, git_args))
   else: # Repo doesn't exist, let's clone it
      os.system('git clone {} {} {}/{}'.format(git_args, repo.clone_url, args.backupdir, repo.name))

if __name__ == "__main__":
   main()
