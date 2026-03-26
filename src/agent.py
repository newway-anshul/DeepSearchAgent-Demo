"""
Deep Search Agent Main Class
Integrates all modules to implement the complete deep search workflow
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

from .llms import DeepSeekLLM, OpenAILLM, BaseLLM
from .nodes import (
    ReportStructureNode,
    FirstSearchNode, 
    ReflectionNode,
    FirstSummaryNode,
    ReflectionSummaryNode,
    ReportFormattingNode
)
from .state import State
from .tools import tavily_search
from .utils import Config, load_config, format_search_results_for_prompt


class DeepSearchAgent:
    """Deep Search Agent Main Class"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Deep Search Agent
        
        Args:
            config: Configuration object, auto-loaded if not provided
        """
        # Load configuration
        self.config = config or load_config()
        
        # Initialize LLM client
        self.llm_client = self._initialize_llm()
        
        # Initialize nodes
        self._initialize_nodes()
        
        # State
        self.state = State()
        
        # Ensure output directory exists
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        print(f"Deep Search Agent initialized")
        print(f"Using LLM: {self.llm_client.get_model_info()}")
    
    def _initialize_llm(self) -> BaseLLM:
        """Initialize LLM client"""
        if self.config.default_llm_provider == "deepseek":
            return DeepSeekLLM(
                api_key=self.config.deepseek_api_key,
                model_name=self.config.deepseek_model
            )
        elif self.config.default_llm_provider == "openai":
            return OpenAILLM(
                api_key=self.config.openai_api_key,
                model_name=self.config.openai_model
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.default_llm_provider}")
    
    def _initialize_nodes(self):
        """Initialize processing nodes"""
        self.first_search_node = FirstSearchNode(self.llm_client)
        self.reflection_node = ReflectionNode(self.llm_client)
        self.first_summary_node = FirstSummaryNode(self.llm_client)
        self.reflection_summary_node = ReflectionSummaryNode(self.llm_client)
        self.report_formatting_node = ReportFormattingNode(self.llm_client)
    
    def research(self, query: str, save_report: bool = True) -> str:
        """
        Execute deep research
        
        Args:
            query: Research query
            save_report: Whether to save the report to a file
            
        Returns:
            Final report content
        """
        print(f"\n{'='*60}")
        print(f"Starting deep research: {query}")
        print(f"{'='*60}")
        
        try:
            # Step 1: Generate report structure
            self._generate_report_structure(query)
            
            # Step 2: Process each paragraph
            self._process_paragraphs()
            
            # Step 3: Generate final report
            final_report = self._generate_final_report()
            
            # Step 4: Save report
            if save_report:
                self._save_report(final_report)
            
            print(f"\n{'='*60}")
            print("Deep research completed!")
            print(f"{'='*60}")
            
            return final_report
            
        except Exception as e:
            print(f"Error during research: {str(e)}")
            raise e
    
    def _generate_report_structure(self, query: str):
        """Generate report structure"""
        print(f"\n[Step 1] Generating report structure...")
        
        # Create report structure node
        report_structure_node = ReportStructureNode(self.llm_client, query)
        
        # Generate structure and update state
        self.state = report_structure_node.mutate_state(state=self.state)
        
        print(f"Report structure generated, total {len(self.state.paragraphs)} paragraphs:")
        for i, paragraph in enumerate(self.state.paragraphs, 1):
            print(f"  {i}. {paragraph.title}")
    
    def _process_paragraphs(self):
        """Process all paragraphs"""
        total_paragraphs = len(self.state.paragraphs)
        
        for i in range(total_paragraphs):
            print(f"\n[Step 2.{i+1}] Processing paragraph: {self.state.paragraphs[i].title}")
            print("-" * 50)
            
            # Initial search and summary
            self._initial_search_and_summary(i)
            
            # Reflection loop
            self._reflection_loop(i)
            
            # Mark paragraph as completed
            self.state.paragraphs[i].research.mark_completed()
            
            progress = (i + 1) / total_paragraphs * 100
            print(f"Paragraph processing completed ({progress:.1f}%)")
    
    def _initial_search_and_summary(self, paragraph_index: int):
        """Execute initial search and summary"""
        paragraph = self.state.paragraphs[paragraph_index]
        
        # Prepare search input
        search_input = {
            "title": paragraph.title,
            "content": paragraph.content
        }
        
        # Generate search query
        print("  - Generating search query...")
        search_output = self.first_search_node.run(search_input)
        search_query = search_output["search_query"]
        reasoning = search_output["reasoning"]
        
        print(f"  - Search query: {search_query}")
        print(f"  - Reasoning: {reasoning}")
        
        # Execute search
        print("  - Executing web search...")
        search_results = tavily_search(
            search_query,
            max_results=self.config.max_search_results,
            timeout=self.config.search_timeout,
            api_key=self.config.tavily_api_key
        )
        
        if search_results:
            print(f"  - Found {len(search_results)} search results")
            for j, result in enumerate(search_results, 1):
                print(f"    {j}. {result['title'][:50]}...")
        else:
            print("  - No search results found")
        
        # Update search history in state
        paragraph.research.add_search_results(search_query, search_results)
        
        # Generate initial summary
        print("  - Generating initial summary...")
        summary_input = {
            "title": paragraph.title,
            "content": paragraph.content,
            "search_query": search_query,
            "search_results": format_search_results_for_prompt(
                search_results, self.config.max_content_length
            )
        }
        
        # Update state
        self.state = self.first_summary_node.mutate_state(
            summary_input, self.state, paragraph_index
        )
        
        print("  - Initial summary completed")
    
    def _reflection_loop(self, paragraph_index: int):
        """Execute reflection loop"""
        paragraph = self.state.paragraphs[paragraph_index]
        
        for reflection_i in range(self.config.max_reflections):
            print(f"  - Reflection {reflection_i + 1}/{self.config.max_reflections}...")
            
            # Prepare reflection input
            reflection_input = {
                "title": paragraph.title,
                "content": paragraph.content,
                "paragraph_latest_state": paragraph.research.latest_summary
            }
            
            # Generate reflection search query
            reflection_output = self.reflection_node.run(reflection_input)
            search_query = reflection_output["search_query"]
            reasoning = reflection_output["reasoning"]
            
            print(f"    Reflection query: {search_query}")
            print(f"    Reflection reasoning: {reasoning}")
            
            # Execute reflection search
            search_results = tavily_search(
                search_query,
                max_results=self.config.max_search_results,
                timeout=self.config.search_timeout,
                api_key=self.config.tavily_api_key
            )
            
            if search_results:
                print(f"    Found {len(search_results)} reflection search results")
            
            # Update search history
            paragraph.research.add_search_results(search_query, search_results)
            
            # Generate reflection summary
            reflection_summary_input = {
                "title": paragraph.title,
                "content": paragraph.content,
                "search_query": search_query,
                "search_results": format_search_results_for_prompt(
                    search_results, self.config.max_content_length
                ),
                "paragraph_latest_state": paragraph.research.latest_summary
            }
            
            # Update state
            self.state = self.reflection_summary_node.mutate_state(
                reflection_summary_input, self.state, paragraph_index
            )
            
            print(f"    Reflection {reflection_i + 1} completed")
    
    def _generate_final_report(self) -> str:
        """Generate final report"""
        print(f"\n[Step 3] Generating final report...")
        
        # Prepare report data
        report_data = []
        for paragraph in self.state.paragraphs:
            report_data.append({
                "title": paragraph.title,
                "paragraph_latest_state": paragraph.research.latest_summary
            })
        
        # Format report
        try:
            final_report = self.report_formatting_node.run(report_data)
        except Exception as e:
            print(f"LLM formatting failed, using fallback method: {str(e)}")
            final_report = self.report_formatting_node.format_report_manually(
                report_data, self.state.report_title
            )
        
        # Update state
        self.state.final_report = final_report
        self.state.mark_completed()
        
        print("Final report generated")
        return final_report
    
    def _save_report(self, report_content: str):
        """Save report to file"""
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_safe = "".join(c for c in self.state.query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        query_safe = query_safe.replace(' ', '_')[:30]
        
        filename = f"deep_search_report_{query_safe}_{timestamp}.md"
        filepath = os.path.join(self.config.output_dir, filename)
        
        # Save report
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"Report saved to: {filepath}")
        
        # Save state (if configuration allows)
        if self.config.save_intermediate_states:
            state_filename = f"state_{query_safe}_{timestamp}.json"
            state_filepath = os.path.join(self.config.output_dir, state_filename)
            self.state.save_to_file(state_filepath)
            print(f"State saved to: {state_filepath}")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        return self.state.get_progress_summary()
    
    def load_state(self, filepath: str):
        """Load state from file"""
        self.state = State.load_from_file(filepath)
        print(f"State loaded from {filepath}")
    
    def save_state(self, filepath: str):
        """Save state to file"""
        self.state.save_to_file(filepath)
        print(f"State saved to {filepath}")


def create_agent(config_file: Optional[str] = None) -> DeepSearchAgent:
    """
    Convenience function to create a Deep Search Agent instance
    
    Args:
        config_file: Configuration file path
        
    Returns:
        DeepSearchAgent instance
    """
    config = load_config(config_file)
    return DeepSearchAgent(config)
