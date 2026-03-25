"""
Summary node implementation.
Responsible for generating and updating paragraph content based on search results.
"""

import json
from typing import Dict, Any, List
from json.decoder import JSONDecodeError

from .base_node import StateMutationNode
from ..state.state import State
from ..prompts import SYSTEM_PROMPT_FIRST_SUMMARY, SYSTEM_PROMPT_REFLECTION_SUMMARY
from ..utils.text_processing import (
    remove_reasoning_from_output,
    clean_json_tags,
    extract_clean_response,
    format_search_results_for_prompt
)


class FirstSummaryNode(StateMutationNode):
    """Node for generating the first paragraph summary from search results."""
    
    def __init__(self, llm_client):
        """
        Initialize the first summary node.
        
        Args:
            llm_client: LLM client
        """
        super().__init__(llm_client, "FirstSummaryNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                required_fields = ["title", "content", "search_query", "search_results"]
                return all(field in data for field in required_fields)
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            required_fields = ["title", "content", "search_query", "search_results"]
            return all(field in input_data for field in required_fields)
        return False
    
    def run(self, input_data: Any, **kwargs) -> str:
        """
        Call LLM to generate a paragraph summary.
        
        Args:
            input_data: Data containing title, content, search_query, and search_results
            **kwargs: Extra parameters
            
        Returns:
            Paragraph summary content
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("Invalid input data format")
            
            # Prepare input data
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)
            
            self.log_info("Generating initial paragraph summary")
            
            # Call LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_FIRST_SUMMARY, message)
            
            # Process response
            processed_response = self.process_output(response)
            
            self.log_info("Successfully generated initial paragraph summary")
            return processed_response
            
        except Exception as e:
            self.log_error(f"Failed to generate initial summary: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> str:
        """
        Process LLM output and extract paragraph summary.
        
        Args:
            output: Raw LLM output
            
        Returns:
            Paragraph summary content
        """
        try:
            # Clean response text
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # Parse JSON
            try:
                result = json.loads(cleaned_output)
            except JSONDecodeError:
                # If not JSON format, return cleaned text directly
                return cleaned_output
            
            # Extract paragraph content
            if isinstance(result, dict):
                paragraph_content = result.get("paragraph_latest_state", "")
                if paragraph_content:
                    return paragraph_content
            
            # If extraction fails, return original cleaned text
            return cleaned_output
            
        except Exception as e:
            self.log_error(f"Failed to process output: {str(e)}")
            return "Paragraph summary generation failed"
    
    def mutate_state(self, input_data: Any, state: State, paragraph_index: int, **kwargs) -> State:
        """
        Update the latest paragraph summary in state.
        
        Args:
            input_data: Input data
            state: Current state
            paragraph_index: Paragraph index
            **kwargs: Extra parameters
            
        Returns:
            Updated state
        """
        try:
            # Generate summary
            summary = self.run(input_data, **kwargs)
            
            # Update state
            if 0 <= paragraph_index < len(state.paragraphs):
                state.paragraphs[paragraph_index].research.latest_summary = summary
                self.log_info(f"Updated initial summary for paragraph {paragraph_index}")
            else:
                raise ValueError(f"Paragraph index {paragraph_index} is out of range")
            
            state.update_timestamp()
            return state
            
        except Exception as e:
            self.log_error(f"State update failed: {str(e)}")
            raise e


class ReflectionSummaryNode(StateMutationNode):
    """Node for updating paragraph summary based on reflection search results."""
    
    def __init__(self, llm_client):
        """
        Initialize the reflection summary node.
        
        Args:
            llm_client: LLM client
        """
        super().__init__(llm_client, "ReflectionSummaryNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                required_fields = ["title", "content", "search_query", "search_results", "paragraph_latest_state"]
                return all(field in data for field in required_fields)
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            required_fields = ["title", "content", "search_query", "search_results", "paragraph_latest_state"]
            return all(field in input_data for field in required_fields)
        return False
    
    def run(self, input_data: Any, **kwargs) -> str:
        """
        Call LLM to update paragraph content.
        
        Args:
            input_data: Data containing complete reflection information
            **kwargs: Extra parameters
            
        Returns:
            Updated paragraph content
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("Invalid input data format")
            
            # Prepare input data
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)
            
            self.log_info("Generating reflection summary")
            
            # Call LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_REFLECTION_SUMMARY, message)
            
            # Process response
            processed_response = self.process_output(response)
            
            self.log_info("Successfully generated reflection summary")
            return processed_response
            
        except Exception as e:
            self.log_error(f"Failed to generate reflection summary: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> str:
        """
        Process LLM output and extract updated paragraph content.
        
        Args:
            output: Raw LLM output
            
        Returns:
            Updated paragraph content
        """
        try:
            # Clean response text
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # Parse JSON
            try:
                result = json.loads(cleaned_output)
            except JSONDecodeError:
                # If not JSON format, return cleaned text directly
                return cleaned_output
            
            # Extract updated paragraph content
            if isinstance(result, dict):
                updated_content = result.get("updated_paragraph_latest_state", "")
                if updated_content:
                    return updated_content
            
            # If extraction fails, return original cleaned text
            return cleaned_output
            
        except Exception as e:
            self.log_error(f"Failed to process output: {str(e)}")
            return "Reflection summary generation failed"
    
    def mutate_state(self, input_data: Any, state: State, paragraph_index: int, **kwargs) -> State:
        """
        Write updated summary into state.
        
        Args:
            input_data: Input data
            state: Current state
            paragraph_index: Paragraph index
            **kwargs: Extra parameters
            
        Returns:
            Updated state
        """
        try:
            # Generate updated summary
            updated_summary = self.run(input_data, **kwargs)
            
            # Update state
            if 0 <= paragraph_index < len(state.paragraphs):
                state.paragraphs[paragraph_index].research.latest_summary = updated_summary
                state.paragraphs[paragraph_index].research.increment_reflection()
                self.log_info(f"Updated reflection summary for paragraph {paragraph_index}")
            else:
                raise ValueError(f"Paragraph index {paragraph_index} is out of range")
            
            state.update_timestamp()
            return state
            
        except Exception as e:
            self.log_error(f"State update failed: {str(e)}")
            raise e
