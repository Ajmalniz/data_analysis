#!/usr/bin/env python3

import warnings
warnings.filterwarnings('ignore')
import os
import yaml
import streamlit as st
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
            st.error(f"Configuration file not found at {file_path}. Please ensure 'agents.yaml' and 'tasks.yaml' are in the 'config' folder.")
            st.stop()
        except yaml.YAMLError as e:
            st.error(f"Error parsing YAML file {file_path}: {e}")
            st.stop()

agents_config = configs['agents']
tasks_config = configs['tasks']

# Streamlit UI
st.title("DataSmart Agent")

# File upload
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # Save the uploaded file temporarily
    with open(files['csv'], "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Initialize CSV tool
    csv_tool = FileReadTool(file_path=files['csv'])

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

    # Run the analysis
    with st.spinner("Analyzing data..."):
        result = analysis_crew.kickoff()

    # Display results
    st.success("Analysis complete!")
    
    # Read and display the generated markdown report
    if os.path.exists("finalreport.md"):
        with open("finalreport.md", "r") as f:
            report_content = f.read()
        st.markdown(report_content, unsafe_allow_html=True)
        
        # Provide download button
        st.download_button(
            label="Download Report",
            data=report_content,
            file_name="finalreport.md",
            mime="text/markdown"
        )
    else:
        st.error("Failed to generate the report. Please check the logs.")

    # Clean up temporary files
    if os.path.exists(files['csv']):
        os.remove(files['csv'])
    if os.path.exists("finalreport.md"):
        os.remove("finalreport.md")

else:
    st.info("Please upload a CSV file to begin the analysis.")