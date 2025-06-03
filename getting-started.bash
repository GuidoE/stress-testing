# Create project
mkdir equity-option-stress-testing
cd equity-option-stress-testing

# Initialize git
git init

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create the directory structure
mkdir -p stress_testing/{core,calculators,engine,scenarios,instruments,pricing,utils,visualization}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p {docs,examples,notebooks,scripts}

# Install in development mode
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install