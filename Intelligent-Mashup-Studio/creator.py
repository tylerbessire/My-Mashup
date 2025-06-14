import numpy as np
from scipy.signal import correlate2d

class MashupCreator:
    """
    Turns analytical data into a creative mashup plan.
    ROBUST VERSION: Uses a "mashability" score based on the AutoMashUpper paper
    to find the best segment pairings between songs.
    """

    def __init__(self, creative_briefs: list):
        if len(creative_briefs) < 2:
            raise ValueError("MashupCreator requires at least two creative briefs.")
        self.briefs = {b['song_info']['title']: b for b in creative_briefs}
        self.primary_title, self.secondary_title = self._select_roles()

    def _select_roles(self):
        tempos = {title: b['analysis_results']['tempo'] for title, b in self.briefs.items()}
        primary = max(tempos, key=tempos.get)
        secondary = min(tempos, key=tempos.get)
        return primary, secondary
    
    def _calculate_mashability(self, seg1_features, seg2_features):
        chroma1 = seg1_features['chroma']
        chroma2 = seg2_features['chroma']
        chroma2_padded = np.vstack([chroma2, chroma2])
        corr = correlate2d(chroma2_padded, chroma1, mode='valid')
        norm1 = np.linalg.norm(chroma1)
        norm2 = np.linalg.norm(chroma2)
        harmonic_sim = np.max(corr) / (norm1 * norm2 + 1e-9)
        
        rhythm1 = seg1_features['rhythm'].flatten()
        rhythm2 = seg2_features['rhythm'].flatten()
        rhythmic_sim = np.dot(rhythm1, rhythm2) / (np.linalg.norm(rhythm1) * np.linalg.norm(rhythm2) + 1e-9)

        spec1 = seg1_features['spectral']
        spec2 = seg2_features['spectral']
        combined_spec = np.mean(spec1 + spec2, axis=1)
        normalized_spec = combined_spec / (np.sum(combined_spec) + 1e-9)
        spectral_balance = 1 - np.std(normalized_spec)

        w_h, w_r, w_l = 1.0, 0.2, 0.2
        mashability_score = (w_h * harmonic_sim) + (w_r * rhythmic_sim) + (w_l * spectral_balance)
        
        return mashability_score

    def create_mashup_recipe(self):
        print("Starting robust recipe creation...")
        
        primary_brief = self.briefs[self.primary_title]
        secondary_brief = self.briefs[self.secondary_title]

        timeline = []
        
        for seg_name, p_seg_info in primary_brief['analysis_results']['segments'].items():
            best_match = {"seg_name": None, "score": -1}

            p_start, p_end = p_seg_info['start_beat'], p_seg_info['end_beat']
            p_features = {
                "chroma": np.array(primary_brief['analysis_results']['features_v2']['beat_synchronous_chroma'])[:, p_start:p_end],
                "rhythm": np.array(primary_brief['analysis_results']['features_v2']['rhythmic_representation'])[:, p_start:p_end],
                "spectral": np.array(primary_brief['analysis_results']['features_v2']['spectral_balance'])[:, p_start:p_end]
            }

            for s_seg_name, s_seg_info in secondary_brief['analysis_results']['segments'].items():
                s_start, s_end = s_seg_info['start_beat'], s_seg_info['end_beat']
                
                if abs((p_end - p_start) - (s_end - s_start)) > 8: continue

                s_features = {
                    "chroma": np.array(secondary_brief['analysis_results']['features_v2']['beat_synchronous_chroma'])[:, s_start:s_end],
                    "rhythm": np.array(secondary_brief['analysis_results']['features_v2']['rhythmic_representation'])[:, s_start:s_end],
                    "spectral": np.array(secondary_brief['analysis_results']['features_v2']['spectral_balance'])[:, s_start:s_end]
                }
                
                if p_features['chroma'].shape[1] == 0 or s_features['chroma'].shape[1] == 0: continue
                if p_features['chroma'].shape[1] != s_features['chroma'].shape[1]:
                     s_features['chroma'] = np.resize(s_features['chroma'], p_features['chroma'].shape)

                score = self._calculate_mashability(p_features, s_features)
                
                if score > best_match['score']:
                    best_match['score'] = score
                    best_match['seg_name'] = s_seg_name
            
            if best_match['seg_name']:
                timeline.append({
                    "time_ms": f"{int(p_seg_info['start_time']*1000)}-{int(p_seg_info['end_time']*1000)}",
                    "description": f"Pairing {seg_name} with {best_match['seg_name']}",
                    "layers": {
                        "instrumental": {"source": self.primary_title, "segment": seg_name},
                        "vocals": {"source": self.secondary_title, "segment": best_match['seg_name']}
                    }
                })

        recipe = {
            "version": 2,
            "mashup_title": f"{self.primary_title} vs {self.secondary_title}",
            "concept": "A robustly generated mashup based on harmonic, rhythmic, and spectral compatibility.",
            "target_tempo": primary_brief['analysis_results']['tempo'],
            "target_key": primary_brief['analysis_results']['estimated_key'],
            "timeline": timeline,
            "briefs": [primary_brief, secondary_brief]
        }
        
        return recipe
