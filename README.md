# Data Analysis Project

## Overview
A Streamlit-based data analysis application.

## Installation

### Prerequisites
- Python (latest stable version recommended)
- UV package manager

### Clone the Repository
```bash
git clone https://github.com/Ajmalniz/data_analysis.git
```

### Setup Environment
1. Install dependencies using UV:
   ```bash
   uv sync
   ```

2. Activate the virtual environment:
   ```bash
   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

## Running the Application

### Method 1: Using UV
```bash
uv run kickoff
```

### Method 2: Using Streamlit Directly
```bash
streamlit run src/data_analysis/app.py
```

The application will open automatically in your default web browser.
Default URL: `http://localhost:8501/`

## Development Notes
- Application runs in watch mode
- Changes to code will trigger automatic reload
- Ensure all dependencies are installed before running
