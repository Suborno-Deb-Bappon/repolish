from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from repolish.tools.custom_tool import GitHubRepoTool
import os
import json
import ast

@CrewBase
class ReadmeGeneratorCrew():
    """ReadmeGeneratorCrew for generating README files"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.github_tool = GitHubRepoTool()
        os.makedirs('output', exist_ok=True)

    @agent
    def repo_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['repo_analyzer'],
            tools=[self.github_tool],
            verbose=True
        )

    @agent
    def content_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['content_generator'],
            verbose=True
        )

    @agent
    def readme_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['readme_formatter'],
            verbose=True
        )

    @agent
    def pr_handler(self) -> Agent:
        return Agent(
            config=self.agents_config['pr_handler'],
            tools=[self.github_tool],
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=500,
            max_retry_limit=3
        )

    @task
    def analyze_repo_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_repo_task'],
            agent=self.repo_analyzer(),
            output_file='output/repo_analysis.json'
        )

    @task
    def generate_content_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_content_task'],
            agent=self.content_generator(),
            context=[self.analyze_repo_task()],
            output_file='output/readme_content.txt'
        )

    @task
    def format_readme_task(self) -> Task:
        return Task(
            config=self.tasks_config['format_readme_task'],
            agent=self.readme_formatter(),
            context=[self.generate_content_task()],
            output_file='output/README.md'
        )

    @task
    def create_pr_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_pr_task'],
            agent=self.pr_handler()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the README generator crew"""
        return Crew(
            agents=[
                self.repo_analyzer(),
                self.content_generator(),
                self.readme_formatter()
            ],
            tasks=[
                self.analyze_repo_task(),
                self.generate_content_task(),
                self.format_readme_task()
            ],
            process=Process.sequential,
            verbose=True
        )
    

    def create_pr(self, repo_url, readme_content):
        """Handle PR creation using the PR agent directly"""
        pr_agent = self.pr_handler()
        inputs = {
            'repo_url': repo_url,
            'operation': 'create_pr',
            'file_path': 'README.md',
            'content': readme_content
        }
        result = pr_agent.execute_task(self.create_pr_task(), inputs)
        
        # Handle different response formats
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            try:
                # Try JSON first
                return json.loads(result)
            except json.JSONDecodeError:
                try:
                    # Fall back to safe Python literal eval
                    return ast.literal_eval(result)
                except Exception:
                    return {'error': f"Unrecognized response format: {result}"}
        else:
            return {'error': f"Unexpected response type: {type(result)}"}