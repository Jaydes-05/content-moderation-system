#!/usr/bin/env python3
"""
Package ContentGuard extension for Microsoft Edge Add-ons submission
"""

import zipfile
import os
from pathlib import Path

def create_extension_package():
    """Create a ZIP package of the extension for Edge Add-ons store"""
    
    # Files to include in the package
    files_to_include = [
        'manifest.json',
        'background.js',
        'content.js',
        'panel.css',
        'popup.html',
        'popup.js',
        'icons/icon16.png',
        'icons/icon48.png',
        'icons/icon128.png',
    ]
    
    extension_dir = Path('extension')
    output_zip = 'contentguard-extension.zip'
    
    # Remove old zip if exists
    if os.path.exists(output_zip):
        os.remove(output_zip)
        print(f"✓ Removed old {output_zip}")
    
    # Create new zip
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_include:
            full_path = extension_dir / file_path
            if full_path.exists():
                # Add file to zip with relative path (no 'extension/' prefix)
                zipf.write(full_path, file_path)
                print(f"✓ Added: {file_path}")
            else:
                print(f"✗ Missing: {file_path}")
    
    # Get file size
    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    
    print(f"\n{'='*50}")
    print(f"✅ Package created: {output_zip}")
    print(f"📦 Size: {size_mb:.2f} MB")
    print(f"{'='*50}")
    print("\nNext steps:")
    print("1. Go to: https://partner.microsoft.com/dashboard/microsoftedge")
    print("2. Sign in with your Microsoft account")
    print("3. Click 'New submission'")
    print(f"4. Upload: {output_zip}")
    print("5. Fill in store listing details")
    print("6. Submit for review!")
    print("\nSee extension/EDGE_PUBLISHING_GUIDE.md for detailed instructions.")

if __name__ == '__main__':
    create_extension_package()
