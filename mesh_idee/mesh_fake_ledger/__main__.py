"""
Entry point for running mesh_fake_ledger as a module.

Usage:
    python -m mesh_fake_ledger [command] [options]
"""

from .cli import cli

if __name__ == '__main__':
    cli(obj={})
