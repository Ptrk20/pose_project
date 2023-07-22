### Import Libraries ###
import tkinter as tk
from tkinter import *
import subprocess
import io
from PIL import ImageTk
from PIL import Image
import cv2
import lib
from ml import Movenet
import argparse
import logging
import sys
import time
import utils
from tkinter import messagebox
from ml import Classifier
import pyttsx3
import pygame
from collections import Counter
from tkinter import PhotoImage

### Initialization of variables ###
main_window = tk.Tk()
main_window.title("Mov4Break")
main_window.geometry('1400x700')
main_window.resizable(False, False)
lib.center_window(main_window)

### Initialization of images 
background_image = PhotoImage(file="Resources/bg.png")
start_image = PhotoImage(file="Resources/start.png")
exit_image = PhotoImage(file="Resources/exit.png")
on_image = PhotoImage(file="Resources/on.png")
off_image = PhotoImage(file="Resources/off.png")
cam_image = PhotoImage(file="Resources/cam.png")
clock_image = PhotoImage(file="Resources/clock.png")
logo_image = PhotoImage(file="Resources/logo.png")
start_timer_image = PhotoImage(file="Resources/start_timer.png")
stop_timer_image = PhotoImage(file="Resources/stop_timer.png")
reset_timer_image = PhotoImage(file="Resources/reset_timer.png")
end_session_image = PhotoImage(file="Resources/end_session.png")

