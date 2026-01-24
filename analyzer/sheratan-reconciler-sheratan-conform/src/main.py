"""CLI interface for Sheratan Version Reconciler."""

import click
from pathlib import Path
from typing import Dict
from .app import SheratanReconciler


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Sheratan Version Reconciler - Merge and reconcile multiple Sheratan installations."""
    pass


@cli.command()
@click.argument('directories', nargs=-1, required=True)
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def scan(directories, config):
    """Scan and analyze multiple Sheratan directories.
    
    Example:
        sheratan-reconciler scan /path/to/sheratan1 /path/to/sheratan2
    """
    # Parse directories
    dir_dict = _parse_directories(directories)
    
    # Initialize reconciler
    config_path = Path(config) if config else None
    reconciler = SheratanReconciler(config_path)
    
    # Perform scan
    results = reconciler.scan(dir_dict)
    
    if 'error' in results:
        click.echo(f"Error: {results['error']}", err=True)
        return 1
    
    click.echo("\n✓ Scan complete!")
    return 0


@cli.command()
@click.argument('directories', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), default='sheratan_comparison_report.md',
              help='Output file path for report')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'html']), 
              default='markdown', help='Report format')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def compare(directories, output, format, config):
    """Generate detailed comparison report.
    
    Example:
        sheratan-reconciler compare /path/to/sheratan1 /path/to/sheratan2 -o report.md
    """
    # Parse directories
    dir_dict = _parse_directories(directories)
    
    # Initialize reconciler
    config_path = Path(config) if config else None
    reconciler = SheratanReconciler(config_path)
    reconciler.reporter.output_format = format
    
    # Generate report
    output_path = Path(output)
    reconciler.compare(dir_dict, output_path)
    
    click.echo(f"\n✓ Comparison report generated: {output_path}")
    return 0


@cli.command()
@click.argument('directories', nargs=-1, required=True)
@click.option('--output', '-o', type=click.Path(), help='Output directory for merged version')
@click.option('--dry-run', is_flag=True, help='Perform dry run without making changes')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def merge(directories, output, dry_run, config):
    """Merge multiple Sheratan versions into unified installation.
    
    Example:
        sheratan-reconciler merge /path/to/sheratan1 /path/to/sheratan2 -o ./unified
    """
    # Parse directories
    dir_dict = _parse_directories(directories)
    
    # Initialize reconciler
    config_path = Path(config) if config else None
    reconciler = SheratanReconciler(config_path)
    
    # Perform merge
    output_dir = Path(output) if output else None
    results = reconciler.merge(dir_dict, output_dir, dry_run=dry_run)
    
    if 'error' in results:
        click.echo(f"Error: {results['error']}", err=True)
        return 1
    
    if results.get('cancelled'):
        click.echo("Merge cancelled by user.")
        return 0
    
    return 0


@cli.command()
@click.argument('directories', nargs=-1, required=True)
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def report(directories, config):
    """Export detailed analysis report in multiple formats.
    
    Example:
        sheratan-reconciler report /path/to/sheratan1 /path/to/sheratan2
    """
    # Parse directories
    dir_dict = _parse_directories(directories)
    
    # Initialize reconciler
    config_path = Path(config) if config else None
    reconciler = SheratanReconciler(config_path)
    
    # Perform analysis
    results = reconciler.scan(dir_dict)
    
    if 'error' in results:
        click.echo(f"Error: {results['error']}", err=True)
        return 1
    
    # Export in multiple formats
    formats = ['markdown', 'json', 'html']
    for fmt in formats:
        output_path = Path(f'sheratan_report.{fmt}')
        reconciler.report(results, output_path, format=fmt)
    
    click.echo("\n✓ Reports generated in multiple formats!")
    return 0


def _parse_directories(directory_args) -> Dict[str, Path]:
    """Parse directory arguments into version name -> path mapping.
    
    Args:
        directory_args: Tuple of directory paths
        
    Returns:
        Dictionary mapping version names to paths
    """
    dir_dict = {}
    
    for i, dir_path in enumerate(directory_args):
        path = Path(dir_path)
        # Use directory name as version name
        version_name = path.name if path.exists() else f"version_{i+1}"
        dir_dict[version_name] = path
    
    return dir_dict


if __name__ == '__main__':
    cli()
