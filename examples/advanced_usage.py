"""
Advanced usage examples.
Demonstrates the advanced capabilities of Deep Search Agent.
"""

import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import DeepSearchAgent, Config
from src.utils.config import print_config


def advanced_example():
    """Advanced usage example."""
    print("=" * 60)
    print("Deep Search Agent - Advanced Usage Example")
    print("=" * 60)
    
    try:
        # Custom configuration
        print("Creating custom configuration...")
        config = Config(
            # Use OpenAI instead of DeepSeek
            default_llm_provider="openai",
            openai_model="gpt-4o-mini",
            # Custom search parameters
            max_search_results=5,  # More search results
            max_reflections=3,     # More reflection rounds
            max_content_length=15000,
            # Custom output settings
            output_dir="custom_reports",
            save_intermediate_states=True
        )
        
        # Set API keys from environment variables
        config.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        if not config.validate():
            print("Configuration validation failed. Check your API key settings.")
            return
        
        print_config(config)
        
        # Create the agent
        print("Initializing agent...")
        agent = DeepSearchAgent(config)
        
        # Run multiple research tasks
        queries = [
            "Applications of deep learning in healthcare",
            "Latest developments in blockchain technology",
            "Sustainable energy technology trends"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"Running research task {i}/{len(queries)}: {query}")
            print(f"{'='*60}")
            
            try:
                # Run the research
                final_report = agent.research(query, save_report=True)
                
                # Save state for demonstration
                state_file = f"custom_reports/state_task_{i}.json"
                agent.save_state(state_file)
                
                print(f"Task {i} completed")
                print(f"Report length: {len(final_report)} characters")
                
                # Show progress
                progress = agent.get_progress_summary()
                print(f"Progress: {progress['progress_percentage']:.1f}%")
                
            except Exception as e:
                print(f"Task {i} failed: {str(e)}")
                continue
        
        print(f"\n{'='*60}")
        print("All research tasks completed!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Advanced example failed: {str(e)}")


def state_management_example():
    """State management example."""
    print("\n" + "=" * 60)
    print("State Management Example")
    print("=" * 60)
    
    try:
        # Create configuration
        config = Config.from_env()
        if not config.validate():
            print("Configuration validation failed")
            return
        
        # Create the agent
        agent = DeepSearchAgent(config)
        
        query = "Current state of quantum computing development"
        print(f"Starting research: {query}")
        
        # Run the research
        final_report = agent.research(query)
        
        # Save state
        state_file = "custom_reports/quantum_computing_state.json"
        agent.save_state(state_file)
        print(f"State saved to: {state_file}")
        
        # Create a new agent and load the saved state
        print("\nCreating a new agent and loading state...")
        new_agent = DeepSearchAgent(config)
        new_agent.load_state(state_file)
        
        # Check the loaded state
        progress = new_agent.get_progress_summary()
        print("Loaded state information:")
        print(f"- Query: {new_agent.state.query}")
        print(f"- Report title: {new_agent.state.report_title}")
        print(f"- Paragraph count: {progress['total_paragraphs']}")
        print(f"- Completion status: {progress['is_completed']}")
        
    except Exception as e:
        print(f"State management example failed: {str(e)}")


if __name__ == "__main__":
    advanced_example()
    state_management_example()
