import validators,streamlit as st
import re
from urllib.parse import urlparse
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader,UnstructuredURLLoader
from langchain_huggingface import HuggingFaceEndpoint
from database import SummaryDatabase, ExportManager
import os
from datetime import datetime


def is_youtube_url(url):
    """Check if URL is a YouTube URL (youtube.com or youtu.be)"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/',
        r'(?:https?://)?(?:www\.)?youtu\.be/'
    ]
    return any(re.search(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)


def validate_and_fix_url(url):
    """Validate URL and provide helpful suggestions"""
    if not url.strip():
        return None, "Please enter a URL"
    
    # Check if URL has a scheme
    parsed = urlparse(url)
    if not parsed.scheme:
        # Try adding https://
        fixed_url = f"https://{url}"
        if validators.url(fixed_url):
            return fixed_url, f"Missing protocol. Did you mean: {fixed_url}?"
        else:
            return None, "Please include the protocol (http:// or https://) in your URL"
    
    # Validate the URL
    if not validators.url(url):
        return None, "Please enter a valid URL format"
    
    return url, None


def display_history_interface():
    """Display the history interface"""
    st.subheader("📚 Summary History")
    
    # Initialize database
    db = SummaryDatabase()
    
    # Search functionality
    search_query = st.text_input("🔍 Search summaries", placeholder="Search by URL, title, or content...")
    
    # Get summaries based on search
    if search_query:
        summaries = db.search_summaries(search_query)
        st.info(f"Found {len(summaries)} summaries matching '{search_query}'")
    else:
        summaries = db.get_all_summaries()
    
    if not summaries:
        st.info("No summaries found. Create your first summary to see it here!")
        return
    
    # Display summaries
    for summary in summaries:
        id, url, title, summary_text, summary_length, summary_tone, model_used, created_at, word_count, video_duration, video_channel = summary
        
        with st.expander(f"📄 {title or 'Untitled'} - {created_at[:10]}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**URL:** [{url}]({url})")
                st.write(f"**Date:** {created_at}")
                st.write(f"**Length:** {summary_length} | **Tone:** {summary_tone}")
                st.write(f"**Word Count:** {word_count}")
                if video_duration:
                    st.write(f"**Duration:** {video_duration}")
                if video_channel:
                    st.write(f"**Channel:** {video_channel}")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{id}"):
                    if db.delete_summary(id):
                        st.success("Summary deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete summary")
            
            st.write("**Summary:**")
            st.write(summary_text)


def export_summaries():
    """Handle export functionality"""
    st.subheader("📥 Export Summaries")
    
    db = SummaryDatabase()
    summaries = db.get_all_summaries()
    
    if not summaries:
        st.warning("No summaries available for export.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as Markdown"):
            markdown_content = ExportManager.export_to_markdown(summaries)
            success, filepath = ExportManager.save_export_file(markdown_content, "summaries", "md")
            if success:
                st.success(f"✅ Exported to {filepath}")
                st.download_button(
                    label="📥 Download Markdown",
                    data=markdown_content,
                    file_name=f"summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            else:
                st.error("Failed to export Markdown")
    
    with col2:
        if st.button("📊 Export as JSON"):
            json_content = ExportManager.export_to_json(summaries)
            success, filepath = ExportManager.save_export_file(json_content, "summaries", "json")
            if success:
                st.success(f"✅ Exported to {filepath}")
                st.download_button(
                    label="📥 Download JSON",
                    data=json_content,
                    file_name=f"summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.error("Failed to export JSON")
    
    with col3:
        if st.button("📈 Export as CSV"):
            csv_content = ExportManager.export_to_csv(summaries)
            success, filepath = ExportManager.save_export_file(csv_content, "summaries", "csv")
            if success:
                st.success(f"✅ Exported to {filepath}")
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_content,
                    file_name=f"summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.error("Failed to export CSV")


## streamlit APP
st.set_page_config(page_title="LangChain: Summarize Text From YouTube", page_icon="🦜")
st.title("📺Summarize Text From YouTube Video Using LangChain 🐦")
st.subheader('Summarize URL')



## Get the Groq API Key and url(YT or website)to be summarized
with st.sidebar:
    hf_api_key=st.text_input("Huggingface API Token",value="",type="password")
    
    # Summary Length Controls
    st.divider()
    st.subheader("📏 Summary Length")
    
    # Length category selection
    length_category = st.selectbox(
        "Choose length category:",
        ["Short (100-150 words)", "Medium (200-300 words)", "Long (400-500 words)", "Custom"],
        index=1  # Default to Medium
    )
    
    # Custom word count slider (only shown when Custom is selected)
    if length_category == "Custom":
        custom_word_count = st.slider(
            "Custom word count:",
            min_value=50,
            max_value=1000,
            value=300,
            step=25,
            help="Select between 50-1000 words"
        )
        word_count = custom_word_count
    else:
        # Extract word count from category
        if "Short" in length_category:
            word_count = 125  # Average of 100-150
        elif "Medium" in length_category:
            word_count = 250  # Average of 200-300
        elif "Long" in length_category:
            word_count = 450  # Average of 400-500
    
    # Display selected word count
    st.info(f"📊 Target: ~{word_count} words")
    
    # History and Export Section
    st.divider()
    st.subheader("📚 History & Export")
    
    # Initialize database for stats
    db = SummaryDatabase()
    summary_count = db.get_summary_count()
    
    if summary_count > 0:
        st.info(f"📊 Total summaries: {summary_count}")
        
        # Recent summaries preview
        recent_summaries = db.get_recent_summaries(3)
        if recent_summaries:
            st.write("**Recent summaries:**")
            for summary in recent_summaries:
                id, url, title, summary_text, summary_length, summary_tone, model_used, created_at, word_count, video_duration, video_channel = summary
                st.write(f"• {title or 'Untitled'} ({created_at[:10]})")
    else:
        st.info("No summaries yet. Create your first one!")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📚 View History", use_container_width=True):
            st.session_state.show_history = True
            st.session_state.show_export = False
    
    with col2:
        if st.button("📥 Export", use_container_width=True):
            st.session_state.show_export = True
            st.session_state.show_history = False
    
    # Clear all button
    if summary_count > 0:
        if st.button("🗑️ Clear All History", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                if db.clear_all_summaries():
                    st.success("All summaries cleared!")
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.error("Failed to clear summaries")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm clearing all history")

# URL input with helper text
generic_url = st.text_input(
    "URL", 
    label_visibility="collapsed",
    placeholder="Enter a YouTube video URL or any webpage URL..."
)

# Helper text with examples
st.caption("💡 **Examples:**")
st.caption("• YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`")
st.caption("• YouTube Short: `https://youtu.be/dQw4w9WgXcQ`")
st.caption("• Web page: `https://example.com/article`")

# Handle different views
if st.session_state.get('show_history', False):
    display_history_interface()
elif st.session_state.get('show_export', False):
    export_summaries()
else:
    # Main summarization interface
    st.write("Enter a URL above to get started with summarization!")

## Gemma Model USsing Groq API
##llm =ChatGroq(model="Gemma-7b-It", groq_api_key=groq_api_key)
repo_id="mistralai/Mistral-7B-Instruct-v0.3"
llm=HuggingFaceEndpoint(repo_id=repo_id,max_length=150,temperature=0.7,token=hf_api_key)

# Validation function for word count
def validate_word_count(word_count):
    """Validate and cap word count to reasonable limits"""
    if word_count < 50:
        return 50
    elif word_count > 1000:
        return 1000
    return word_count

# Validate the word count
validated_word_count = validate_word_count(word_count)

# Create dynamic prompt template
prompt_template=f"""
Provide a comprehensive summary of the following content in approximately {validated_word_count} words. 
Make sure the summary is well-structured and covers the key points:

