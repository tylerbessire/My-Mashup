import os
from analyzer import AudioAnalyzer
from creator import MashupCreator
from engine import AudioEngine
from reviser import RevisionEngine

def create_mashup_task(job_id, songs, jobs):
    """The main background task for creating a mashup from scratch."""
    try:
        jobs[job_id]["status"] = "processing"
        
        # 1. Download and Analyze all songs
        creative_briefs = []
        for i, song_query in enumerate(songs):
            jobs[job_id]["progress"] = f"Analyzing song {i+1}/{len(songs)}: {song_query['query']}"
            analyzer = AudioAnalyzer(song_query['query'])
            brief = analyzer.full_analysis()
            if not brief:
                raise Exception(f"Analysis failed for {song_query['query']}")
            creative_briefs.append(brief)

        # 2. Create the Mashup Recipe
        jobs[job_id]["progress"] = "Generating creative recipe..."
        director = MashupCreator(creative_briefs)
        recipe = director.create_mashup_recipe()
        
        # 3. Render the audio
        jobs[job_id]["progress"] = "Rendering audio..."
        audio_engine = AudioEngine(recipe)
        output_filename = audio_engine.execute_recipe()
        
        # 4. Finalize job
        mashup_id = os.path.splitext(os.path.basename(output_filename))[0]
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = "Done"
        jobs[job_id]["result"] = {
            "mashup_id": mashup_id,
            "audio_url": f"/api/mashup/audio/{output_filename}",
            "recipe": recipe
        }

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


def revise_mashup_task(job_id, data, jobs):
    """Background task for revising an existing mashup."""
    try:
        jobs[job_id]["status"] = "processing"
        
        # 1. Revise the recipe using the RevisionEngine
        jobs[job_id]["progress"] = "Revising recipe with AI assistant..."
        reviser = RevisionEngine(data['current_recipe'], data['user_command'])
        new_recipe = reviser.revise()

        # 2. Re-render the audio with the new recipe
        jobs[job_id]["progress"] = "Re-rendering audio..."
        audio_engine = AudioEngine(new_recipe)
        output_filename = audio_engine.execute_recipe()
        
        # 3. Finalize Job
        mashup_id = os.path.splitext(os.path.basename(output_filename))[0]
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = "Done"
        jobs[job_id]["result"] = {
            "mashup_id": mashup_id,
            "audio_url": f"/api/mashup/audio/{output_filename}",
            "recipe": new_recipe
        }

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
