import os
import json
from github import Github
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from datetime import datetime


class GitHubRepoInput(BaseModel):
    """Input schema for GitHubRepoTool."""
    repo_url: str = Field(..., description="The URL of the GitHub repository")
    operation: str = Field(default='analyze', description="The operation to perform ('analyze' or 'create_pr')")
    file_path: Optional[str] = Field(None, description="Path to the file for PR (used in create_pr operation)")
    content: Optional[str] = Field(None, description="Content of the file for PR (used in create_pr operation)")


class GitHubRepoTool(BaseTool):
    name: str = "GitHubRepoTool"
    description: str = (
        "Tool for analyzing GitHub repositories and creating pull requests."
    )
    args_schema: Type[BaseModel] = GitHubRepoInput

    def _run(self, repo_url: str, operation: str = 'analyze', file_path: str = None, content: str = None) -> str:
        """
        Execute the GitHub repository tool.
        
        Args:
            repo_url (str): The URL of the GitHub repository
            operation (str): The operation to perform ('analyze' or 'create_pr')
            file_path (str): Path to the file for PR (used in create_pr operation)
            content (str): Content of the file for PR (used in create_pr operation)
        
        Returns:
            str: JSON string containing results of the operation
        """
        try:
            # Extract owner and repo name from URL
            repo_path = repo_url.replace('https://github.com/', '')
            owner, repo_name = repo_path.split('/')
            
            # Get GitHub token from environment
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                return json.dumps({'error': 'GITHUB_TOKEN environment variable not set'})
            
            g = Github(github_token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            
            if operation == 'analyze':
                # Get repository contents
                contents = repo.get_contents("")
                analysis = {
                    'name': repo.name,
                    'description': repo.description or 'No description provided',
                    'language': repo.language,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'files': [],
                    'dependencies': {},
                    'topics': repo.get_topics()
                }
                
                # Analyze files
                for content_item in contents:
                    if content_item.type == 'file' and not content_item.name.lower() == 'readme.md':
                        analysis['files'].append({
                            'name': content_item.name,
                            'path': content_item.path,
                            'type': 'file',
                            'size': content_item.size
                        })
                    elif content_item.type == 'dir':
                        analysis['files'].append({
                            'name': content_item.name,
                            'path': content_item.path,
                            'type': 'dir'
                        })
                
                # Check for common dependency files
                for dep_file in ['requirements.txt', 'package.json', 'pom.xml', 'Cargo.toml', 'go.mod']:
                    try:
                        dep_content = repo.get_contents(dep_file)
                        analysis['dependencies'][dep_file] = dep_content.decoded_content.decode()
                    except:
                        pass
                return json.dumps(analysis)
                
            elif operation == 'create_pr' and file_path and content:
                # Create a new branch
                try:
                    source_branch = repo.get_branch("main")
                except:
                    # If main doesn't exist, try master
                    try:
                        source_branch = repo.get_branch("master")
                    except:
                        return json.dumps({'error': 'Could not find main or master branch'})
                
                new_branch = f"add-readme-{int(datetime.now().timestamp())}"
                repo.create_git_ref(
                    ref=f"refs/heads/{new_branch}",
                    sha=source_branch.commit.sha
                )
                
                # Create or update README file
                try:
                    existing_file = repo.get_contents("README.md", ref=new_branch)
                    repo.update_file(
                        "README.md",
                        "Update README.md",
                        content,
                        existing_file.sha,
                        branch=new_branch
                    )
                except:
                    repo.create_file(
                        "README.md",
                        "Add README.md",
                        content,
                        branch=new_branch
                    )
                
                # Create pull request
                pr = repo.create_pull(
                    title="Add/Update README.md",
                    body="Automatically generated README file using CrewAI",
                    head=new_branch,
                    base=source_branch.name
                )
                
                # Ensure proper JSON formatting
                return json.dumps({
                    'success': True, 
                    'pr_url': pr.html_url, 
                    'pr_number': pr.number
                })
                
            return json.dumps({'error': 'Invalid operation or missing parameters'})
            
        except Exception as e:
            return json.dumps({'error': str(e)})