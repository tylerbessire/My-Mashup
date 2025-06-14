import os
import subprocess
import librosa
import numpy as np

class AudioAnalyzer:
    """
    Analyzes a single audio track to produce a detailed Creative Brief.
    ROBUST VERSION: Extracts detailed features for advanced mashability scoring.
    """

    def __init__(self, song_query: str):
        self.song_query = song_query
        self.workspace_dir = "workspace/audio_sources"
        os.makedirs(self.workspace_dir, exist_ok=True)

    def _download_song(self):
        print(f"Downloading '{self.song_query}'...")
        output_template = os.path.join(self.workspace_dir, "%(title)s.%(ext)s")
        command = ["yt-dlp", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0", "-o", output_template, "ytsearch1:" + self.song_query]
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
            for line in result.stdout.splitlines():
                if "[ExtractAudio] Destination:" in line:
                    filepath = line.split("Destination:")[1].strip()
                    if os.path.exists(filepath): return filepath
            raise FileNotFoundError("Could not determine downloaded file path.")
        except Exception as e:
            print(f"Error downloading song: {e}")
            return None

    def full_analysis(self):
        """Runs the full analysis pipeline and returns the complete Creative Brief."""
        audio_path = self._download_song()
        if not audio_path: return None

        self.audio_path = audio_path
        self.file_name = os.path.splitext(os.path.basename(audio_path))[0]
        self.y, self.sr = librosa.load(self.audio_path, sr=44100, duration=240)
        self.tempo, self.beats = librosa.beat.beat_track(y=self.y, sr=self.sr)
        self.beat_times = librosa.frames_to_time(self.beats, sr=self.sr)

        print(f"Starting robust analysis for {self.file_name}...")
        
        brief = {
            "song_info": {"title": self.file_name, "source_file": self.audio_path},
            "analysis_results": {
                "tempo": float(f"{self.tempo:.2f}"),
                "estimated_key": self._analyze_key(),
                "segments": self._analyze_structure(),
                "lyrics": self._transcribe_lyrics(),
                "features_v2": {
                    "beat_synchronous_chroma": self._extract_beat_synchronous_chroma().tolist(),
                    "rhythmic_representation": self._extract_rhythmic_representation().tolist(),
                    "spectral_balance": self._extract_spectral_balance().tolist()
                }
            }
        }
        print(f"Robust analysis for {self.file_name} complete.")
        return brief

    def _analyze_key(self):
        chroma = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        key_vals = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        return key_vals[np.argmax(np.sum(chroma, axis=1))]

    def _analyze_structure(self):
        chroma = librosa.feature.chroma_cqt(y=self.y, sr=self.sr)
        boundaries = librosa.segment.agglomerative(chroma, k=10)
        segment_times = librosa.frames_to_time(boundaries, sr=self.sr)
        segments = {}
        for i, start_time in enumerate(segment_times):
            end_time = segment_times[i + 1] if i + 1 < len(segment_times) else librosa.get_duration(y=self.y, sr=self.sr)
            start_beat_idx = np.searchsorted(self.beat_times, start_time)
            end_beat_idx = np.searchsorted(self.beat_times, end_time)
            segments[f"segment_{i+1}"] = {
                "start_time": start_time, 
                "end_time": end_time,
                "start_beat": int(start_beat_idx),
                "end_beat": int(end_beat_idx)
            }
        return segments
    
    def _transcribe_lyrics(self):
        # This is a placeholder for the heavy Whisper/Demucs process
        return "Lyrics would be transcribed here."

    def _extract_beat_synchronous_chroma(self):
        chroma = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        beat_chroma = librosa.util.sync(chroma, self.beats, aggregate=np.median)
        return beat_chroma

    def _extract_rhythmic_representation(self):
        onset_env = librosa.onset.onset_detect(y=self.y, sr=self.sr, aggregate=True)
        y_h, y_p = librosa.effects.hpss(self.y)
        kick_env = librosa.onset.onset_detect(y=y_p, sr=self.sr, fmax=150, aggregate=True)
        snare_env = librosa.onset.onset_detect(y=y_h, sr=self.sr, fmin=200, fmax=2000, aggregate=True)
        sub_beats_per_beat = 12
        rhythmic_feature = np.zeros((2, len(self.beats) * sub_beats_per_beat))
        times = librosa.times_like(onset_env, sr=self.sr)
        for i in range(len(self.beats) - 1):
            start_time = self.beat_times[i]
            end_time = self.beat_times[i+1]
            beat_duration = end_time - start_time
            for j in range(sub_beats_per_beat):
                sub_beat_time = start_time + (j / sub_beats_per_beat) * beat_duration
                frame_idx = np.argmin(np.abs(times - sub_beat_time))
                global_sub_beat_idx = i * sub_beats_per_beat + j
                rhythmic_feature[0, global_sub_beat_idx] = kick_env[frame_idx]
                rhythmic_feature[1, global_sub_beat_idx] = snare_env[frame_idx]
        return rhythmic_feature.reshape(2, len(self.beats), sub_beats_per_beat).mean(axis=0).T

    def _extract_spectral_balance(self):
        S = np.abs(librosa.stft(self.y))
        freqs = librosa.fft_frequencies(sr=self.sr)
        low_band = (freqs < 220)
        mid_band = (freqs >= 220) & (freqs < 1760)
        high_band = (freqs >= 1760)
        low_power = librosa.power_to_db(np.sum(S[low_band, :], axis=0), ref=np.max)
        mid_power = librosa.power_to_db(np.sum(S[mid_band, :], axis=0), ref=np.max)
        high_power = librosa.power_to_db(np.sum(S[high_band, :], axis=0), ref=np.max)
        spectral_bands = np.vstack([low_power, mid_power, high_power])
        beat_spectral_balance = librosa.util.sync(spectral_bands, self.beats, aggregate=np.mean)
        return beat_spectral_balance
