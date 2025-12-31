import threading
import customtkinter as ctk
import speech_recognition as sr
import pyttsx3
import pywhatkit
import psutil
import datetime
import os
import time
import cv2
from PIL import Image, ImageTk
from google import genai
from AppOpener import open as open_app

# --- CONFIGURATION ---
API_KEY = "AIzaSyDsdFdIRn_5AfYFIJgqO2jeQoEqaOHwgak"  # <--- PASTE YOUR KEY HERE
OWNER_PHOTO = "owner.jpg"      # <--- Make sure this file exists!

# --- SETUP AI & VOICE ---
client = genai.Client(api_key=API_KEY)
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
engine.setProperty('rate', 190)

# --- GLOBAL VARIABLES ---
app = None
status_label = None
chat_log = None
camera_label = None
cap = None
current_frame_pil = None
owner_image_pil = None

def speak(text):
    """Updates GUI Log and speaks"""
    global chat_log
    if chat_log:
        chat_log.configure(state="normal")
        chat_log.insert("end", f"JARVIS: {text}\n")
        chat_log.configure(state="disabled")
        chat_log.see("end")
    threading.Thread(target=lambda: _speak_thread(text), daemon=True).start()

def _speak_thread(text):
    engine.say(text)
    engine.runAndWait()

def load_owner_photo():
    """Loads the reference photo for security"""
    global owner_image_pil
    if os.path.exists(OWNER_PHOTO):
        owner_image_pil = Image.open(OWNER_PHOTO)
        print("Security: Owner photo loaded.")
    else:
        print("Security Warning: owner.jpg not found!")
        speak("Security warning. Reference photo not found.")

def authenticate_user():
    """Biometric Scan using Gemini Vision"""
    global current_frame_pil, owner_image_pil
    
    if not owner_image_pil:
        speak("Authentication failed. No reference photo.")
        return

    if current_frame_pil:
        speak("Scanning biometric data...")
        if status_label:
            status_label.configure(text="VERIFYING ID...", text_color="orange")
        
        try:
            # Send BOTH images to Gemini for comparison
            prompt = "Look at these two images. Image 1 is the Master User. Image 2 is the Current User. Are they the same person? Answer exactly 'MATCH' or 'NO MATCH' followed by a short reason."
            
            response = client.models.generate_content(
                model="gemini-2.5-flash", # Use the stable vision model
                contents=[prompt, owner_image_pil, current_frame_pil]
            )
            
            result = response.text
            
            if "MATCH" in result.upper() and "NO MATCH" not in result.upper():
                speak("Identity verified. Welcome back, Arya.")
                if status_label:
                    status_label.configure(text="ACCESS GRANTED", text_color="#00ff00") # Green
            else:
                speak("Access denied. User not recognized.")
                if status_label:
                    status_label.configure(text="ACCESS DENIED", text_color="red") # Red
                    
        except Exception as e:
            speak("Biometric sensor error.")
            print(f"Error: {e}")
    else:
        speak("Camera unavailable.")

def listen():
    """Listens for voice commands"""
    global status_label
    r = sr.Recognizer()
    with sr.Microphone() as source:
        if status_label: status_label.configure(text="LISTENING", text_color="#00ff00")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            if status_label: status_label.configure(text="PROCESSING", text_color="#00ccff")
            command = r.recognize_google(audio)
            
            if chat_log:
                chat_log.configure(state="normal")
                chat_log.insert("end", f"USER: {command}\n")
                chat_log.configure(state="disabled")
                chat_log.see("end")
            return command.lower()
        except Exception:
            if status_label: status_label.configure(text="STANDBY", text_color="gray")
            return ""

def jarvis_brain():
    """Main Logic Loop"""
    time.sleep(2)
    load_owner_photo()
    speak("Security protocol active. State your command.")
    
    chat = client.chats.create(model="gemini-2.5-flash")

    while True:
        user_input = listen()
        if not user_input: continue
        
        # --- COMMANDS ---
        if user_input in ["exit", "quit", "shutdown"]:
            speak("Shutting down.")
            if cap: cap.release()
            os._exit(0)

        elif "verify" in user_input or "who am i" in user_input or "scan me" in user_input:
            authenticate_user() # Trigger Face ID via Voice

        elif "see" in user_input or "look" in user_input:
            # Vision Analysis (What is this?)
            if current_frame_pil:
                speak("Analyzing environment...")
                try:
                    res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=["Describe this image concisely.", current_frame_pil]
                    )
                    speak(res.text)
                except: speak("Visual error.")

        elif "open" in user_input:
            app_name = user_input.replace("open", "").strip()
            speak(f"Opening {app_name}")
            open_app(app_name, match_closest=True)
        
        elif "play" in user_input:
            song = user_input.replace("play", "").strip()
            pywhatkit.playonyt(song)

        else:
            try:
                response = chat.send_message(user_input)
                speak(response.text)
            except Exception as e: print(e)

def update_camera():
    global current_frame_pil, cap
    if cap and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            current_frame_pil = Image.fromarray(frame_rgb)
            img_ctk = ctk.CTkImage(current_frame_pil, size=(320, 240))
            if camera_label:
                camera_label.configure(image=img_ctk)
                camera_label.image = img_ctk
    if app: app.after(30, update_camera)

def start_gui():
    global app, status_label, chat_log, camera_label, cap

    cap = cv2.VideoCapture(0)
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")

    app = ctk.CTk()
    app.title("J.A.R.V.I.S. SECURITY PROTOCOL")
    app.geometry("950x600")
    
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(1, weight=1)

    # HEADER
    ctk.CTkLabel(app, text="J.A.R.V.I.S. BIOMETRIC INTERFACE", font=("Orbitron", 26, "bold"), text_color="#00ccff").grid(row=0, columnspan=3, pady=15)

    # CENTER PANEL (CAMERA + SECURITY)
    center_frame = ctk.CTkFrame(app)
    center_frame.grid(row=1, column=1, padx=20, pady=20)
    
    ctk.CTkLabel(center_frame, text="VISUAL SENSOR", font=("Roboto", 14, "bold")).pack(pady=5)
    
    # Status
    status_label = ctk.CTkLabel(center_frame, text="UNAUTHORIZED", font=("Orbitron", 20), text_color="red")
    status_label.pack(pady=5)

    # Camera Feed
    camera_label = ctk.CTkLabel(center_frame, text="[CONNECTING CAM...]", width=320, height=240)
    camera_label.pack(pady=10)

    # Buttons
    btn_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
    btn_frame.pack(pady=10)
    
    scan_btn = ctk.CTkButton(btn_frame, text="VERIFY IDENTITY", command=authenticate_user, fg_color="#00ccff", text_color="black", width=150)
    scan_btn.pack(side="left", padx=10)
    
    exit_btn = ctk.CTkButton(btn_frame, text="SHUTDOWN", command=lambda: os._exit(0), fg_color="#ff3333", width=100)
    exit_btn.pack(side="left", padx=10)

    # LOG PANEL (Bottom)
    chat_log = ctk.CTkTextbox(app, height=150, font=("Consolas", 12))
    chat_log.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=20)

    # START THREADS
    threading.Thread(target=jarvis_brain, daemon=True).start()
    update_camera()

    app.mainloop()

if __name__ == "__main__":
    start_gui()