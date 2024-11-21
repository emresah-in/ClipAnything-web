# ClipAnything Web

A web application for intelligent video processing, transcription, and clip generation using AI technologies.

## Features

- Video Upload or URL Input
- AI-powered Video Transcription
- Topic-based Clip Generation
- Customizable Clip Length
- Transcript and Clip Downloads

## Prerequisites

- Python 3.12
- FFmpeg installed and in system PATH
- OpenAI API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ClipAnything-web
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open a web browser and navigate to `http://localhost:5000`

3. Upload a video file or provide a video URL

4. Specify:
   - Number of clips to generate
   - Topics for clip generation
   - Desired clip length

5. Click "Process Video" and wait for the results

6. Download the generated transcript and clips

## Technical Details

- Uses OpenAI Whisper for video transcription
- Leverages GPT-4 for intelligent clip selection
- MoviePy for video processing
- Flask web framework
- Secure file handling and unique session management

## Limitations

- Maximum file size: 500MB
- Requires stable internet connection for API calls
- Processing time depends on video length and complexity

## Security Notes

- API keys should be kept secure
- Temporary files are automatically cleaned up
- Input validation and secure filename handling implemented

## License

[Your License Here]
