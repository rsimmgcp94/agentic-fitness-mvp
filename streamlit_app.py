import streamlit as st
import requests
import time
import os

# Configure the API URL. In production, this should point to your Cloud Run URL.
# For local testing, it defaults to http://localhost:8000
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Agentic Fitness MVP", page_icon="🏋️", layout="centered")

st.title("🏋️ Agentic Fitness MVP")
st.markdown("Upload your photos and goals to get a hyper-personalized, AI-generated fitness plan.")

with st.form("assessment_form"):
    st.header("1. Your Profile & Goals")
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.text_input("Age", placeholder="e.g., 30")
    with col2:
        height = st.text_input("Height", placeholder="e.g., 5'10\"")
    with col3:
        weight = st.text_input("Weight", placeholder="e.g., 180 lbs")
        
    goals = st.text_area("What are your fitness goals?", placeholder="e.g., Build muscle, fix my posture, and get stronger.")
    
    st.header("2. Posture Photos")
    st.markdown("Please upload clear photos of your full body.")
    col_f, col_s, col_b = st.columns(3)
    
    with col_f:
        front_photo = st.file_uploader("Front Photo", type=["jpg", "jpeg", "png", "webp"])
    with col_s:
        side_photo = st.file_uploader("Side Photo", type=["jpg", "jpeg", "png", "webp"])
    with col_b:
        back_photo = st.file_uploader("Back Photo", type=["jpg", "jpeg", "png", "webp"])
        
    submitted = st.form_submit_button("Generate Workout Plan")

if submitted:
    if not all([age, height, weight, goals, front_photo, side_photo, back_photo]):
        st.error("Please fill in all fields and upload all three photos.")
    else:
        with st.spinner("Uploading files and submitting assessment..."):
            try:
                # Prepare the multipart form data
                files = {
                    "front_photo": (front_photo.name, front_photo.getvalue(), front_photo.type),
                    "side_photo": (side_photo.name, side_photo.getvalue(), side_photo.type),
                    "back_photo": (back_photo.name, back_photo.getvalue(), back_photo.type),
                }
                data = {
                    "goals": goals,
                    "age": age,
                    "height": height,
                    "weight": weight,
                }
                
                response = requests.post(f"{API_URL}/submit-assessment", data=data, files=files)
                response.raise_for_status()
                result = response.json()
                plan_id = result.get("plan_id")
                
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to submit assessment: {e}")
                st.stop()
                
        # Polling for results
        status_placeholder = st.empty()
        plan_placeholder = st.empty()
        
        with st.spinner("AI Agents are analyzing your posture and generating your plan. This usually takes 15-30 seconds..."):
            while True:
                try:
                    status_response = requests.get(f"{API_URL}/assessment/{plan_id}")
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    status = status_data.get("status")
                    
                    if status == "completed":
                        status_placeholder.success("Plan generated successfully!")
                        plan_placeholder.markdown(status_data.get("plan", "No plan content returned."))
                        break
                    elif status == "failed":
                        status_placeholder.error(f"Analysis failed: {status_data.get('error', 'Unknown error')}")
                        break
                    else:
                        # Processing or pending
                        time.sleep(2)
                        
                except requests.exceptions.RequestException as e:
                    status_placeholder.error(f"Error checking status: {e}")
                    time.sleep(2)  # don't spam if there's a transient error