### Set background image
background_label = tk.Label(main_window, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

### variables for cam toggle button
button_state = tk.IntVar()
button_state.set(1)

### variables for timer toggle button
timer_state = tk.IntVar()
timer_state.set(0)

camera_running = True
timer_stopped = False

### Remaining Time: 30 minutes x 60 seconds
remaining_time = 1 * 60

current_class_detected = ""
tensions_by_second = []

tensions_detected = []

### Open the video capture ###
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def update_camera():
	global current_class_detected
	
	estimation_model = "movenet_thunder"
	pose_detector = Movenet(estimation_model)
	
	# Variables to calculate FPS
	counter, fps = 0, 0
	start_time = time.time()

	# Visualization parameters
	row_size = 20  # pixels
	left_margin = 24  # pixels
	text_color = (0, 0, 255)  # red
	font_size = 1
	font_thickness = 1
	classification_results_to_show = 3
	fps_avg_frame_count = 30
	keypoint_detection_threshold_for_classifier = 0.7
	classifier = None
	
	### ------------ Classification Model -------------- ###
	classification_model = "sitting_f.tflite"  
	label_file = "new_sitting.txt"
	
	counter = 0

	# Initialize the classification model
	if classification_model:
		classifier = Classifier(classification_model, label_file)
		classification_results_to_show = min(classification_results_to_show,len(classifier.pose_class_names))
		
	ret, frame = cap.read()
	if not ret:
		sys.exit('ERROR: Unable to read from webcam. Please verify your webcam settings.')
		
	counter += 1
	frame = cv2.flip(frame, 1)
	list_persons = [pose_detector.detect(frame)]
		
	# Draw keypoints and edges on input image
	frame = utils.visualize(frame, list_persons)
		
	if classifier:
		# Check if all keypoints are detected before running the classifier.
		# If there's a keypoint below the threshold, show an error.
		person = list_persons[0]
		min_score = min([keypoint.score for keypoint in person.keypoints])
		detections = []
		className = []
		### You can remove this 'if' condition if you don't requires all keypoints are shown in camera 
		if min_score < keypoint_detection_threshold_for_classifier:
			error_text = 'Some keypoints are not detected.'
			log.config(text=error_text)
			text_location = (left_margin, 2 * row_size)
			cv2.putText(frame, error_text, text_location, cv2.FONT_HERSHEY_PLAIN,font_size, text_color, font_thickness)
			error_text = 'Make sure the person is fully visible in the camera.'
			text_location = (left_margin, 3 * row_size)
			cv2.putText(frame, error_text, text_location, cv2.FONT_HERSHEY_PLAIN,font_size, text_color, font_thickness)
		else:
			# Run pose classification
			prob_list = classifier.classify_pose(person)
			
			# Show classification results on the image
			for i in range(classification_results_to_show):
				class_name = prob_list[i].label
				probability = round(prob_list[i].score, 2)
				result_text = class_name + ' (' + str(probability) + ')'
				text_location = (left_margin, (i + 2) * row_size)
				
				### This will add detection in a list by frame
				detections.append(result_text)
				if class_name != '': 
					className.append(class_name)
				
				### Use this condition if you want to get only class with probabilty to 1.0 
				# if probability == 1.0:
				# 		detections.append(class_name)
					
				cv2.putText(frame, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,font_size, text_color, font_thickness)
			
			### Display in logs the class detected by frame
			log.config(text=detections)
			current_class_detected = className[0]
			
					
	# Calculate the FPS
	if counter % fps_avg_frame_count == 0:
		end_time = time.time()
		fps = fps_avg_frame_count / (end_time - start_time)
		start_time = time.time()
			
	# Show the FPS
	fps_text = 'FPS = ' + str(int(fps))
	text_location = (left_margin, row_size)
	cv2.putText(frame, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN,font_size, text_color, font_thickness)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		
	# Create an ImageTk object from the frame
	image = Image.fromarray(frame)
	photo = ImageTk.PhotoImage(image)
		
	# Update the canvas with the new image
	camera.config(image=photo)
	camera.image = photo
		
	# Keep updating the video display
	#cv2.imshow(estimation_model, frame)
	main_window.after(15, update_camera)
		      
def close():
	# Release the video capture and destroy the window
    cap.release()
    main_window.destroy()
    
def camera_toggle():
	### Function for camera toggle button
	global camera_running
	if button_state.get() == 0:
	   cam_button.config(image=on_image)
	   button_state.set(1)
	   camera.place(x=20,y=80)

	else:
	   cam_button.config(image=off_image)
	   button_state.set(0)
	   camera.place_forget()

def timer_toggle():
	### Function for timer toggle button
	global timer_stopped
	global timer_state
	if timer_state.get() == 0:
	   timer_button.config(image=stop_timer_image)
	   timer_stopped = False
	   start_timer()
	   timer_state.set(1)
	   text_to_speech("Timer, Started")
	else:
	   timer_button.config(image=start_timer_image)
	   timer_state.set(0)
	   timer_stopped = True
	   start_timer()
	   text_to_speech("Timer, Stopped")
	   
def reset_timer():
	global timer_stopped
	global remaining_time
	global timer_state
	
	timer_state.set(0)
	timer_stopped = True
	remaining_time = 30 * 60
	timer_button.config(image=start_timer_image)
	lib.create_label(main_window,"Timer: 30:00",800,50,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")
	start_timer()
	   
def start_timer():
	
	def update_timer():
		global remaining_time
		global timer_stopped
		global tensions_detected
		global tensions_by_second
		global current_class_detected
	
		minutes = remaining_time // 60
		seconds = remaining_time % 60
		lib.create_label(main_window,f"Timer: {minutes:02d}:{seconds:02d}",800,50,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")
		
		if remaining_time > 0 and timer_stopped == False:
			remaining_time -= 1
			if current_class_detected != "":
				tensions_by_second.append(current_class_detected)
			main_window.after(1000, update_timer)
			
		elif remaining_time == 0:
			sound_path = "/home/pi/project/Mov4Break/Sound/AlarmSound.mp3"
			play_sound(sound_path)
			timer_stopped = True
			remaining_time = 30 * 60
			timer_button.config(image=start_timer_image)
			timer_state.set(0)
			lib.create_label(main_window,"Timer: 30:00",800,50,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")
			get_tensions_detected()
			notif()
			
		else:
			timer_stopped = True
			
			
	def stop_timer():
		global timer_stopped
		timer_stopped = True
		
	update_timer()
    
def notif():
	### Function for messagebox
	global tensions_detected
	notif_message = ""
	
	if len(tensions_detected)==0:
		notif_message = "The system didn't detect any tensions in your body"
		messagebox.showinfo("Mov4Break", notif_message)
	else:
		notif_message = f"The system detected tensions in your {tensions_detected}. We prepare stretches that specific on the tensions detected. Would you like to start stretching?"
		result = messagebox.askokcancel("Attention", notif_message)
		
		if result:
			subprocess.Popen(['python3', 'stretching_win.py',str(tensions_detected)])
			main_window.destroy()
	
def end_session():
	result = messagebox.askokcancel("Attention", "Do you want to end the session?")
	if result:
		main_window.destroy()
	
def text_to_speech(text):
	### Function for text to speech
	subprocess.call(['espeak', text])

def play_sound(file_path):
	### Function for playing sounds
	pygame.mixer.init()
	pygame.mixer.music.load(file_path)
	pygame.mixer.music.play()

def get_tensions_detected():
	### Function for summarize improper sittins detected per second in 30 mins
	global tensions_by_second
	global tensions_detected
	
	### ----------- Sample Code ---------- ###
	### To be updated based on your conditions
	tensions_count = Counter(tensions_by_second)
	sorted_tension_class = sorted(tensions_count.items())
	
	
	for tension, count in sorted_tension_class:
		### If improper sitting detected 5 times in 30 mins (means detected 5 seconds total time: 1count:1sec), add in tensions detected
		if count > 5:
			### get tension category
			tension = classify_tension(tension)
			
			### add in tensions detected
			tensions_detected.append(tension)

def classify_tension(imp_sitting):
	### sample code to categorize tension based on improper sitting detected
	tension = ""
	
	if imp_sitting == "hunched_forward" or imp_sitting == "leaning_backward":
		tension = "Neck"
	if imp_sitting == "hunched_forward" or imp_sitting == "leaning_backward":
		tension = "Shoulder"
	if imp_sitting == "hunched_forward" or imp_sitting == "leaning_backward":
		tension = "Spine"
	if imp_sitting == "hunched_forward" or imp_sitting == "leaning_backward":
		tension = "Hip"
	if imp_sitting == "feet_on_chair" or imp_sitting == "knee extension":
		tension = "Knee"
	if imp_sitting == "hunched_forward" or imp_sitting == "leaning_backward" or "feet_on_chair" or imp_sitting == "knee extension":
		tension = "Wrist"
	else:
		tension = imp_sitting
	
	return tension
	
### camera view ###
camera = tk.Label(main_window, border=2)
camera.place(x=20,y=80)

### camera Toggle Button ###
button_font = ("Helvetica", 12, 'bold')
cam_button = tk.Button(main_window, bd=0, command=camera_toggle, image=on_image,bg='black',activebackground='black')
cam_button.place(x=75, y=600)

cam_icon = tk.Label(main_window, image=cam_image, bd=0, bg='black')
cam_icon.place(x=20, y=600)

clock_icon = tk.Label(main_window, image=clock_image, bd=0, bg='black')
clock_icon.place(x=700, y=50)

logo = tk.Label(main_window, image=logo_image, bd=0, bg='black')
logo.place(x=20, y=10)

### result text ###
label_font = ("Arial", 20, 'normal')
log = tk.Label(main_window, text="",width=45,height=10, font=label_font, borderwidth=2, relief="groove", anchor="nw")
log.place(x=700, y=220)

### timer text ###
lib.create_label(main_window,f"Timer: 30:00",800,50,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")

### Timer Toggle Button ###
timer_button = tk.Button(main_window, bd=0,image=start_timer_image, bg='black',activebackground='black', command=timer_toggle)
timer_button.place(x=1050, y=140)

### Reset Timer Toggle Button ###
reset_timer_button = tk.Button(main_window, bd=0,image=reset_timer_image, bg='black',activebackground='black', command=reset_timer)
reset_timer_button.place(x=900, y=142)

### End Session Button ###
endSession_button = tk.Button(main_window, bd=0,image=end_session_image, bg='black',activebackground='black', command=end_session)
endSession_button.place(x=1200, y=600)

### Start the video display ###
update_camera()
main_window.protocol("WM_DELETE_WINDOW", close)

# Run the Tkinter event loop
main_window.mainloop()
