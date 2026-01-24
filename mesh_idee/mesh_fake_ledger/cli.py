"""
Command-line interface for the mesh fake ledger.

Provides commands for account management, transfers, and history queries.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from .ledger_service import LedgerService, LedgerConfig
from .ledger_store import AccountNotFoundError, InsufficientBalanceError, LedgerError


def get_service(ledger_path: Optional[str] = None) -> LedgerService:
    """Get a configured ledger service instance."""
    config = LedgerConfig()
    if ledger_path:
        config.ledger_path = Path(ledger_path)
    return LedgerService(config)


@click.group()
@click.option(
    '--ledger',
    '-l',
    default='ledger.json',
    help='Path to ledger file',
    type=click.Path()
)
@click.pass_context
def cli(ctx, ledger):
    """Mesh Fake Ledger - Off-chain token ledger system."""
    ctx.ensure_object(dict)
    ctx.obj['ledger_path'] = ledger


@cli.command('create-account')
@click.argument('account_id')
@click.option('--balance', '-b', default=0, type=int, help='Initial balance')
@click.pass_context
def create_account(ctx, account_id, balance):
    """Create a new account."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        created = service.create_account_if_missing(account_id, balance)
        
        if created:
            click.secho(f"✓ Account '{account_id}' created with balance: {balance}", fg='green')
        else:
            current_balance = service.get_balance(account_id)
            click.secho(
                f"⚠ Account '{account_id}' already exists with balance: {current_balance}",
                fg='yellow'
            )
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command('balance')
@click.argument('account_id')
@click.pass_context
def balance(ctx, account_id):
    """Get account balance."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        bal = service.get_balance(account_id)
        click.echo(f"Account: {account_id}")
        click.echo(f"Balance: {bal}")
    except AccountNotFoundError:
        click.secho(f"✗ Account '{account_id}' not found", fg='red', err=True)
        sys.exit(1)
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command('transfer')
@click.argument('from_account')
@click.argument('to_account')
@click.argument('amount', type=int)
@click.option('--job-id', '-j', help='Optional job ID')
@click.option('--note', '-n', help='Optional note')
@click.pass_context
def transfer_cmd(ctx, from_account, to_account, amount, job_id, note):
    """Transfer tokens between accounts."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        record = service.charge(from_account, to_account, amount, job_id, note)
        
        click.secho("✓ Transfer completed", fg='green')
        click.echo(f"  Transfer ID: {record['id']}")
        click.echo(f"  From:        {from_account}")
        click.echo(f"  To:          {to_account}")
        click.echo(f"  Amount:      {amount}")
        if job_id:
            click.echo(f"  Job ID:      {job_id}")
        if note:
            click.echo(f"  Note:        {note}")
        
        # Show updated balances
        from_balance = service.get_balance(from_account)
        to_balance = service.get_balance(to_account)
        click.echo(f"\nUpdated balances:")
        click.echo(f"  {from_account}: {from_balance}")
        click.echo(f"  {to_account}:   {to_balance}")
        
    except AccountNotFoundError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)
    except InsufficientBalanceError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command('history')
@click.option('--account', '-a', help='Filter by account ID')
@click.option('--limit', '-l', type=int, default=20, help='Number of records to show')
@click.pass_context
def history(ctx, account, limit):
    """Show transfer history."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        transfers = service.get_transfers(account, limit)
        
        if not transfers:
            click.echo("No transfers found.")
            return
        
        click.echo(f"Transfer History (showing {len(transfers)} most recent):")
        click.echo("-" * 80)
        
        for t in transfers:
            # Format timestamp
            timestamp = t['timestamp'][:19]  # Remove Z and microseconds
            
            # Direction indicator if filtering by account
            direction = ""
            if account:
                if t['from_account'] == account:
                    direction = click.style("→ OUT", fg='red')
                else:
                    direction = click.style("← IN ", fg='green')
            
            click.echo(f"{timestamp} {direction}")
            click.echo(f"  {t['from_account']} → {t['to_account']}")
            click.echo(f"  Amount: {t['amount']}")
            
            if t.get('job_id'):
                click.echo(f"  Job ID: {t['job_id']}")
            if t.get('note'):
                click.echo(f"  Note: {t['note']}")
            
            click.echo(f"  ID: {t['id']}")
            click.echo()
            
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command('list-accounts')
@click.pass_context
def list_accounts(ctx):
    """List all accounts and balances."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        accounts = service.list_accounts()
        
        if not accounts:
            click.echo("No accounts found.")
            return
        
        click.echo("Accounts:")
        click.echo("-" * 50)
        
        # Sort by account ID
        for account_id in sorted(accounts.keys()):
            balance = accounts[account_id]
            click.echo(f"{account_id:30s} {balance:>15,}")
        
        click.echo("-" * 50)
        total = sum(accounts.values())
        click.echo(f"{'Total':30s} {total:>15,}")
        
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


@cli.command('credit')
@click.argument('account_id')
@click.argument('amount', type=int)
@click.option('--reason', '-r', help='Reason for credit')
@click.pass_context
def credit(ctx, account_id, amount, reason):
    """Credit tokens to an account (admin operation)."""
    try:
        service = get_service(ctx.obj['ledger_path'])
        record = service.credit(account_id, amount, reason)
        
        click.secho(f"✓ Credited {amount} tokens to '{account_id}'", fg='green')
        new_balance = service.get_balance(account_id)
        click.echo(f"  New balance: {new_balance}")
        if reason:
            click.echo(f"  Reason: {reason}")
        
    except LedgerError as e:
        click.secho(f"✗ Error: {e}", fg='red', err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
