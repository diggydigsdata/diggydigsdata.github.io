import os
from pathlib import Path

# --- Configuration ---
POSTS_DIR = 'posts'

# The YAML template to be written to each new index.qmd file
YAML_TEMPLATE = """---
title: "Title Placeholder"
author: "Diggy"
date: "YYYY-MM-DD"
description: "Description placeholder for this post."
image: "featured.jpg"
image-alt: "Image description"
categories: [Journalism]
---
"""
# ---------------------

def create_index_files(root_dir: str, template: str):
    """
    Loops through subdirectories in the root_dir and creates an index.qmd
    if one does not already exist.
    """
    print(f"Starting scan in: {root_dir}")
    
    # Convert the root directory string to a Path object for easier handling
    root_path = Path(root_dir)
    
    # Iterate through every item inside the root_dir
    for item in root_path.iterdir():
        # Check if the item is a directory AND not a hidden/system folder
        if item.is_dir() and not item.name.startswith('.'):
            
            # Define the full path for the index.qmd file
            index_file_path = item / "index.qmd"
            
            # Check if index.qmd already exists in the subdirectory
            if not index_file_path.exists():
                
                folder_title = item.name.replace('-', ' ').title()
                customized_template = template.replace('Title Placeholder', folder_title)
                
                try:
                    # Write the YAML content to the new file
                    index_file_path.write_text(customized_template, encoding='utf-8')
                    print(f"✅ Created: {index_file_path}")
                except Exception as e:
                    print(f"❌ Error creating {index_file_path}: {e}")
            else:
                print(f"➡️ Skipped: {item.name} (index.qmd already exists)")

if __name__ == "__main__":
    create_index_files(POSTS_DIR, YAML_TEMPLATE)