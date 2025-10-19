import validators,streamlit as st
import re
from urllib.parse import urlparse
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import YoutubeLoader,UnstructuredURLLoader
from langchain_huggingface import HuggingFaceEndpoint


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


## streamlit APP
st.set_page_config(page_title="LangChain: Summarize Text From YouTube", page_icon="🦜")
st.title("📺Summarize Text From YouTube Video Using LangChain 🐦")
st.subheader('Summarize URL')



## Get the Groq API Key and url(YT or website)to be summarized
with st.sidebar:
    hf_api_key=st.text_input("Huggingface API Token",value="",type="password")

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

## Gemma Model USsing Groq API
##llm =ChatGroq(model="Gemma-7b-It", groq_api_key=groq_api_key)
repo_id="mistralai/Mistral-7B-Instruct-v0.3"
llm=HuggingFaceEndpoint(repo_id=repo_id,max_length=150,temperature=0.7,token=hf_api_key)

prompt_template="""
Provide a summary of the following content in 300 words:
Content:{text}

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
                with st.spinner("Waiting..."):
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

                    st.success(output_summary)
            except Exception as e:
                st.exception(f"Exception: {e}")