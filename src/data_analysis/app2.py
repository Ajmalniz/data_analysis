#!/usr/bin/env python3

import warnings
warnings.filterwarnings('ignore')
import os
import yaml
import time
from crewai import Agent, Task, Crew, LLM
from crewai_tools import FileReadTool
from dotenv import load_dotenv, find_dotenv
import matplotlib.pyplot as plt
import pandas as pd
import chainlit as cl

# Load environment variables
load_dotenv(find_dotenv())

# Configure LLM
llm = LLM(
    provider="google",  # Using Google's API
    model=os.getenv("MODEL"),  # Gemini Pro model
    api_key=os.getenv("GOOGLE_API_KEY"),  # Using Google API key from .env file
    temperature=0.5  # Add some creativity while keeping responses focused
)

# Create necessary directories
def ensure_directories():
    """Create necessary directories for the application."""
    dirs = ['./public/charts', './reports']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    # Clear any existing charts to prevent confusion
    clear_charts()

def clear_charts():
    """Clear existing chart files."""
    charts_dir = './public/charts'
    if os.path.exists(charts_dir):
        for file in os.listdir(charts_dir):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                try:
                    os.remove(os.path.join(charts_dir, file))
                except Exception as e:
                    print(f"Error removing file {file}: {e}")

@cl.on_chat_start
async def start():
    """
    Initialize the chat session and welcome the user.
    """
    ensure_directories()
    await cl.Message(
        content="Welcome to the Data Analysis Assistant! Please provide your CSV file to begin the analysis."
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """
    Process incoming messages and handle CSV analysis.
    """
    # Check if a file was uploaded
    if not message.elements:
        await cl.Message(content="Please upload a CSV file to analyze.").send()
        return

    for element in message.elements:
        if element.name.endswith('.csv'):
            try:
                # Create a message for progress updates
                progress_msg = cl.Message(content="Starting analysis of your CSV file...")
                await progress_msg.send()
                
                # Process the CSV file and get the report
                report_path = run_crew(element.path)
                
                # Update progress
                await progress_msg.update(content="📊 Analyzing data and generating insights...")
                await cl.sleep(1)  # Small delay for UI updates
                
                await progress_msg.update(content="📈 Creating visualizations...")
                await cl.sleep(1)  # Small delay for UI updates
                
                await progress_msg.update(content="📝 Assembling final report...")
                await cl.sleep(1)  # Small delay for UI updates
                
                # Ensure the report file exists
                if not os.path.exists(report_path):
                    await cl.Message(content="⚠️ Report generation failed. Please try again.").send()
                    return
                
                # Read the generated report
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                # Get all generated charts
                charts_dir = './public/charts'
                chart_files = []
                if os.path.exists(charts_dir):
                    chart_files = [f for f in os.listdir(charts_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                
                # Create elements list for charts
                elements = []
                for chart_file in chart_files:
                    chart_path = os.path.join(charts_dir, chart_file)
                    elements.append(
                        cl.Image(path=chart_path, name=chart_file, display="inline")
                    )
                
                # Send completion message
                await progress_msg.update(content="✨ Analysis complete! Report generated successfully.")
                
                # Ensure the report content is properly formatted
                if not report_content or len(report_content.strip()) == 0:
                    await cl.Message(content="⚠️ The generated report appears to be empty. Please try again.").send()
                    return
                
                # Display the full report with charts
                report_message = cl.Message(
                    content=f"# 📊 Data Analysis Report\n\n{report_content}",
                    elements=elements
                )
                await report_message.send()
                
                # Send the report location and next steps
                await cl.Message(
                    content=f"""## 📋 Report Details
The full report has been saved to: `{report_path}`

## 🎯 Next Steps:
1. Review the detailed analysis above
2. Check the visualizations and insights
3. Implement the recommended actions
4. Download the full report from the provided location

Need any clarification or have questions about the analysis? Feel free to ask!"""
                ).send()
                
            except Exception as e:
                error_msg = f"""❌ Error processing the file:
```
{str(e)}
```
Please make sure the CSV file is properly formatted and try again."""
                await cl.Message(content=error_msg).send()
                import traceback
                print(traceback.format_exc())  # Print full error trace for debugging
            return

    await cl.Message(content="Please upload a valid CSV file.").send()

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define configuration file paths
agents_config_path = os.path.join(current_dir, 'config', 'agents.yaml')
tasks_config_path = os.path.join(current_dir, 'config', 'tasks.yaml')

# Load YAML configurations
with open(agents_config_path, 'r') as file:
    agents_config = yaml.safe_load(file)
with open(tasks_config_path, 'r') as file:
    tasks_config = yaml.safe_load(file)

# Custom tool for chart generation
class ChartGenerationTool:
    def __init__(self):
        self.name = "Chart Generator"
        self.description = "Generates charts from data and saves them as image files in the public/charts directory."

    def __call__(self, data_dict: dict, chart_type: str, title: str, x_label: str, y_label: str, filename: str):
        """
        Generate a chart from data and save it to the public/charts directory.
        Args:
            data_dict (dict): Dictionary containing the data to plot (will be converted to DataFrame)
            chart_type (str): Type of chart to generate ('bar', 'line', 'scatter', 'pie', etc.)
            title (str): Title of the chart
            x_label (str): Label for x-axis
            y_label (str): Label for y-axis
            filename (str): Name of the file to save the chart as
        Returns:
            str: Markdown-formatted string for embedding the chart in the report
        """
        try:
            # Convert dictionary to DataFrame
            data = pd.DataFrame.from_dict(data_dict)
            
            save_dir = './public/charts'
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
            
            plt.figure(figsize=(10, 6))  # Set a larger figure size
            
            # Handle different chart types
            if chart_type == "bar":
                data.plot(kind="bar")
            elif chart_type == "line":
                data.plot(kind="line")
            elif chart_type == "scatter":
                # For scatter plots, need at least two columns
                if len(data.columns) >= 2:
                    plt.scatter(data.iloc[:, 0], data.iloc[:, 1])
                else:
                    plt.scatter(range(len(data)), data.iloc[:, 0])
            elif chart_type == "pie":
                # For pie charts, use the first column as labels and the second as values
                if len(data.columns) >= 2:
                    plt.pie(data.iloc[:, 1], labels=data.iloc[:, 0], autopct='%1.1f%%')
                else:
                    plt.pie(data.iloc[:, 0], labels=data.index, autopct='%1.1f%%')
            else:
                # Default to bar chart if type is not recognized
                data.plot(kind="bar")
            
            plt.title(title, pad=20)  # Add some padding to the title
            plt.xlabel(x_label)
            plt.ylabel(y_label)
            plt.tight_layout()  # Adjust layout to prevent label cutoff
            plt.savefig(save_path, dpi=300, bbox_inches='tight')  # Higher resolution
            plt.close()
            
            # Return markdown for the image with correct path
            return f"![{title}](./charts/{filename})"
        except Exception as e:
            print(f"Error generating chart: {e}")
            return f"Error generating chart: {str(e)}"

    @property
    def func(self):
        return self.__call__

def run_crew(csv_path):
    """
    Process the CSV file and generate a report.
    Args:
        csv_path (str): Path to the CSV file.
    Returns:
        str: Path to the generated markdown report file.
    """
    # Initialize the CSV tool with the provided path
    csv_tool = FileReadTool(file_path=csv_path)
    
    # Create Agents with LLM configuration
    suggestion_generation_agent = Agent(
        config=agents_config['suggestion_generation_agent'],
        tools=[csv_tool],
        llm=llm
    )
    reporting_agent = Agent(
        config=agents_config['reporting_agent'],
        tools=[csv_tool],
        llm=llm
    )
    chart_tool = ChartGenerationTool()
    chart_generation_agent = Agent(
        config=agents_config['chart_generation_agent'],
        tools=[chart_tool],
        allow_code_execution=True,  # Allow code execution for chart generation
        llm=llm
    )
    
    # Create Tasks
    suggestion_generation = Task(
        config=tasks_config['suggestion_generation'],
        agent=suggestion_generation_agent
    )
    table_generation = Task(
        config=tasks_config['table_generation'],
        agent=reporting_agent
    )
    chart_generation = Task(
        config=tasks_config['chart_generation'],
        agent=chart_generation_agent
    )
    
    # Ensure the report directory exists
    os.makedirs('reports', exist_ok=True)
    
    # Define the report path
    report_path = os.path.join('reports', 'finalreport.md')
    
    # Create the final report assembly task
    final_report_assembly = Task(
        config=tasks_config['final_report_assembly'],
        agent=reporting_agent,
        context=[suggestion_generation, table_generation, chart_generation],
        output_file=report_path  # Specify the absolute output file path
    )
    
    # Create and configure Crew
    support_report_crew = Crew(
        agents=[suggestion_generation_agent, reporting_agent, chart_generation_agent],
        tasks=[suggestion_generation, table_generation, chart_generation, final_report_assembly],
        verbose=True
    )
    
    # Execute the crew
    result = support_report_crew.kickoff()
    
    # If the report wasn't automatically saved by the crew, save it manually
    if not os.path.exists(report_path):
        # Get timestamps for the report
        current_time = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get list of charts
        chart_list = []
        charts_dir = './public/charts'
        if os.path.exists(charts_dir):
            chart_list = [f for f in os.listdir(charts_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        # Create chart references
        chart_references = []
        for chart in chart_list:
            chart_references.append(f'![Chart: {chart}](./charts/{chart})')
        
        # Build the markdown report
        markdown_report = f"""# Data Analysis Report

## Executive Summary

{result}

## Data Analysis Insights

{suggestion_generation.output.raw if suggestion_generation.output else "No suggestions generated."}

## Data Visualization

The following charts show key metrics and trends from the analysis:

{chr(10).join(chart_references)}

## Key Findings and Tables

{table_generation.output.raw if table_generation.output else "No tables generated."}

## Recommendations

{chart_generation.output.raw if chart_generation.output else "No charts generated."}

## Generated on: {current_time}
"""
        # Save the report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
    
    # Give the file system a moment to catch up
    time.sleep(1)
    
    return report_path

if __name__ == "__main__":
    # For testing purposes with a hardcoded CSV
    csv_path = os.path.join(current_dir, 'support_tickets_data.csv')
    if os.path.exists(csv_path):
        result = run_crew(csv_path)
        print("\n=== Execution Result ===")
        print(result)
    else:
        print(f"Error: CSV file not found at {csv_path}")
