#!/usr/bin/env python3
"""
Fresh start script for the Supervity AP Command Center.
This script:
1. Clears the database
2. Initializes configuration data
3. Starts the application server

Usage:
    python run_fresh.py [--reset]
    
Options:
    --reset    Perform a full database reset (drop and recreate tables)
"""

import os
import sys
import subprocess
import time

def run_script(script_path, args=None):
    """Run a Python script and wait for it to complete."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"🔧 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"❌ Script failed with return code {result.returncode}")
        sys.exit(1)
    print(f"✅ Completed: {script_path}")

def main():
    """Main function to orchestrate the fresh start process."""
    print("🚀 SUPERVITY AP COMMAND CENTER - FRESH START")
    print("=" * 50)
    print("This will:")
    print("1. Clean the database")
    print("2. Initialize configuration data")
    print("3. Start the application server")
    print("=" * 50)
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Define script paths
    cleanup_script = os.path.join(project_root, "scripts", "cleanup_db.py")
    init_config_script = os.path.join(project_root, "scripts", "init_config_data.py")
    run_script_path = os.path.join(project_root, "run.py")
    
    # Check if --reset flag is passed
    reset_args = []
    if "--reset" in sys.argv:
        reset_args = ["--reset"]
        print("⚠️ Full database reset mode enabled")
    
    try:
        # Step 1: Clean/Reset the database
        print("\n📝 STEP 1: Database Cleanup")
        print("-" * 30)
        run_script(cleanup_script, reset_args)
        
        # Step 2: Initialize configuration data
        print("\n📝 STEP 2: Initialize Configuration")
        print("-" * 30)
        run_script(init_config_script)
        
        # Step 3: Start the application
        print("\n📝 STEP 3: Starting Application")
        print("-" * 30)
        print("🎉 Database is clean and configured!")
        print("🚀 Starting the Supervity AP Command Center server...")
        print("\n" + "=" * 50)
        
        # Run the main application (this will block)
        os.execv(sys.executable, [sys.executable, run_script_path])
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during fresh start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 