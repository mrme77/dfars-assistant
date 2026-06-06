"""Hugging Face Spaces entry point for the DFARS Streamlit app."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).parent / "app"
sys.path.insert(0, str(APP_DIR))

from streamlit_app import main


if __name__ == "__main__":
    main()
