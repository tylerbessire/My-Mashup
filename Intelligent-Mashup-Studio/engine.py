import os
import tempfile
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
import pyrubberband as pyrb

class AudioEngine:
    """
    Renders the final audio track from a mashup recipe.
    FINAL VERSION: Includes high-quality, pitch-independent time-stretching.
    """

    def __init__(self, recipe: dict):
        self.recipe = recipe
        self.stems_base_dir = "workspace/stems"
        self.output_dir = "workspace/mashups"
        os.makedirs(self.output_dir, exist_ok=True)
        self.briefs = {b['song_info']['title']: b for b in self.recipe.get('briefs', [])}
        if not self.briefs:
             raise ValueError("Engine requires creative briefs embedded in the recipe.")

    def _get_stem(self, song_title: str, stem_type: str = "instrumental"):
        filename = "vocals.wav" if stem_type == "vocals" else "no_vocals.wav"
        source_brief = self.briefs.get(song_title)
        if not source_brief:
             raise FileNotFoundError(f"Brief for song '{song_title}' not found in recipe.")
        stem_path = os.path.join(self.stems_base_dir, "htdemucs", os.path.splitext(os.path.basename(source_brief['song_info']['source_file']))[0], filename)
        if not os.path.exists(stem_path):
             main_source_path = source_brief['song_info']['source_file']
             if not os.path.exists(main_source_path):
                 raise FileNotFoundError(f"Fatal: Neither stem nor source audio file found for {song_title}")
             return AudioSegment.from_file(main_source_path)
        return AudioSegment.from_file(stem_path)

    def _get_segment_milliseconds(self, song_title: str, segment_name: str):
        brief = self.briefs[song_title]
        segment_info = brief['analysis_results']['segments'].get(segment_name)
        if not segment_info:
            raise ValueError(f"Segment '{segment_name}' not found in brief for '{song_title}'")
        start_ms = segment_info['start_time'] * 1000
        end_ms = segment_info['end_time'] * 1000
        return int(start_ms), int(end_ms)
        
    def _time_stretch_segment(self, audio_clip: AudioSegment, target_duration_ms: int):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_in_file:
            audio_clip.export(temp_in_file.name, format="wav")
            temp_in_filename = temp_in_file.name
        y, sr = sf.read(temp_in_filename)
        current_duration_ms = len(audio_clip)
        stretch_ratio = current_duration_ms / target_duration_ms
        y_stretched = pyrb.time_stretch(y, sr, stretch_ratio)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_out_file:
             sf.write(temp_out_file.name, y_stretched, sr)
             temp_out_filename = temp_out_file.name
        stretched_segment = AudioSegment.from_file(temp_out_filename)
        os.remove(temp_in_filename)
        os.remove(temp_out_filename)
        return stretched_segment

    def execute_recipe(self):
        print("Executing FINAL recipe with AudioEngine v2.1...")
        final_mashup = AudioSegment.empty()
        for item in self.recipe['timeline']:
            timeline_start_ms, timeline_end_ms = [int(t) for t in item['time_ms'].split('-')]
            timeline_duration_ms = timeline_end_ms - timeline_start_ms
            segment_mix = AudioSegment.silent(duration=timeline_duration_ms)
            for layer, details in item['layers'].items():
                if not details: continue
                source_audio = self._get_stem(details['source'], layer)
                clip_start_ms, clip_end_ms = self._get_segment_milliseconds(details['source'], details['segment'])
                audio_clip = source_audio[clip_start_ms:clip_end_ms]
                if len(audio_clip) > 0 and abs(len(audio_clip) - timeline_duration_ms) > 10:
                    audio_clip = self._time_stretch_segment(audio_clip, timeline_duration_ms)
                if "pitch_shift_semitones" in details:
                    semitones = details.get("pitch_shift_semitones", 0)
                    if semitones != 0:
                        audio_clip = audio_clip._spawn(audio_clip.raw_data, overrides={"frame_rate": int(audio_clip.frame_rate * (2 ** (semitones / 12.0)))}).set_frame_rate(audio_clip.frame_rate)
                segment_mix = segment_mix.overlay(audio_clip)
            final_mashup = final_mashup.append(segment_mix, crossfade=100)
        final_mashup = normalize(final_mashup)
        version = self.recipe.get('version', '2.1')
        output_filename = f"{self.recipe['mashup_title'].replace(' ', '_').replace('vs', '')}_v{version}.wav"
        output_path = os.path.join(self.output_dir, output_filename)
        final_mashup.export(output_path, format="wav")
        return output_filename
