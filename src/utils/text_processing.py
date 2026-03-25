"""
Text processing utility functions.
Used to clean LLM output, parse JSON, and related tasks.
"""

import re
import json
from typing import Dict, Any, List
from json.decoder import JSONDecodeError


def clean_json_tags(text: str) -> str:
    """
    Remove JSON code fence tags from text.
    
    Args:
        text: Raw text.
        
    Returns:
        Cleaned text.
    """
    # Remove ```json and ``` tags.
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'```', '', text)
    
    return text.strip()


def clean_markdown_tags(text: str) -> str:
    """
    Remove Markdown code fence tags from text.
    
    Args:
        text: Raw text.
        
    Returns:
        Cleaned text.
    """
    # Remove ```markdown and ``` tags.
    text = re.sub(r'```markdown\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'```', '', text)
    
    return text.strip()


def remove_reasoning_from_output(text: str) -> str:
    """
    Remove reasoning text from output.
    
    Args:
        text: Raw text.
        
    Returns:
        Cleaned text.
    """
    # Remove common reasoning markers.
    patterns = [
        r'(?:reasoning|推理|思考|分析)[:：]\s*.*?(?=\{|\[)',  # 移除推理部分
        r'(?:explanation|解释|说明)[:：]\s*.*?(?=\{|\[)',   # 移除解释部分
        r'^.*?(?=\{|\[)',  # 移除JSON前的所有文本
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()


def extract_clean_response(text: str) -> Dict[str, Any]:
    """
    Extract and clean JSON content from a response.
    
    Args:
        text: Raw response text.
        
    Returns:
        Parsed JSON dictionary.
    """
    # Clean the text first.
    cleaned_text = clean_json_tags(text)
    cleaned_text = remove_reasoning_from_output(cleaned_text)
    
    # Try direct parsing first.
    try:
        return json.loads(cleaned_text)
    except JSONDecodeError:
        pass
    
    # Try locating a JSON object.
    json_pattern = r'\{.*\}'
    match = re.search(json_pattern, cleaned_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except JSONDecodeError:
            pass
    
    # Try locating a JSON array.
    array_pattern = r'\[.*\]'
    match = re.search(array_pattern, cleaned_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except JSONDecodeError:
            pass
    
    # If all attempts fail, return error details.
    print(f"Unable to parse JSON response: {cleaned_text[:200]}...")
    return {"error": "JSON parsing failed", "raw_text": cleaned_text}


def update_state_with_search_results(search_results: List[Dict[str, Any]], 
                                   paragraph_index: int, state: Any) -> Any:
    """
    Update the state object with search results.
    
    Args:
        search_results: List of search results.
        paragraph_index: Paragraph index.
        state: State object.
        
    Returns:
        Updated state object.
    """
    if 0 <= paragraph_index < len(state.paragraphs):
        # Get the latest search query (assumed to be the current query).
        current_query = ""
        if search_results:
            # Infer the query from the search results.
            # This should be improved later to capture the actual query.
            current_query = "search query"
        
        # Add search results to the state.
        state.paragraphs[paragraph_index].research.add_search_results(
            current_query, search_results
        )
    
    return state


def validate_json_schema(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate whether JSON data contains required fields.
    
    Args:
        data: Data to validate.
        required_fields: List of required fields.
        
    Returns:
        Whether validation passes.
    """
    return all(field in data for field in required_fields)


def truncate_content(content: str, max_length: int = 20000) -> str:
    """
    Truncate content to the specified length.
    
    Args:
        content: Original content.
        max_length: Maximum length.
        
    Returns:
        Truncated content.
    """
    if len(content) <= max_length:
        return content
    
    # Try truncating at a word boundary.
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Use the last space if it is in a reasonable position.
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def format_search_results_for_prompt(search_results: List[Dict[str, Any]], 
                                   max_length: int = 20000) -> List[str]:
    """
    Format search results for prompt input.
    
    Args:
        search_results: List of search results.
        max_length: Maximum length for each result.
        
    Returns:
        List of formatted content.
    """
    formatted_results = []
    
    for result in search_results:
        content = result.get('content', '')
        if content:
            truncated_content = truncate_content(content, max_length)
            formatted_results.append(truncated_content)
    
    return formatted_results
