"""
Report structure generation node.
Responsible for generating the overall report structure based on the query.
"""

import json
from typing import Dict, Any, List
from json.decoder import JSONDecodeError

from .base_node import StateMutationNode
from ..state.state import State
from ..prompts import SYSTEM_PROMPT_REPORT_STRUCTURE
from ..utils.text_processing import (
    remove_reasoning_from_output,
    clean_json_tags,
    extract_clean_response
)


class ReportStructureNode(StateMutationNode):
    """Node for generating report structure."""
    
    def __init__(self, llm_client, query: str):
        """
        Initialize the report structure node.
        
        Args:
            llm_client: LLM client
            query: User query
        """
        super().__init__(llm_client, "ReportStructureNode")
        self.query = query
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        return isinstance(self.query, str) and len(self.query.strip()) > 0
    
    def run(self, input_data: Any = None, **kwargs) -> List[Dict[str, str]]:
        """
        Call LLM to generate report structure.
        
        Args:
            input_data: Input data (unused here; uses query from initialization)
            **kwargs: Extra parameters
            
        Returns:
            Report structure list
        """
        try:
            self.log_info(f"Generating report structure for query: {self.query}")
            
            # Call LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_REPORT_STRUCTURE, self.query)
            
            # Process response
            processed_response = self.process_output(response)
            
            self.log_info(f"Successfully generated {len(processed_response)} paragraph structures")
            return processed_response
            
        except Exception as e:
            self.log_error(f"Failed to generate report structure: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> List[Dict[str, str]]:
        """
        Process LLM output and extract report structure.
        
        Args:
            output: Raw LLM output
            
        Returns:
            Processed report structure list
        """
        try:
            # Clean response text
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # Parse JSON
            try:
                report_structure = json.loads(cleaned_output)
            except JSONDecodeError:
                # Use a more robust extraction method
                report_structure = extract_clean_response(cleaned_output)
                if "error" in report_structure:
                    raise ValueError("JSON parsing failed")
            
            # Validate structure
            if not isinstance(report_structure, list):
                raise ValueError("Report structure should be a list")
            
            # Validate each paragraph
            validated_structure = []
            for i, paragraph in enumerate(report_structure):
                if not isinstance(paragraph, dict):
                    continue
                
                title = paragraph.get("title", f"Paragraph {i+1}")
                content = paragraph.get("content", "")
                
                validated_structure.append({
                    "title": title,
                    "content": content
                })
            
            return validated_structure
            
        except Exception as e:
            self.log_error(f"Failed to process output: {str(e)}")
            # Return default structure
            return [
                {
                    "title": "Overview",
                    "content": f"A general overview and background introduction of '{self.query}'"
                },
                {
                    "title": "Detailed Analysis",
                    "content": f"An in-depth analysis of content related to '{self.query}'"
                }
            ]
    
    def mutate_state(self, input_data: Any = None, state: State = None, **kwargs) -> State:
        """
        Write report structure into state.
        
        Args:
            input_data: Input data
            state: Current state; if None, create a new state
            **kwargs: Extra parameters
            
        Returns:
            Updated state
        """
        if state is None:
            state = State()
        
        try:
            # Generate report structure
            report_structure = self.run(input_data, **kwargs)
            
            # Set query and report title
            state.query = self.query
            if not state.report_title:
                state.report_title = f"In-depth Research Report on '{self.query}'"
            
            # Add paragraphs to state
            for paragraph_data in report_structure:
                state.add_paragraph(
                    title=paragraph_data["title"],
                    content=paragraph_data["content"]
                )
            
            self.log_info(f"Added {len(report_structure)} paragraphs to state")
            return state
            
        except Exception as e:
            self.log_error(f"State update failed: {str(e)}")
            raise e
