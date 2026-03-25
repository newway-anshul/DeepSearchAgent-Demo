"""
Basic usage example.
Shows how to use Deep Search Agent for a basic deep search workflow.
"""

import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import DeepSearchAgent, load_config
from src.utils.config import print_config


def basic_example():
    """Basic usage example."""
    print("=" * 60)
    print("Deep Search Agent - Basic Usage Example")
    print("=" * 60)
    
    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config()
        print_config(config)
        
        # Create the agent
        print("Initializing agent...")
        agent = DeepSearchAgent(config)
        
        # Run the research
        query = "AI development trends in 2025"
        print(f"Starting research: {query}")
        
        final_report = agent.research(query, save_report=True)
        
        # Show results
        print("\n" + "=" * 60)
        print("Research complete. Final report preview:")
        print("=" * 60)
        print(final_report[:500] + "..." if len(final_report) > 500 else final_report)
        
        # Show progress information
        progress = agent.get_progress_summary()
        print(f"\nProgress information:")
        print(f"- Total paragraphs: {progress['total_paragraphs']}")
        print(f"- Completed paragraphs: {progress['completed_paragraphs']}")
        print(f"- Progress: {progress['progress_percentage']:.1f}%")
        print(f"- Completed: {progress['is_completed']}")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")
        print("Please check:")
        print("1. Whether all dependencies are installed: pip install -r requirements.txt")
        print("2. Whether the required API keys are set")
        print("3. Whether the network connection is working")
        print("4. Whether the configuration file is correct")


if __name__ == "__main__":
    basic_example()
