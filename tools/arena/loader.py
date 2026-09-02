'''
	Git-worktree management: checks out a given ref into an isolated directory so its
	version of the bot code can be run (in a subprocess, see worker.py) without touching
	the user's working tree and without colliding with another ref's checkout.
'''

import hashlib
import subprocess


def _run(cmd, cwd=None):
	result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
	if result.returncode != 0:
		raise RuntimeError("Command failed: %s\n%s" % (" ".join(cmd), result.stderr))
	return result.stdout.strip()


def alias_for(ref):
	digest = hashlib.sha1(ref.encode('utf-8')).hexdigest()[:10]
	return "arena_%s" % digest


def add_worktree(repo_root, ref, worktree_root):
	'''Returns (alias, worktree_dir). Reuses an existing worktree for this ref if already checked out.'''
	alias = alias_for(ref)
	worktree_dir = worktree_root / alias
	if worktree_dir.exists():
		return alias, worktree_dir

	resolved = _run(['git', 'rev-parse', ref], cwd=str(repo_root))
	worktree_root.mkdir(parents=True, exist_ok=True)
	_run(['git', 'worktree', 'add', '--detach', str(worktree_dir), resolved], cwd=str(repo_root))
	return alias, worktree_dir


def remove_worktree(repo_root, worktree_dir):
	_run(['git', 'worktree', 'remove', '--force', str(worktree_dir)], cwd=str(repo_root))


def prune_worktrees(repo_root):
	_run(['git', 'worktree', 'prune'], cwd=str(repo_root))
