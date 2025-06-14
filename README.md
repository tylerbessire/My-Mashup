# My-Mashup - Intelligent Music Mashup Studio

An AI-powered audio blending and music creation platform that allows users to create sophisticated audio mashups using advanced machine learning and audio processing techniques.

## Features

- **Intelligent Audio Analysis**: Uses advanced algorithms to analyze audio tracks and determine optimal mixing points
- **AI-Powered Mashup Creation**: Automatically creates seamless blends between multiple tracks
- **Real-time Audio Processing**: Dynamic audio manipulation and effects processing
- **Modern Web Interface**: Intuitive React-based frontend for easy interaction
- **Flexible Backend**: Python Flask API with comprehensive audio processing capabilities

## Architecture

### Backend (Intelligent-Mashup-Studio)
- **Flask API** for handling audio processing requests
- **Audio Analysis Engine** using librosa and advanced signal processing
- **Mashup Creation System** with intelligent tempo and key matching
- **Audio Processing Pipeline** with support for stems separation and effects

### Frontend (Mashup-Studio-Frontend)
- **React Application** with modern UI components
- **Real-time Progress Tracking** for long-running audio processing tasks
- **Interactive Controls** for mashup customization
- **Responsive Design** using Tailwind CSS

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd Intelligent-Mashup-Studio
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install additional audio processing dependencies:
```bash
# For audio separation (optional)
pip install torch torchaudio
pip install demucs
pip install openai-whisper
```

4. Run the Flask server:
```bash
python app.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd Mashup-Studio-Frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## Usage

1. Start both backend and frontend servers
2. Open your browser to `http://localhost:3000`
3. Upload audio files you want to mashup
4. Configure mashup parameters (tempo, key, mixing points)
5. Process and download your custom mashup

## API Endpoints

### POST /api/mashup/create
Creates a new mashup from provided audio tracks.

**Request Body:**
```json
{
  "songs": [
    "path/to/song1.mp3",
    "path/to/song2.mp3"
  ],
  "options": {
    "tempo_sync": true,
    "key_match": true,
    "fade_duration": 3.0
  }
}
```

**Response:**
```json
{
  "job_id": "mashup_job_uuid",
  "status": "pending",
  "progress": "queued"
}
```

### GET /api/mashup/status/{job_id}
Check the status of a mashup creation job.

### POST /api/mashup/revise
Revise an existing mashup with new parameters.

## Dependencies

### Backend
- Flask 2.3.2
- librosa 0.10.0
- pydub 0.25.1
- yt-dlp 2023.7.6
- scipy >= 1.8.0
- numpy >= 1.21.0
- pyrubberband 0.3.0
- openai 1.3.3

### Frontend
- React 18.3.1
- axios 1.6.8
- lucide-react 0.378.0
- Tailwind CSS 3.4.3

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with advanced audio processing libraries
- Inspired by modern music production techniques
- Designed for both casual users and audio professionals
