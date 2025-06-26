[version]: 0.0.1
 
# First start
  *Create virtual env for python*
    python3 -m venv .venv

  *Install dependencies*
    source .venv/bin/activate
    pip install -r requirements.txt

  *Check if it's working*
    python3 examples/test_gtw_emulator.py

# Create requirements.txt
  pip freeze > requirements.txt

# Active virtual enviroment
  source .venv/bin/activate

# Install all dependecies
  pip install .