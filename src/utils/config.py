"""
Configuration management module.
Handles environment variables and configuration parameters.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration container."""
    # API keys
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # Model configuration
    default_llm_provider: str = "deepseek"  # deepseek or openai
    deepseek_model: str = "deepseek-chat"
    openai_model: str = "gpt-4o-mini"
    
    # Search configuration
    max_search_results: int = 3
    search_timeout: int = 240
    max_content_length: int = 20000
    
    # Agent configuration
    max_reflections: int = 2
    max_paragraphs: int = 5
    
    # Output configuration
    output_dir: str = "reports"
    save_intermediate_states: bool = True
    
    def validate(self) -> bool:
        """Validate the configuration."""
        # Check required API keys.
        if self.default_llm_provider == "deepseek" and not self.deepseek_api_key:
            print("Error: DeepSeek API key is not set")
            return False
        
        if self.default_llm_provider == "openai" and not self.openai_api_key:
            print("Error: OpenAI API key is not set")
            return False
        
        if not self.tavily_api_key:
            print("Error: Tavily API key is not set")
            return False
        
        return True
    
    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Create a configuration object from a config file."""
        if config_file.endswith('.py'):
            # Python config file.
            import importlib.util
            
            # Dynamically import the config file.
            spec = importlib.util.spec_from_file_location("config", config_file)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            return cls(
                deepseek_api_key=getattr(config_module, "DEEPSEEK_API_KEY", None),
                openai_api_key=getattr(config_module, "OPENAI_API_KEY", None),
                tavily_api_key=getattr(config_module, "TAVILY_API_KEY", None),
                default_llm_provider=getattr(config_module, "DEFAULT_LLM_PROVIDER", "deepseek"),
                deepseek_model=getattr(config_module, "DEEPSEEK_MODEL", "deepseek-chat"),
                openai_model=getattr(config_module, "OPENAI_MODEL", "gpt-4o-mini"),
                max_search_results=getattr(config_module, "SEARCH_RESULTS_PER_QUERY", 3),
                search_timeout=getattr(config_module, "SEARCH_TIMEOUT", 240),
                max_content_length=getattr(config_module, "SEARCH_CONTENT_MAX_LENGTH", 20000),
                max_reflections=getattr(config_module, "MAX_REFLECTIONS", 2),
                max_paragraphs=getattr(config_module, "MAX_PARAGRAPHS", 5),
                output_dir=getattr(config_module, "OUTPUT_DIR", "reports"),
                save_intermediate_states=getattr(config_module, "SAVE_INTERMEDIATE_STATES", True)
            )
        else:
            # .env-style config file.
            config_dict = {}
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config_dict[key.strip()] = value.strip()
            
            return cls(
                deepseek_api_key=config_dict.get("DEEPSEEK_API_KEY"),
                openai_api_key=config_dict.get("OPENAI_API_KEY"),
                tavily_api_key=config_dict.get("TAVILY_API_KEY"),
                default_llm_provider=config_dict.get("DEFAULT_LLM_PROVIDER", "deepseek"),
                deepseek_model=config_dict.get("DEEPSEEK_MODEL", "deepseek-chat"),
                openai_model=config_dict.get("OPENAI_MODEL", "gpt-4o-mini"),
                max_search_results=int(config_dict.get("SEARCH_RESULTS_PER_QUERY", "3")),
                search_timeout=int(config_dict.get("SEARCH_TIMEOUT", "240")),
                max_content_length=int(config_dict.get("SEARCH_CONTENT_MAX_LENGTH", "20000")),
                max_reflections=int(config_dict.get("MAX_REFLECTIONS", "2")),
                max_paragraphs=int(config_dict.get("MAX_PARAGRAPHS", "5")),
                output_dir=config_dict.get("OUTPUT_DIR", "reports"),
                save_intermediate_states=config_dict.get("SAVE_INTERMEDIATE_STATES", "true").lower() == "true"
            )


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Load configuration.
    
    Args:
        config_file: Config file path. If omitted, default paths are used.
        
    Returns:
        Configuration object.
    """
    # Determine which config file to load.
    if config_file:
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file does not exist: {config_file}")
        file_to_load = config_file
    else:
        # Try common config file locations.
        for config_path in ["config.py", "config.env", ".env"]:
            if os.path.exists(config_path):
                file_to_load = config_path
                print(f"Found config file: {config_path}")
                break
        else:
            raise FileNotFoundError("No config file found. Please create a config.py file")
    
    # Create the configuration object.
    config = Config.from_file(file_to_load)
    
    # Validate the configuration.
    if not config.validate():
        raise ValueError("Configuration validation failed. Please check the API keys in the config file")
    
    return config


def print_config(config: Config):
    """Print configuration information with sensitive values hidden."""
    print("\n=== Current Configuration ===")
    print(f"LLM provider: {config.default_llm_provider}")
    print(f"DeepSeek model: {config.deepseek_model}")
    print(f"OpenAI model: {config.openai_model}")
    print(f"Max search results: {config.max_search_results}")
    print(f"Search timeout: {config.search_timeout} seconds")
    print(f"Max content length: {config.max_content_length}")
    print(f"Max reflections: {config.max_reflections}")
    print(f"Max paragraphs: {config.max_paragraphs}")
    print(f"Output directory: {config.output_dir}")
    print(f"Save intermediate states: {config.save_intermediate_states}")
    
    # Show API key status without revealing actual values.
    print(f"DeepSeek API key: {'set' if config.deepseek_api_key else 'not set'}")
    print(f"OpenAI API key: {'set' if config.openai_api_key else 'not set'}")
    print(f"Tavily API key: {'set' if config.tavily_api_key else 'not set'}")
    print("=============================\n")
