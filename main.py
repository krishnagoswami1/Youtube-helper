import streamlit as st
import yt_dlp
import os
import tempfile
import shutil
from pathlib import Path
import re

# Set page config
st.set_page_config(
    page_title="Ytube Buddy",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
# st.markdown("""
# <style>
#     .main-header {
#         text-align: center;
#         color: #ff0000;
#         margin-bottom: 2rem;
#     }
#     .download-section {
#         background-color: #f8f9fa;
#         padding: 2rem;
#         border-radius: 10px;
#         margin: 1rem 0;
#     }
#     .quality-info {
#         background-color: #e3f2fd;
#         padding: 1rem;
#         border-radius: 5px;
#         margin: 1rem 0;
#     }
#     .success-message {
#         background-color: #d4edda;
#         color: #155724;
#         padding: 1rem;
#         border-radius: 5px;
#         border: 1px solid #c3e6cb;
#     }
#     .error-message {
#         background-color: #f8d7da;
#         color: #721c24;
#         padding: 1rem;
#         border-radius: 5px;
#         border: 1px solid #f5c6cb;
#     }
# </style>
# """, unsafe_allow_html=True)

def is_valid_youtube_url(url):
    """Validate if the URL is a valid YouTube URL"""
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(https?://)?(www\.)?youtu\.be/',
        r'(https?://)?(www\.)?youtube\.com/watch\?v=',
        r'(https?://)?(www\.)?youtube\.com/embed/',
        r'(https?://)?(www\.)?youtube\.com/v/',
    ]
    
    for pattern in youtube_patterns:
        if re.search(pattern, url):
            return True
    return False

def get_video_info(url):
    """Get video information and available formats"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant information
            video_info = {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'thumbnail': info.get('thumbnail', ''),
            }
            
            # Get available formats
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':  # Video + Audio
                        quality = f.get('format_note', f.get('height', 'Unknown'))
                        ext = f.get('ext', 'mp4')
                        filesize = f.get('filesize', 0)
                        formats.append({
                            'format_id': f['format_id'],
                            'quality': f"{quality}p" if isinstance(quality, int) else quality,
                            'ext': ext,
                            'filesize': filesize,
                            'type': 'video+audio'
                        })
                
                # Also get audio-only formats
                for f in info['formats']:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':  # Audio only
                        quality = f.get('format_note', f.get('abr', 'Unknown'))
                        ext = f.get('ext', 'mp3')
                        filesize = f.get('filesize', 0)
                        formats.append({
                            'format_id': f['format_id'],
                            'quality': f"{quality}kbps" if isinstance(quality, int) else quality,
                            'ext': ext,
                            'filesize': filesize,
                            'type': 'audio-only'
                        })
            
            return video_info, formats
            
    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        return None, None

def format_filesize(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "Unknown size"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_duration(seconds):
    """Convert seconds to human readable format"""
    if seconds == 0:
        return "Unknown duration"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def download_video(url, format_id, output_path):
    """Download video with specified format"""
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return True, "Download completed successfully!"
        
    except Exception as e:
        return False, f"Download failed: {str(e)}"

# Main app
def main():
    st.markdown('<h1 class="main-header">📺 YouTube Video Downloader</h1>', unsafe_allow_html=True)
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Paste YouTube URL** in the input field
        2. **Click 'Get Video Info'** to fetch details
        3. **Choose quality** from available options
        4. **Click 'Download'** to start downloading
        
        ### 📝 Supported URLs:
        - youtube.com/watch?v=...
        - youtu.be/...
        - youtube.com/embed/...
        
        ### ⚠️ Important Notes:
        - Downloads are saved to a temporary directory
        - Large files may take time to download
        - Respect copyright and terms of service
        """)
        
    
    # Main content area
    # col1, col2 = st.columns([2, 1])
    
    # with col1:
    # st.markdown('<div class="download-section">', unsafe_allow_html=True)
    
    # URL input
    url = st.text_input(
        "🔗 Enter YouTube URL:",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste the YouTube video URL here"
    )
    
    # Get video info button
    if st.button("🔍 Get Video Info", type="primary"):
        if not url:
            st.error("Please enter a YouTube URL!")
        elif not is_valid_youtube_url(url):
            st.error("Please enter a valid YouTube URL!")
        else:
            with st.spinner("Fetching video information..."):
                video_info, formats = get_video_info(url)
                
                if video_info and formats:
                    st.session_state.video_info = video_info
                    st.session_state.formats = formats
                    st.session_state.url = url
                    st.success("Video information fetched successfully!")
                else:
                    st.error("Failed to fetch video information. Please check the URL and try again.")
    
        # st.markdown('</div>', unsafe_allow_html=True)
    
    # Display video information if available
    if hasattr(st.session_state, 'video_info') and st.session_state.video_info:
        video_info = st.session_state.video_info
        
        # Video details
        st.markdown("### 📹 Video Information")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Title:** {video_info['title']}")
            st.markdown(f"**Uploader:** {video_info['uploader']}")
            st.markdown(f"**Duration:** {format_duration(video_info['duration'])}")
            st.markdown(f"**Views:** {video_info['view_count']:,}")
        
        with col2:
            if video_info['thumbnail']:
                st.image(video_info['thumbnail'], width=300)
        

        feature_col1, feature_col2  = st.columns(2)
        with feature_col1:
            # Format selection
            if hasattr(st.session_state, 'formats') and st.session_state.formats:
                st.markdown("### ⬇️ Download Options")
                
                # Separate video and audio formats
                video_formats = [f for f in st.session_state.formats if f['type'] == 'video+audio']
                audio_formats = [f for f in st.session_state.formats if f['type'] == 'audio-only']
                
                format_type = st.radio("Choose format type:", ["Video + Audio", "Audio Only"])
                
                if format_type == "Video + Audio" and video_formats:
                    formats_to_show = video_formats
                elif format_type == "Audio Only" and audio_formats:
                    formats_to_show = audio_formats
                else:
                    formats_to_show = []
                
                if formats_to_show:
                    # Create format options
                    format_options = []
                    for f in formats_to_show:
                        size_str = format_filesize(f['filesize']) if f['filesize'] else "Unknown size"
                        option = f"{f['quality']} ({f['ext']}) - {size_str}"
                        format_options.append(option)
                    
                    selected_format_idx = st.selectbox(
                        "Select quality:",
                        range(len(format_options)),
                        format_func=lambda x: format_options[x]
                    )
                    
                    selected_format = formats_to_show[selected_format_idx]
                    
                    # Download button
                    # col1, col2, col3 = st.columns([1, 1, 2])
                    
                    # with col1:
                    if st.button("⬇️ Download", type="primary"):
                        st.markdown(f"""
                **Selected Format Details:**
                - Quality: {selected_format['quality']}
                - Format: {selected_format['ext']}
                - Type: {selected_format['type']}
                - Size: {format_filesize(selected_format['filesize']) if selected_format['filesize'] else 'Unknown'}
                """)
                        # Create temporary directory for download
                        temp_dir = tempfile.mkdtemp()
                        
                        with st.spinner("Downloading... Please wait..."):
                            success, message = download_video(
                                st.session_state.url,
                                selected_format['format_id'],
                                temp_dir
                            )
                            
                            if success:
                                st.success(message)
                                
                                # List downloaded files
                                downloaded_files = list(Path(temp_dir).glob("*"))
                                if downloaded_files:
                                    st.markdown("### 📁 Downloaded Files:")
                                    for file_path in downloaded_files:
                                        file_size = format_filesize(file_path.stat().st_size)
                                        st.markdown(f"- **{file_path.name}** ({file_size})")
                                        
                                        # Provide download link
                                        with open(file_path, "rb") as file:
                                            st.download_button(
                                                label=f"💾 Download {file_path.name}",
                                                data=file.read(),
                                                file_name=file_path.name,
                                                mime="application/octet-stream"
                                            )
                            else:
                                st.error(message)
                
                # Format info
                # st.markdown('<div class="quality-info">', unsafe_allow_html=True)
                
                # st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("No formats available for the selected type.")
        with feature_col2: 
            st.markdown("### ⚒️Other options")

            st.subheader("🎯Summarize")
            st.button("Generate Summary",type='primary')

            st.subheader("🗨️ Download Transcript of the video:")
            st.button("Download transcript",type='primary')
            
        st.write("summary will be shown starting here")
            
if __name__ == "__main__":
    main()