import google.generativeai as genai
import os
import json
import logging

logger = logging.getLogger(__name__)

def generate_workout_plan(goals: str, pose_analysis: dict) -> str:
    """
    Calls Gemini to generate a customized workout plan based on the user's goals
    and the raw 3D landmark data extracted from their photos.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is missing.")
        raise ValueError("GEMINI_API_KEY environment variable not set.")
        
    genai.configure(api_key=api_key, transport="rest")  # type: ignore
    
    prompt = f"""
    Role: You are a Senior Sports Physiotherapist and Elite Strength Coach specializing in biomechanical assessment.

    Objective: Analyze the provided client data to identify postural deviations, calculate approximate body composition, and generate a hyper-personalized, injury-preventative fitness and nutrition roadmap.
    
    Input Data Context:
    Client Profile & Goals: 
    {goals}
    
    Pose Landmarks (33 3D points normalized [0.0, 1.0] extracted via Computer Vision): 
    {json.dumps(pose_analysis, indent=2)}
    
    Analysis Workflow (Chain of Thought):
    1. Postural Screening: Evaluate the 3D landmarks for common deviations (e.g., Anterior Pelvic Tilt, Kyphosis, Valgus stress, lateral shifts).
    2. Kinetic Chain Impact: Explain how these postural findings will affect specific movements (e.g., "Tight hip flexors may limit squat depth").
    3. Volume & Intensity Calibration: Based on the goal (e.g., hypertrophy vs. fat loss), determine the optimal caloric deficit/surplus and weekly set volume.

    Output Structure (in beautifully formatted Markdown):
    - Postural Summary: A "Red/Yellow/Green" flag system for joint alignment.
    - The "Pre-hab" Protocol: 2–3 corrective exercises to be done before every workout.
    - Workout Architecture: A structured 4-week plan (Exercises, Sets, Reps, RPE).
    - Nutritional Macro-Targets: Daily Protein, Carbs, and Fats based on TDEE calculations.

    Constraints:
    - Do not suggest exercises that aggravate identified postural issues.
    - Tone should be professional, data-driven, and encouraging.
    """
    
    logger.info("Sending analysis data to Gemini...")
    
    try:
        # Try the standard 1.5 Flash alias first
        model = genai.GenerativeModel('gemini-1.5-flash')  # type: ignore
        response = model.generate_content(prompt)
    except Exception as e:
        logger.warning(f"Primary model failed ({e}). Discovering available models...")
        
        # Dynamically fetch available models that support text generation
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        logger.info(f"Available models for this API key: {available_models}")
        
        if not available_models:
            raise RuntimeError("No suitable generative models found for this API key/region.")
            
        # Safely pick the first available model (stripping 'models/' prefix)
        fallback_model = available_models[0].replace("models/", "")
        logger.info(f"Using dynamic fallback model: {fallback_model}")
        
        model = genai.GenerativeModel(fallback_model)  # type: ignore
        response = model.generate_content(prompt)
    
    return response.text