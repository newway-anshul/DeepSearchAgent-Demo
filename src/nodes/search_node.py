"""
Search node implementation.
Responsible for generating initial search queries and reflection queries.
"""

import json
from typing import Dict, Any
from json.decoder import JSONDecodeError

from .base_node import BaseNode
from ..prompts import SYSTEM_PROMPT_FIRST_SEARCH, SYSTEM_PROMPT_REFLECTION
from ..utils.text_processing import (
    remove_reasoning_from_output,
    clean_json_tags,
    extract_clean_response
)


class FirstSearchNode(BaseNode):
    """Node for generating the first search query for a paragraph."""
    
    def __init__(self, llm_client):
        """
        Initialize the first search node.
        
        Args:
            llm_client: LLM client
        """
        super().__init__(llm_client, "FirstSearchNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                return "title" in data and "content" in data
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            return "title" in input_data and "content" in input_data
        return False
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, str]:
        """
        Call LLM to generate a search query and reasoning.
        
        Args:
            input_data: String or dictionary containing title and content
            **kwargs: Extra parameters
            
        Returns:
            Dictionary containing search_query and reasoning
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("Invalid input format; 'title' and 'content' are required")
            
            # Prepare input data
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)
            
            self.log_info("Generating initial search query")
            
            # Call LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_FIRST_SEARCH, message)
            
            # Process response
            processed_response = self.process_output(response)
            
            self.log_info(f"Generated search query: {processed_response.get('search_query', 'N/A')}")
            return processed_response
            
        except Exception as e:
            self.log_error(f"Failed to generate initial search query: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> Dict[str, str]:
        """
        Process LLM output and extract search query and reasoning.
        
        Args:
            output: Raw LLM output
            
        Returns:
            Dictionary containing search_query and reasoning
        """
        try:
            # Clean response text
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # Parse JSON
            try:
                result = json.loads(cleaned_output)
            except JSONDecodeError:
                # Use a more robust extraction method
                result = extract_clean_response(cleaned_output)
                if "error" in result:
                    raise ValueError("JSON parsing failed")
            
            # Validate and clean results
            search_query = result.get("search_query", "")
            reasoning = result.get("reasoning", "")
            
            if not search_query:
                raise ValueError("Search query not found")
            
            return {
                "search_query": search_query,
                "reasoning": reasoning
            }
            
        except Exception as e:
            self.log_error(f"Failed to process output: {str(e)}")
            # Return default query
            return {
                "search_query": "related topic research",
                "reasoning": "Using default search query due to parsing failure"
            }


class ReflectionNode(BaseNode):
    """Node for reflecting on a paragraph and generating a new search query."""
    
    def __init__(self, llm_client):
        """
        Initialize the reflection node.
        
        Args:
            llm_client: LLM client
        """
        super().__init__(llm_client, "ReflectionNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                required_fields = ["title", "content", "paragraph_latest_state"]
                return all(field in data for field in required_fields)
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            required_fields = ["title", "content", "paragraph_latest_state"]
            return all(field in input_data for field in required_fields)
        return False
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, str]:
        """
        Call LLM to reflect and generate a search query.
        
        Args:
            input_data: String or dictionary containing title, content, and paragraph_latest_state
            **kwargs: Extra parameters
            
        Returns:
            Dictionary containing search_query and reasoning
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("Invalid input format; 'title', 'content', and 'paragraph_latest_state' are required")
            
            # Prepare input data
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)
            
            self.log_info("Reflecting and generating a new search query")
            
            # Call LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_REFLECTION, message)
            
            # Process response
            processed_response = self.process_output(response)
            
            self.log_info(f"Reflection generated search query: {processed_response.get('search_query', 'N/A')}")
            return processed_response
            
        except Exception as e:
            self.log_error(f"Failed to generate reflection search query: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> Dict[str, str]:
        """
        Process LLM output and extract search query and reasoning.
        
        Args:
            output: Raw LLM output
            
        Returns:
            Dictionary containing search_query and reasoning
        """
        try:
            # Clean response text
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # Parse JSON
            try:
                result = json.loads(cleaned_output)
            except JSONDecodeError:
                # Use a more robust extraction method
                result = extract_clean_response(cleaned_output)
                if "error" in result:
                    raise ValueError("JSON parsing failed")
            
            # Validate and clean results
            search_query = result.get("search_query", "")
            reasoning = result.get("reasoning", "")
            
            if not search_query:
                raise ValueError("Search query not found")
            
            return {
                "search_query": search_query,
                "reasoning": reasoning
            }
            
        except Exception as e:
            self.log_error(f"Failed to process output: {str(e)}")
            # Return default query
            return {
                "search_query": "supplementary deep research information",
                "reasoning": "Using default reflection search query due to parsing failure"
            }
