# NCore - Streaming

## Prerequisites

The project requires **Peerflix** for torrent streaming.

### Peerflix Installation

Install Peerflix globally using npm:

    npm install -g peerflix

## Installation

### 1. Create a Python virtual environment

    python -m venv .venv

### 2. Activate the virtual environment

    source .venv/bin/activate

### 3. Install Python dependencies

    pip install -r requirements.txt

### 4. Create `config.py`

Create a `config.py` file in the project root directory.

An example configuration is provided in the repository. Use the provided example as a template and fill in your own credentials and configuration values.

## Usage

Start the application with:

    python main.py