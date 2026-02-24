#!/usr/bin/env python3
import argparse
import sys
import json

def main():
    parser = argparse.ArgumentParser(
        description="Agnostic utility for [Specific Transformation/Calculation]. "
                    "This script returns structured JSON for agent ingestion."
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Input data or path to the file to be processed."
    )
    parser.add_argument(
        "--mode", 
        choices=["extract", "transform", "validate"], 
        default="transform",
        help="Operation mode for the utility."
    )

    args = parser.parse_args()

    try:
        # AGNOSTIC LOGIC PLACEHOLDER
        # Perform calculation, data cleaning, or formatting here.
        result = {
            "status": "success",
            "processed_data": f"Result based on {args.input} in {args.mode} mode",
            "metadata": {"source": "helper_tool.py", "version": "1.0.0"}
        }
        
        # Output is ALWAYS structured JSON for the agent to parse
        print(json.dumps(result, indent=2))

    except Exception as e:
        error_output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_output, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
