"""Report generation utilities for Sheratan Version Reconciler."""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class Reporter:
    """Generates reports in various formats."""
    
    def __init__(self, output_format: str = 'markdown'):
        """Initialize reporter.
        
        Args:
            output_format: Output format (markdown, json, html)
        """
        self.output_format = output_format
    
    def generate_comparison_report(self, analysis_results: Dict[str, Any], output_path: Path = None) -> str:
        """Generate comparison report from analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis data
            output_path: Optional path to save report
            
        Returns:
            Report content as string
        """
        if self.output_format == 'markdown':
            report = self._generate_markdown_report(analysis_results)
        elif self.output_format == 'json':
            report = self._generate_json_report(analysis_results)
        elif self.output_format == 'html':
            report = self._generate_html_report(analysis_results)
        else:
            report = self._generate_markdown_report(analysis_results)
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown format report."""
        lines = []
        lines.append("# Sheratan Version Comparison Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary section
        if 'summary' in results:
            lines.append("## Summary\n")
            summary = results['summary']
            lines.append(f"- **Versions Compared:** {summary.get('version_count', 0)}")
            lines.append(f"- **Total Files Analyzed:** {summary.get('total_files', 0)}")
            lines.append(f"- **Files with Differences:** {summary.get('different_files', 0)}")
            lines.append(f"- **Unique Files:** {summary.get('unique_files', 0)}")
            lines.append(f"- **Conflicts Detected:** {summary.get('conflicts', 0)}\n")
        
        # File structure analysis
        if 'file_structure' in results:
            lines.append("## File Structure Analysis\n")
            fs = results['file_structure']
            
            if 'missing_files' in fs and fs['missing_files']:
                lines.append("### Missing Files\n")
                for version, files in fs['missing_files'].items():
                    if files:
                        lines.append(f"**{version}:**")
                        for f in files[:20]:  # Limit to 20
                            lines.append(f"- `{f}`")
                        if len(files) > 20:
                            lines.append(f"- ... and {len(files) - 20} more\n")
                        else:
                            lines.append("")
            
            if 'extra_files' in fs and fs['extra_files']:
                lines.append("### Extra Files\n")
                for version, files in fs['extra_files'].items():
                    if files:
                        lines.append(f"**{version}:**")
                        for f in files[:20]:
                            lines.append(f"- `{f}`")
                        if len(files) > 20:
                            lines.append(f"- ... and {len(files) - 20} more\n")
                        else:
                            lines.append("")
        
        # Code differences
        if 'code_diff' in results:
            lines.append("## Code Differences\n")
            cd = results['code_diff']
            
            if 'modified_files' in cd:
                lines.append(f"### Modified Files ({len(cd['modified_files'])})\n")
                for file_info in cd['modified_files'][:10]:  # Show top 10
                    lines.append(f"#### `{file_info['file']}`\n")
                    lines.append(f"- **Change Type:** {file_info.get('change_type', 'modified')}")
                    lines.append(f"- **Severity:** {file_info.get('severity', 'medium')}")
                    if 'description' in file_info:
                        lines.append(f"- **Description:** {file_info['description']}\n")
                    else:
                        lines.append("")
        
        # Configuration drift
        if 'config_drift' in results:
            lines.append("## Configuration Drift\n")
            cfg = results['config_drift']
            
            if 'conflicts' in cfg and cfg['conflicts']:
                lines.append("### Configuration Conflicts\n")
                for conflict in cfg['conflicts'][:10]:
                    lines.append(f"#### `{conflict['file']}`\n")
                    lines.append(f"- **Key:** `{conflict['key']}`")
                    lines.append(f"- **Values:** {conflict['values']}\n")
        
        # Recommendations
        if 'recommendations' in results:
            lines.append("## Recommendations\n")
            for rec in results['recommendations']:
                lines.append(f"- {rec}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, results: Dict[str, Any]) -> str:
        """Generate JSON format report."""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'analysis_results': results
        }
        return json.dumps(report_data, indent=2)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML format report."""
        # Convert markdown to HTML (simplified version)
        markdown_report = self._generate_markdown_report(results)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Sheratan Version Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }}
        h3 {{ color: #888; }}
        code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        ul {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <pre>{markdown_report}</pre>
</body>
</html>"""
        return html
    
    def generate_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a brief summary of analysis results.
        
        Args:
            analysis_results: Dictionary containing analysis data
            
        Returns:
            Summary string
        """
        summary = analysis_results.get('summary', {})
        
        lines = [
            "Sheratan Version Comparison Summary:",
            f"  Versions: {summary.get('version_count', 0)}",
            f"  Total Files: {summary.get('total_files', 0)}",
            f"  Different Files: {summary.get('different_files', 0)}",
            f"  Conflicts: {summary.get('conflicts', 0)}"
        ]
        
        return "\n".join(lines)
