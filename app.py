import os
import whisper
from moviepy.editor import VideoFileClip, concatenate_videoclips
import requests
import json
from flask import Flask, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('outputs', exist_ok=True)

def download_video(url, output_path):
    """Download video from URL"""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def transcribe_video(video_path, model_name="base"):
    """Transcribe video using Whisper"""
    model = whisper.load_model(model_name)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_audio.wav")
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    os.system(f'ffmpeg -i "{video_path}" -ar 16000 -ac 1 -b:a 64k -f mp3 "{audio_path}"')
    result = model.transcribe(audio_path)
    
    if os.path.exists(audio_path):
        os.remove(audio_path)
        
    return result['segments']

def get_relevant_segments(transcript, topics, clip_length):
    """Get relevant segments using OpenAI API"""
    prompt = f"""You are an expert video editor. Given a transcript with segments and a list of topics, 
    find relevant segments for each topic. Each clip should be approximately {clip_length} seconds long.

    Topics:
    {topics}

    Guidelines:
    1. For each topic, find the most relevant continuous segment
    2. Each segment should be approximately {clip_length} seconds
    3. Segments should not overlap
    4. Choose segments that provide complete context

    Output format: {{"clips": [{{"topic": "topic1", "start": s1, "end": e1}}, {{"topic": "topic2", "start": s2, "end": e2}}]}}

    Transcript:
    {transcript}"""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }

    data = {
        "messages": [{"role": "system", "content": prompt}],
        "model": "gpt-4-turbo-preview",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    content = response.json()["choices"][0]["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)["clips"]

def create_clip(video_path, start, end, output_path):
    """Create video clip from start to end time"""
    video = VideoFileClip(video_path)
    clip = video.subclip(start, end)
    clip.write_videofile(output_path, codec='libx264')
    video.close()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    """Process video upload and generate clips"""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    session_dir = os.path.join('outputs', session_id)
    os.makedirs(session_dir, exist_ok=True)

    try:
        # Get video file
        if 'video' in request.files and request.files['video'].filename:
            video = request.files['video']
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
            video.save(video_path)
        elif request.form.get('video_url'):
            video_url = request.form['video_url']
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}.mp4")
            download_video(video_url, video_path)
        else:
            return "No video provided", 400

        # Get parameters
        topics = request.form['topics'].split('\n')
        clip_length = int(request.form['clip_length'])

        # Transcribe video
        print("Transcribing video...")
        segments = transcribe_video(video_path)
        
        # Save transcript
        transcript_file = os.path.join(session_dir, 'transcript.txt')
        with open(transcript_file, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}\n")

        # Get relevant segments for each topic
        print("Finding relevant segments...")
        clips_info = get_relevant_segments(segments, topics, clip_length)

        # Create clips
        print("Creating clips...")
        clip_files = []
        for i, clip in enumerate(clips_info):
            output_path = os.path.join(session_dir, f'clip_{i+1}.mp4')
            create_clip(video_path, clip['start'], clip['end'], output_path)
            clip_files.append(os.path.basename(output_path))

        # Clean up
        if os.path.exists(video_path):
            os.remove(video_path)

        return render_template('index.html', 
                            results=True,
                            transcript_file=os.path.basename(transcript_file),
                            clips=clip_files)

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error processing video: {str(e)}", 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    # Find the file in any session directory
    for session_dir in os.listdir('outputs'):
        file_path = os.path.join('outputs', session_dir, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not set in environment variables")
    app.run(debug=True)
