"""
Streamlit web interface.
Provides a user-friendly web interface for Deep Search Agent.
"""

import os
import sys
import streamlit as st
from datetime import datetime
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src import DeepSearchAgent, Config


def main():
    """Main entry point."""
    st.set_page_config(
        page_title="Deep Search Agent",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("Deep Search Agent")
    st.markdown("A framework-free deep search AI agent powered by DeepSeek")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API key configuration
        st.subheader("API Keys")
        deepseek_key = st.text_input("DeepSeek API Key", type="password", 
                                   value="")
        tavily_key = st.text_input("Tavily API Key", type="password",
                                 value="")
        
        # Advanced configuration
        st.subheader("Advanced Configuration")
        max_reflections = st.slider("Reflection Rounds", 1, 5, 2)
        max_search_results = st.slider("Search Results", 1, 10, 3)
        max_content_length = st.number_input("Maximum Content Length", 1000, 50000, 20000)
        
        # Model selection
        llm_provider = st.selectbox("LLM Provider", ["deepseek", "openai"])
        
        if llm_provider == "deepseek":
            model_name = st.selectbox("DeepSeek Model", ["deepseek-chat"])
        else:
            model_name = st.selectbox("OpenAI Model", ["gpt-4o-mini", "gpt-4o"])
            openai_key = st.text_input("OpenAI API Key", type="password",
                                     value="")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Research Query")
        query = st.text_area(
            "Enter the topic you want to research",
            placeholder="For example: AI development trends in 2025",
            height=100
        )
        
        # Preset example queries
        st.subheader("Example Queries")
        example_queries = [
            "AI development trends in 2025",
            "Applications of deep learning in healthcare",
            "Latest developments in blockchain technology",
            "Sustainable energy technology trends",
            "Current state of quantum computing development"
        ]
        
        selected_example = st.selectbox("Choose an Example Query", ["Custom"] + example_queries)
        if selected_example != "Custom":
            query = selected_example
    
    with col2:
        st.header("Status")
        if 'agent' in st.session_state and hasattr(st.session_state.agent, 'state'):
            progress = st.session_state.agent.get_progress_summary()
            st.metric("Total Paragraphs", progress['total_paragraphs'])
            st.metric("Completed", progress['completed_paragraphs'])
            st.progress(progress['progress_percentage'] / 100)
        else:
            st.info("Research has not started yet")
    
    # Action button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        start_research = st.button("Start Research", type="primary", use_container_width=True)
    
    # Validate configuration
    if start_research:
        if not query.strip():
            st.error("Please enter a research query")
            return
        
        if not deepseek_key and llm_provider == "deepseek":
            st.error("Please provide a DeepSeek API Key")
            return
        
        if not tavily_key:
            st.error("Please provide a Tavily API Key")
            return
        
        if llm_provider == "openai" and not openai_key:
            st.error("Please provide an OpenAI API Key")
            return
        
        # Create configuration
        config = Config(
            deepseek_api_key=deepseek_key if llm_provider == "deepseek" else None,
            openai_api_key=openai_key if llm_provider == "openai" else None,
            tavily_api_key=tavily_key,
            default_llm_provider=llm_provider,
            deepseek_model=model_name if llm_provider == "deepseek" else "deepseek-chat",
            openai_model=model_name if llm_provider == "openai" else "gpt-4o-mini",
            max_reflections=max_reflections,
            max_search_results=max_search_results,
            max_content_length=max_content_length,
            output_dir="streamlit_reports"
        )
        
        # Run the research
        execute_research(query, config)


def execute_research(query: str, config: Config):
    """Run the research workflow."""
    try:
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize the agent
        status_text.text("Initializing agent...")
        agent = DeepSearchAgent(config)
        st.session_state.agent = agent
        
        progress_bar.progress(10)
        
        # Generate report structure
        status_text.text("Generating report structure...")
        agent._generate_report_structure(query)
        progress_bar.progress(20)
        
        # Process paragraphs
        total_paragraphs = len(agent.state.paragraphs)
        for i in range(total_paragraphs):
            status_text.text(f"Processing paragraph {i+1}/{total_paragraphs}: {agent.state.paragraphs[i].title}")
            
            # Initial search and summary
            agent._initial_search_and_summary(i)
            progress_value = 20 + (i + 0.5) / total_paragraphs * 60
            progress_bar.progress(int(progress_value))
            
            # Reflection loop
            agent._reflection_loop(i)
            agent.state.paragraphs[i].research.mark_completed()
            
            progress_value = 20 + (i + 1) / total_paragraphs * 60
            progress_bar.progress(int(progress_value))
        
        # Generate final report
        status_text.text("Generating final report...")
        final_report = agent._generate_final_report()
        progress_bar.progress(90)
        
        # Save the report
        status_text.text("Saving report...")
        agent._save_report(final_report)
        progress_bar.progress(100)
        
        status_text.text("Research complete!")
        
        # Display results
        display_results(agent, final_report)
        
    except Exception as e:
        st.error(f"An error occurred during research: {str(e)}")


def display_results(agent: DeepSearchAgent, final_report: str):
    """Display the research results."""
    st.header("Research Results")
    
    # Result tabs
    tab1, tab2, tab3 = st.tabs(["Final Report", "Details", "Download"])
    
    with tab1:
        st.markdown(final_report)
    
    with tab2:
        # Paragraph details
        st.subheader("Paragraph Details")
        for i, paragraph in enumerate(agent.state.paragraphs):
            with st.expander(f"Paragraph {i+1}: {paragraph.title}"):
                st.write("**Expected content:**", paragraph.content)
                st.write("**Final content:**", paragraph.research.latest_summary[:300] + "..." 
                        if len(paragraph.research.latest_summary) > 300 
                        else paragraph.research.latest_summary)
                st.write("**Search count:**", paragraph.research.get_search_count())
                st.write("**Reflection rounds:**", paragraph.research.reflection_iteration)
        
        # Search history
        st.subheader("Search History")
        all_searches = []
        for paragraph in agent.state.paragraphs:
            all_searches.extend(paragraph.research.search_history)
        
        if all_searches:
            for i, search in enumerate(all_searches):
                with st.expander(f"Search {i+1}: {search.query}"):
                    st.write("**URL:**", search.url)
                    st.write("**Title:**", search.title)
                    st.write("**Content preview:**", search.content[:200] + "..." if len(search.content) > 200 else search.content)
                    if search.score:
                        st.write("**Relevance score:**", search.score)
    
    with tab3:
        # Download options
        st.subheader("Download Report")
        
        # Markdown download
        st.download_button(
            label="Download Markdown Report",
            data=final_report,
            file_name=f"deep_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
        
        # JSON state download
        state_json = agent.state.to_json()
        st.download_button(
            label="Download State File",
            data=state_json,
            file_name=f"deep_search_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
