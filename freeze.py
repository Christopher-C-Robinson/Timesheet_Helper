#!/usr/bin/env python3
"""
freeze.py - Script to generate static files from Flask app for GitHub Pages deployment

This script uses Frozen-Flask to generate static HTML files from the Flask application
and creates a fully static version suitable for GitHub Pages deployment.
"""

import os
import shutil
from flask import Flask
from flask_frozen import Freezer
from app import app

# Create a static version of the app that serves the static template
static_app = Flask(__name__)

@static_app.route("/")
def index():
    """Serve the static version of the index page"""
    with open('templates/static_index.html', 'r') as f:
        return f.read()

def main():
    """Generate static site files for GitHub Pages deployment"""
    
    # Create freezer instance
    freezer = Freezer(static_app)
    
    # Configure output directory
    output_dir = 'docs'
    static_app.config['FREEZER_DESTINATION'] = output_dir
    static_app.config['FREEZER_RELATIVE_URLS'] = True
    
    # Clean existing output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    print(f"Generating static site in '{output_dir}/' directory...")
    
    # Generate static files
    freezer.freeze()
    
    print(f"Static site generated successfully!")
    print(f"Files created in '{output_dir}/' directory:")
    
    # List generated files
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, output_dir)
            print(f"  - {rel_path}")
    
    print(f"\nTo deploy to GitHub Pages:")
    print(f"1. Commit and push the '{output_dir}/' directory")
    print(f"2. Configure GitHub Pages to serve from the '{output_dir}/' directory")
    print(f"3. Your static site will be available at: https://USERNAME.github.io/REPOSITORY/")

if __name__ == "__main__":
    main()