# Data Analysis Project

This project provides data analysis capabilities using Streamlit.

## Setup Instructions

1. **Set up Python Environment**
   - Make sure you have Python installed on your system
   - Install `uv` package manager if not already installed

2. **Install Dependencies**
   ```bash
   uv sync
   ```

3. **Activate Virtual Environment**
   ```bash
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

## Running the Application

1. Start the Streamlit application:
   ```bash
   chainlit  run src/data_analysis/app.py
   ```

2. The application will automatically open in your default web browser. If it doesn't, you can access it at `http://localhost:8000`

## Notes
- Make sure all dependencies are properly installed before running the application
- The application runs in watch mode by default, which means it will automatically reload when you make changes to the code
