#!/usr/bin/env python3
"""
Utility script to initialize the standard folder structure for a new skill.
This script handles the mkdir -p logic for the 5 required subfolders.
"""
import argparse
import json
import os
import sys
from pathlib import Path

def create_folders(skill_path: Path) -> dict:
    """Create all required subdirectories for a skill."""
    required_dirs = [
        "advanced",
        "examples",
        "references",
        "scripts",
        ".workdir/tasks"
    ]
    
    results = {
        "status": "success",
        "created": [],
        "errors": []
    }
    
    for dir_path in required_dirs:
        full_path = skill_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            results["created"].append(str(dir_path))
        except Exception as e:
            results["errors"].append({
                "path": str(dir_path),
                "error": str(e)
            })
            results["status"] = "partial"
    
    if results["errors"]:
        results["status"] = "error"
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Initialize folder structure for a new skill. "
                    "Returns structured JSON for agent ingestion."
    )
    parser.add_argument(
        "--skill-path",
        required=True,
        help="Path to the skill directory (absolute or relative to repo root)."
    )
    
    args = parser.parse_args()
    
    skill_path = Path(args.skill_path).resolve()
    
    try:
        results = create_folders(skill_path)
        
        # Output is ALWAYS structured JSON for the agent to parse
        print(json.dumps(results, indent=2))
        
        if results["status"] == "error":
            sys.exit(1)
            
    except Exception as e:
        error_output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_output, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
