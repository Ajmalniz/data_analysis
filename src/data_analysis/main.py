#!/usr/bin/env python3

import warnings
warnings.filterwarnings('ignore')
import os
import yaml
from crewai import Agent, Task, Crew
from crewai_tools import FileReadTool
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define file paths
files = {
    'agents': os.path.join(current_dir, 'config', 'agents.yaml'),
    'tasks': os.path.join(current_dir, 'config', 'tasks.yaml'),
    'csv': os.path.join(current_dir, 'data.csv')
}

# Load YAML configurations
configs = {}
for config_type, file_path in files.items():
    if config_type != 'csv':
        try:
            with open(file_path, 'r') as file:
                configs[config_type] = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {file_path}")
            exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {file_path}: {e}")
            exit(1)

agents_config = configs['agents']
tasks_config = configs['tasks']

# Initialize CSV tool
csv_path = files['csv']
if not os.path.exists(csv_path):
    print(f"Error: CSV file not found at {csv_path}")
    exit(1)

csv_tool = FileReadTool(file_path=csv_path)

def main():    
    # Create Agents
    suggestion_agent = Agent(
        config=agents_config['suggestion_generation_agent'],
        tools=[csv_tool]
    )

    reporting_agent = Agent(
        config=agents_config['reporting_agent'],
        tools=[csv_tool]
    )

    chart_agent = Agent(
        config=agents_config['chart_generation_agent'],
        allow_code_execution=False
    )

    # Create Tasks
    suggestion_task = Task(
        config=tasks_config['suggestion_generation'],
        agent=suggestion_agent
    )

    table_task = Task(
        config=tasks_config['table_generation'],
        agent=reporting_agent
    )

    chart_task = Task(
        config=tasks_config['chart_generation'],
        agent=chart_agent
    )

    report_task = Task(
        config=tasks_config['final_report_assembly'],
        agent=reporting_agent,
        context=[suggestion_task, table_task, chart_task],
        output_file='finalreport.md'
    )

    # Create Crew
    analysis_crew = Crew(
        agents=[suggestion_agent, reporting_agent, chart_agent],
        tasks=[suggestion_task, table_task, chart_task, report_task],
        verbose=True
    )

    # Execute
    print("Starting analysis...")
    result = analysis_crew.kickoff()
    print("\n=== Analysis Complete ===")
    print("Report saved as 'finalreport.md'")
    print(result.raw)

if __name__ == "__main__":
    main()