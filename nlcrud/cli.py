#!/usr/bin/env python
"""
Command-line interface for the NLCRUD application.
Includes warning suppression and enhanced options.
"""
import argparse
import os
import sys
import warnings
import logging
import uvicorn

# Configure logging to suppress specific error messages
logging.basicConfig(level=logging.INFO)

# Create a filter for the root logger to filter out blake2 hash errors
class HashLibFilter(logging.Filter):
    def filter(self, record):
        if record.levelno == logging.ERROR and "code for hash blake2" in record.getMessage():
            return False
        return True

# Apply the filter to the root logger
logging.getLogger('root').addFilter(HashLibFilter())

# Suppress all warnings by default
warnings.filterwarnings("ignore")

# Redirect stderr to suppress specific error messages
class StderrFilter:
    def __init__(self):
        self.original_stderr = sys.stderr
        self.filtered_lines = ["code for hash blake2b was not found",
                              "code for hash blake2s was not found",
                              "unsupported hash type blake2"]
    
    def write(self, text):
        if not any(line in text for line in self.filtered_lines):
            self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()

# Redirect stdout to filter out specific error messages
class StdoutFilter:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.filtered_phrases = [
            "Error during prediction: Unable to avoid copy while creating an array as requested",
            "If using `np.array(obj, copy=False)` replace it with `np.asarray(obj)`",
            "For more details, see https://numpy.org/devdocs/numpy_2_0_migration_guide.html",
            "Using rule-based fallback"
        ]
    
    def write(self, text):
        if not any(phrase in text for phrase in self.filtered_phrases):
            self.original_stdout.write(text)
    
    def flush(self):
        self.original_stdout.flush()

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Natural Language CRUD Engine")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("serve", help="Run the API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    server_parser.add_argument("--extractor", choices=["regex", "spacy"], default="spacy",
                               help="Entity extractor to use (regex or spacy)")
    server_parser.add_argument("--show-warnings", action="store_true",
                               help="Show all warnings (default: warnings are suppressed)")
    server_parser.add_argument("--log-level", default="info",
                               choices=["debug", "info", "warning", "error", "critical"],
                               help="Set the logging level")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run the test suite")
    test_parser.add_argument("--show-warnings", action="store_true",
                             help="Show all warnings (default: warnings are suppressed)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "serve":
        # Set environment variable for extractor choice
        if args.extractor == "regex":
            os.environ["USE_REGEX_EXTRACTOR"] = "true"
        else:
            os.environ.pop("USE_REGEX_EXTRACTOR", None)
        
        # Apply warning suppression unless explicitly disabled
        original_stderr = None
        if not args.show_warnings:
            # Apply the stderr filter to suppress specific warnings
            original_stderr = sys.stderr
            sys.stderr = StderrFilter()
        
        try:
            # Run the server
            uvicorn.run(
                "nlcrud.api.app:app",
                host=args.host,
                port=args.port,
                reload=args.reload,
                log_level=args.log_level
            )
        finally:
            # Restore original stderr if it was changed
            if original_stderr:
                sys.stderr = original_stderr
    elif args.command == "test":
        # Apply stdout filter to suppress NumPy warnings
        if not args.show_warnings:
            sys.stdout = StdoutFilter()
            
        try:
            # Import and run the tests
            from test_nlcrud import run_tests
            run_tests()
        finally:
            # Restore original stdout
            if not args.show_warnings:
                sys.stdout = sys.stdout.original_stdout
    else:
        # If no command is provided, show help
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()