Content: {{text}}

Summary:
"""
prompt=PromptTemplate(template=prompt_template,input_variables=["text"])

if st.button("Summarize"):
    ## Validate all the inputs
    if not hf_api_key.strip():
        st.error("Please provide your Hugging Face API token")
    elif not generic_url.strip():
        st.error("Please enter a URL to summarize")
    else:
        # Validate and potentially fix the URL
        validated_url, error_message = validate_and_fix_url(generic_url)
        
        if error_message:
            st.error(error_message)
            # If we have a suggestion, show it as a warning
            if "Did you mean:" in error_message:
                st.warning("💡 **Tip:** Click the suggested URL above to copy it, then paste it back into the input field.")
        else:
            # Use the validated (potentially fixed) URL
            generic_url = validated_url
            
            try:
                with st.spinner("Loading and processing content..."):
                    ## loading the website or yt video data
                    if is_youtube_url(generic_url):
                        loader = YoutubeLoader.from_youtube_url(generic_url, add_video_info=True)
                    else:
                        loader = UnstructuredURLLoader(
                            urls=[generic_url], 
                            ssl_verify=False,
                            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}
                        )
                    docs = loader.load()

                    ## Chain For Summarization
                    chain = load_summarize_chain(llm, chain_type="stuff", prompt=prompt)
                    output_summary = chain.run(docs)

                    # Display the summary
                    st.success("Summary generated successfully!")
                    st.write(output_summary)
                    
                    # Save to database
                    db = SummaryDatabase()
                    
                    # Extract metadata
                    title = "Untitled"
                    video_duration = None
                    video_channel = None
                    
                    if is_youtube_url(generic_url) and docs:
                        # Try to extract video metadata
                        try:
                            if hasattr(docs[0], 'metadata'):
                                metadata = docs[0].metadata
                                title = metadata.get('title', 'Untitled')
                                video_duration = metadata.get('length', None)
                                video_channel = metadata.get('author', None)
                        except:
                            pass
                    
                    # Save summary to database
                    success = db.save_summary(
                        url=generic_url,
                        title=title,
                        summary_text=output_summary,
                        summary_length=length_category,
                        summary_tone="Professional",
                        model_used=repo_id,
                        video_duration=video_duration,
                        video_channel=video_channel
                    )
                    
                    if success:
                        st.info("✅ Summary saved to history!")
                    else:
                        st.warning("⚠️ Summary generated but failed to save to history")
                        
            except Exception as e:
                st.exception(f"Exception: {e}")