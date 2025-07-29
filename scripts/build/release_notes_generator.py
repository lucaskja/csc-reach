#!/usr/bin/env python3
"""
Release Notes Generator for CSC-Reach
Automatically generates release notes from git history, issues, and pull requests
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


class ReleaseNotesGenerator:
    """Generates comprehensive release notes for CSC-Reach releases."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the release notes generator."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_url = self._get_repo_url()
        
    def _get_repo_url(self) -> Optional[str]:
        """Get repository URL from git remote."""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                url = result.stdout.strip()
                # Convert SSH to HTTPS format
                if url.startswith('git@github.com:'):
                    url = url.replace('git@github.com:', 'https://github.com/')
                if url.endswith('.git'):
                    url = url[:-4]
                return url
        except Exception:
            pass
        
        return None
    
    def get_commits_since_tag(self, since_tag: Optional[str] = None) -> List[Dict[str, str]]:
        """Get commits since the last tag or specified tag."""
        try:
            # Get the last tag if not specified
            if not since_tag:
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--abbrev=0'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if result.returncode == 0:
                    since_tag = result.stdout.strip()
                else:
                    # If no tags, get commits from last week
                    since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    git_range = f'--since="{since_date}"'
            
            if since_tag:
                git_range = f'{since_tag}..HEAD'
            
            # Get commit log
            result = subprocess.run([
                'git', 'log', git_range,
                '--pretty=format:%H|%s|%an|%ad|%b',
                '--date=short'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                    
                parts = line.split('|', 4)
                if len(parts) >= 4:
                    commits.append({
                        'hash': parts[0][:8],
                        'subject': parts[1],
                        'author': parts[2],
                        'date': parts[3],
                        'body': parts[4] if len(parts) > 4 else ''
                    })
            
            return commits
            
        except Exception as e:
            print(f"Warning: Could not get git commits: {e}")
            return []
    
    def categorize_commits(self, commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Categorize commits by type."""
        categories = {
            'features': [],
            'fixes': [],
            'improvements': [],
            'docs': [],
            'tests': [],
            'build': [],
            'other': []
        }
        
        # Patterns for categorization
        patterns = {
            'features': [r'^feat', r'^add', r'^implement', r'new feature', r'feature:'],
            'fixes': [r'^fix', r'^bug', r'fix:', r'bugfix', r'hotfix'],
            'improvements': [r'^improve', r'^enhance', r'^update', r'^refactor', r'improvement:'],
            'docs': [r'^docs?', r'documentation', r'readme', r'doc:'],
            'tests': [r'^test', r'testing', r'spec:', r'test:'],
            'build': [r'^build', r'^ci', r'workflow', r'pipeline', r'build:']
        }
        
        for commit in commits:
            subject_lower = commit['subject'].lower()
            categorized = False
            
            for category, category_patterns in patterns.items():
                for pattern in category_patterns:
                    if re.search(pattern, subject_lower):
                        categories[category].append(commit)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                categories['other'].append(commit)
        
        return categories
    
    def get_github_issues_and_prs(self, since_date: str) -> Tuple[List[Dict], List[Dict]]:
        """Get closed issues and merged PRs from GitHub API."""
        if not self.github_token or not self.repo_url:
            return [], []
        
        try:
            # Extract owner/repo from URL
            parts = self.repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return [], []
            
            owner, repo = parts[0], parts[1]
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get closed issues
            issues_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
            issues_params = {
                'state': 'closed',
                'since': since_date,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            issues_response = requests.get(issues_url, headers=headers, params=issues_params)
            issues = issues_response.json() if issues_response.status_code == 200 else []
            
            # Separate issues and PRs
            actual_issues = [issue for issue in issues if 'pull_request' not in issue]
            pull_requests = [issue for issue in issues if 'pull_request' in issue]
            
            return actual_issues, pull_requests
            
        except Exception as e:
            print(f"Warning: Could not fetch GitHub data: {e}")
            return [], []
    
    def generate_release_notes(
        self, 
        version: str, 
        release_type: str = "production",
        since_tag: Optional[str] = None,
        include_github_data: bool = True
    ) -> str:
        """Generate comprehensive release notes."""
        
        # Get commits
        commits = self.get_commits_since_tag(since_tag)
        categorized_commits = self.categorize_commits(commits)
        
        # Get GitHub data if available
        issues, prs = [], []
        if include_github_data:
            since_date = (datetime.now() - timedelta(days=30)).isoformat()
            issues, prs = self.get_github_issues_and_prs(since_date)
        
        # Start building release notes
        notes = f"""# CSC-Reach {version}

## 🚀 What's New

This release includes {len(commits)} commits with new features, improvements, and bug fixes.

"""
        
        # Add features section
        if categorized_commits['features']:
            notes += "## ✨ New Features\n\n"
            for commit in categorized_commits['features']:
                notes += f"- {commit['subject']} ({commit['hash']})\n"
            notes += "\n"
        
        # Add improvements section
        if categorized_commits['improvements']:
            notes += "## 🔧 Improvements\n\n"
            for commit in categorized_commits['improvements']:
                notes += f"- {commit['subject']} ({commit['hash']})\n"
            notes += "\n"
        
        # Add bug fixes section
        if categorized_commits['fixes']:
            notes += "## 🐛 Bug Fixes\n\n"
            for commit in categorized_commits['fixes']:
                notes += f"- {commit['subject']} ({commit['hash']})\n"
            notes += "\n"
        
        # Add documentation updates
        if categorized_commits['docs']:
            notes += "## 📚 Documentation\n\n"
            for commit in categorized_commits['docs']:
                notes += f"- {commit['subject']} ({commit['hash']})\n"
            notes += "\n"
        
        # Add build/CI improvements
        if categorized_commits['build']:
            notes += "## 🏗️ Build & CI\n\n"
            for commit in categorized_commits['build']:
                notes += f"- {commit['subject']} ({commit['hash']})\n"
            notes += "\n"
        
        # Add GitHub Issues if available
        if issues:
            notes += "## 🎯 Closed Issues\n\n"
            for issue in issues[:10]:  # Limit to 10 most recent
                notes += f"- #{issue['number']}: {issue['title']}\n"
            if len(issues) > 10:
                notes += f"- ... and {len(issues) - 10} more issues\n"
            notes += "\n"
        
        # Add merged PRs if available
        if prs:
            notes += "## 🔀 Merged Pull Requests\n\n"
            for pr in prs[:10]:  # Limit to 10 most recent
                notes += f"- #{pr['number']}: {pr['title']}\n"
            if len(prs) > 10:
                notes += f"- ... and {len(prs) - 10} more pull requests\n"
            notes += "\n"
        
        # Add download section
        notes += """## 📦 Downloads

Choose the appropriate download for your operating system:

### Windows
- **CSC-Reach-Windows.zip** - Complete Windows application package
  - Extract to your desired location
  - Run `CSC-Reach.exe` to start the application

### macOS
- **CSC-Reach-macOS.dmg** - macOS installer package
  - Double-click to mount the disk image
  - Drag CSC-Reach.app to your Applications folder

## 🔧 System Requirements

### Windows
- Windows 10 or later (64-bit)
- Microsoft Outlook installed and configured
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space

### macOS
- macOS 10.14 (Mojave) or later
- Microsoft Outlook for Mac installed and configured
- 4GB RAM minimum, 8GB recommended
- 500MB free disk space

## 📋 Installation Instructions

### First-time Installation
1. Download the appropriate package for your operating system
2. Follow the platform-specific installation steps above
3. Launch CSC-Reach and complete the initial setup wizard
4. Configure your Outlook integration and messaging preferences

### Upgrading from Previous Version
1. Close CSC-Reach if it's currently running
2. Download and install the new version
3. Your settings and templates will be preserved automatically

## 🆕 What's Changed Since Last Release

"""
        
        # Add summary of changes
        total_changes = sum(len(commits) for commits in categorized_commits.values())
        notes += f"- **{len(categorized_commits['features'])}** new features\n"
        notes += f"- **{len(categorized_commits['improvements'])}** improvements\n"
        notes += f"- **{len(categorized_commits['fixes'])}** bug fixes\n"
        notes += f"- **{len(categorized_commits['docs'])}** documentation updates\n"
        notes += f"- **{total_changes}** total changes\n\n"
        
        # Add support section
        notes += """## 🆘 Support

If you encounter any issues:

1. Check the [User Manual](docs/user/user_manual.md) for common solutions
2. Review the [Troubleshooting Guide](docs/user/troubleshooting_guide.md)
3. Search existing [GitHub Issues](""" + (self.repo_url + "/issues" if self.repo_url else "#") + """)
4. Create a new issue if your problem isn't already reported

## 🙏 Contributors

Thank you to all contributors who made this release possible!

"""
        
        # Add contributor list
        contributors = set()
        for commit in commits:
            contributors.add(commit['author'])
        
        if contributors:
            for contributor in sorted(contributors):
                notes += f"- {contributor}\n"
            notes += "\n"
        
        # Add build information
        notes += f"""---

**Release Information:**
- **Version:** {version}
- **Release Type:** {release_type.title()}
- **Build Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
- **Total Commits:** {len(commits)}
"""
        
        # Add environment info if available
        if os.environ.get('GITHUB_RUN_ID'):
            notes += f"- **GitHub Workflow:** [{os.environ.get('GITHUB_RUN_ID')}]({self.repo_url}/actions/runs/{os.environ.get('GITHUB_RUN_ID')})\n"
        
        if os.environ.get('GITHUB_SHA'):
            commit_hash = os.environ.get('GITHUB_SHA')[:8]
            notes += f"- **Commit:** [{commit_hash}]({self.repo_url}/commit/{os.environ.get('GITHUB_SHA')})\n"
        
        return notes
    
    def save_release_notes(self, notes: str, output_file: Path) -> bool:
        """Save release notes to file."""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(notes)
            return True
        except Exception as e:
            print(f"Error saving release notes: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate release notes for CSC-Reach")
    parser.add_argument("--version", required=True, help="Version for the release")
    parser.add_argument("--release-type", choices=["development", "staging", "production"],
                       default="production", help="Type of release")
    parser.add_argument("--since-tag", help="Generate notes since this tag")
    parser.add_argument("--output", type=Path, help="Output file for release notes")
    parser.add_argument("--no-github", action="store_true", 
                       help="Skip GitHub API calls for issues/PRs")
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = ReleaseNotesGenerator()
    
    # Generate release notes
    notes = generator.generate_release_notes(
        args.version,
        args.release_type,
        args.since_tag,
        not args.no_github
    )
    
    # Output or save
    if args.output:
        if generator.save_release_notes(notes, args.output):
            print(f"✅ Release notes saved to {args.output}")
        else:
            print("❌ Failed to save release notes")
            return 1
    else:
        print(notes)
    
    return 0


if __name__ == "__main__":
    exit(main())