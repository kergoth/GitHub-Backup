#!/usr/bin/env python

# Author: Anthony Gargiulo (anthony@agargiulo.com)
# Created Fri Jun 15 2012

import pygithub3
from argparse import ArgumentParser
from collections import defaultdict
import os
import sys
import subprocess

def main():
   parser = init_parser()
   args = parser.parse_args()
   args.repodir = args.repodir.format(username=args.username, repo_type="{repo_type}")
   args.gistsdir = args.gistsdir.format(username=args.username, repodir=args.repodir, repo_type="{repo_type}")

   try:
      user = run(['git', 'config', 'github.user'])
   except Exception:
      user = None

   try:
      password = run(['git', 'config', 'github.password'])
   except Exception:
      password = None

   try:
      token = run(['git', 'config', 'github.token'])
   except Exception:
      token = None

   if not user:
      user = os.environ.get('GITHUB_USER', os.environ.get('GITHUB_USER'))

   if not password:
      password = os.environ.get('GITHUB_PASSWORD', os.environ.get('GITHUB_PASSWORD'))

   if not user:
      sys.exit("Unable to determine github username, please set github.user or export GITHUB_USER")

   if not password and not token:
      if not args.cron:
         sys.stderr.write("Unable to determine github password or token. To access private repositories, set github.password, github.token or export GITHUB_PASSWORD\n")
         sys.stderr.write("For help on oauth based token authentication see https://help.github.com/articles/creating-an-oauth-token-for-command-line-use\n")
      user = None

   gh = pygithub3.Github(login=user, password=password, token=token)
   repositories = get_repositories(gh, user, args.username)

   for repo_type, repos in sorted(repositories.iteritems(), key=lambda i: i[0]):
      if repo_type.startswith('gists/'):
         repo_type = repo_type[6:]
         gistsdir = args.gistsdir.format(repo_type=repo_type)
         for repo in repos:
            clone(repo.git_pull_url, os.path.join(gistsdir, repo.id), name=repo.id, mirror=args.mirror)
      else:
         repodir = args.repodir.format(repo_type=repo_type)
         for repo in repos:
            clone(repo.clone_url, os.path.join(repodir, repo.name), name=repo.full_name, mirror=args.mirror)


def get_repositories(github, auth_user, username):
   repositories = defaultdict(list)
   repositories['watched'] = github.repos.watchers.list_repos(username).all()
   if auth_user == username:
      repositories['gists/starred'] = github.gists.starred().all()

   for gist in github.gists.list(username).all():
      if gist.public:
         repositories['gists/public'].append(gist)
      else:
         repositories['gists/private'].append(gist)

   try:
      repos = github.repos.list_by_org(username).all()
   except pygithub3.exceptions.NotFound:
      repos = github.repos.list(username).all()

   for repo in repos:
      if repo.fork:
         repositories['forks'].append(repo)
      elif repo.private:
         repositories['private'].append(repo)
      # elif repo.description and 'mirror' in repo.description:
      #    repositories['mirrors'].append(repo)
      else:
         repositories['public'].append(repo)

   return repositories


def init_parser():
   """
   set up the argument parser
   """
   parser = ArgumentParser(
      description="""Backup all of a github user's repositories and gists.

   The 'dir' commandline options (-b, -g) may use 'username' and 'repo_type' patterns in braces. repo_type will resolve to 'public', 'private', 'forks', 'watched', or 'starred', as appropriate.""")

   parser.add_argument("username", help="A Github username, default to GITHUB_USER or LOGNAME")
   parser.add_argument("-r", "--repodir", default="./{username}/{repo_type}",
         help="The folder where you want your backup repos to go (Default: %(default)s)")
   parser.add_argument("-g", "--gistsdir", default="./{username}/gists/{repo_type}",
         help="The folder where you want your backup gists to go (Default: %(default)s)")
   parser.add_argument("-m","--mirror", help="Use the --mirror option when cloning",
      action="store_true")
   return parser


def run(cmd):
    stdout, stderr = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    return stdout.rstrip()


def clone(url, destdir, quiet=False, name=None, mirror=False):
   if name is None:
      name = os.path.basename(url)

   if quiet:
      git_args = "-q"
   else:
      print("Processing {}".format(name))
      git_args = ""

   if mirror:
      git_args += " --mirror"
      if not destdir.endswith('.git'):
         destdir += ".git"

   if os.path.exists(destdir):
      if not quiet:
         print("Updating existing repo at {}".format(destdir))
      os.system('cd {} && git pull {}'.format(destdir, git_args))
   else:
      if not quiet:
         print("Cloning {} to {}".format(url, destdir))
      os.system('git clone {} {} {}'.format(git_args, url, destdir))

   if mirror:
      if not quiet:
         print("Updating server info in {}".format(destdir))
      os.system('git update-server-info')

if __name__ == "__main__":
   main()

# vim: set et fenc=utf-8 sts=3 sw=3 :
