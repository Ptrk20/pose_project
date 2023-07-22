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
import os
import sys
from ml import Classifier
from tkinter import messagebox
import pyttsx3
import pygame
from tkinter import PhotoImage

### Initialization of variables ###
stretch_window = tk.Tk()
stretch_window.title("Mov4Break")
stretch_window.geometry('1400x800')
stretch_window.resizable(False, False)
lib.center_window(stretch_window)

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
background_label = tk.Label(stretch_window, image=background_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)

stretch_path = "/home/pi/project/Mov4Break/Stretches"
tension_detected = eval(sys.argv[1])
print(tension_detected)

current_stretch = 0
current_tension = 0

stretch_detected = False

button_state = tk.IntVar()
button_state.set(1)
camera_running = True

timer_stopped = True
prepareStretch_stopped = False
remaining_time = 15
prepareStretch_remaining_time = 3


### Open the video capture ###
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def stretch_toDo(tension):
	stretches = []
	stretch_name = []
	if tension == "Neck":
		stretches = ["neck_extension"]
		stretch_name = ["Neck Extension"]
	elif tension == "Shoulder":
		stretches = ["side_stretch"]
		stretch_name = ["Left Side Stretch", "Right Side Stretch"]
	elif tension == "Spine":
		stretches = ["side_stretch"]
		stretch_name = ["Side Stretch"]
	elif tension == "Hip":
		stretches = ["hamstring_stretch"]
		stretch_name = ["Left Hamstring Stretch","Right Hamstring Stretch"]
	elif tension == "Knee":
		stretches = ["single_leg_balance", "hamstring_stretch"]
		stretch_name = ["Left Single Leg Balance","Right Single Leg Balance","Left Standing Hamstring Stretch","Right Standing Hamstring Stretch"]
	elif tension == "Wrist":
		stretches = ["standing_prayer"]
		stretch_name = ["Left Standing Prayer","Right Standing Prayer"]
	else:
		stretches = []
		stretch_name = []
	
	return stretches, stretch_name	
	
def start_timer():
	
	def update_timer():
		global remaining_time
		global timer_stopped
		global tensions_detected
		global current_stretch
		
		minutes = remaining_time // 60
		seconds = remaining_time % 60
		lib.create_label(stretch_window,f"Timer: {minutes:02d}:{seconds:02d}",850,20,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")
		
		if remaining_time > 0 and timer_stopped == False:
			remaining_time -= 1
			stretch_window.after(1000, update_timer)
		elif remaining_time == 0:
			timer_stopped = True
			remaining_time = 15
			lib.create_label(stretch_window,"Timer: 00:15",850,20,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")
			current_stretch += 1
			next_stretch()
		else:
			timer_stopped = True
				
	def stop_timer():
		global timer_stopped
		timer_stopped = True
		
	update_timer()

def next_stretch():
	global stretch_path
	global tension_detected
	global current_stretch
	global current_tension
	global prepareStretch_stopped
	
	tension_count = len(tension_detected)
	
	if current_tension < tension_count:
		file_names = os.listdir(stretch_path + "/" + tension_detected[current_tension])
		stretch_count = len(file_names)
		stretchCode, stretchName = stretch_toDo(tension_detected[current_tension])
		exercise.config(text="Exercise for: "+ tension_detected[current_tension] + " tension")
		
		if current_stretch < stretch_count:
			### change image ###
			image = Image.open(stretch_path + "/" + tension_detected[current_tension] + "/" + stretchCode[current_stretch] + ".jpg")
			resized_image = image.resize((600,400), Image.LANCZOS)
			photo = ImageTk.PhotoImage(resized_image)
			stretch_image.config(image=photo)
			stretch_image.image = photo
			stretch_name.config(text=stretchName[current_stretch])
			text_to_speech(stretchName[current_stretch])
			prepareStretch_stopped = False
			prepareToStretch_Timer()
		else:
			current_tension += 1
			current_stretch = 0
			next_stretch()
	else:
		exercise.config(text="Exercise Completed")
		current_stretch = 0
		current_tension = 0
		prepareStretch_stopped = False
		notif()
		
def update_camera():
	global tension_detected
	global current_tension
	global current_stretch
	global timer_stopped
	global prepareStretch_stopped
	
	tension_count = len(tension_detected)
	
	if current_tension < tension_count:
		stretchCode, stretchName = stretch_toDo(tension_detected[current_tension])
	
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
	keypoint_detection_threshold_for_classifier = 0.8
	classifier = None
	
	### ------------ Classification Model -------------- ###
	classification_model = "5.tflite"
	label_file = "5.txt"
	
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
		detected_stretch_pos = []
		min_score = min([keypoint.score for keypoint in person.keypoints])
		
		# Run pose classification
		prob_list = classifier.classify_pose(person)
			
		# Show classification results on the image
		for i in range(classification_results_to_show):
			class_name = prob_list[i].label
			probability = round(prob_list[i].score, 2)
			result_text = class_name + ' (' + str(probability) + ')'
			text_location = (left_margin, (i + 2) * row_size)
			detected_stretch_pos.append(class_name)
			cv2.putText(frame, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,font_size, text_color, font_thickness)
			
		### Convert stretch code to class name ex. Left and Right Side Stretch will be 7SS instead of 7RSS and 7LSS
		SC = convert_stretchCode(stretchCode[current_stretch])
		
		if prepareStretch_stopped:
			### pose detected will start timer
			if detected_stretch_pos[0] == SC:
				if timer_stopped:
					timer_stopped = False
					start_timer()
									
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
	stretch_window.after(15, update_camera)

def close():
	# Release the video capture and destroy the window
    cap.release()
    stretch_window.destroy()

def camera_toggle():
	global camera_running
	if button_state.get() == 0:
	   cam_button.config(image=on_image)
	   button_state.set(1)
	   camera.place(x=700,y=200)

	else:
	   cam_button.config(image=off_image)
	   button_state.set(0)
	   camera.place_forget()

def convert_stretchCode(code):
	stretchName = ""
	if code == "Neck Extension":
		stretchName = "neck_extension"
	elif code == "Left Side Stretch" or "Right Side Stretch":
		stretchName = "side_stretch"
	elif code == "Standing Prayer":
		stretchName = "standing_prayer"
	elif code == "Left Hamstring Stretch" or "Right Hamstring Stretch":
		stretchName = "hamstring_stretch"
	elif code == "Left Single Leg Balance" or "Right Single Leg Balance":
		stretchName = "single_leg_balance"
	else:
		stretchName = code
		
	return stretchName
	
def text_to_speech(text):
	subprocess.call(['espeak', text])

def play_sound(file_path):
	pygame.mixer.init()
	pygame.mixer.music.load(file_path)
	pygame.mixer.music.play()		
	
def prepareToStretch_Timer():
	
	def update_timer():
		global prepareStretch_remaining_time
		global prepareStretch_stopped
		
		if prepareStretch_remaining_time > 0 and prepareStretch_stopped == False:
			prepareStretch_remaining_time -= 1
			stretch_window.after(1000, update_timer)
			num = prepareStretch_remaining_time + 1
			ready_stretch.config(text=str(num))

		elif prepareStretch_remaining_time == 0:
			prepareStretch_stopped = True
			prepareStretch_remaining_time = 3
			ready_stretch.config(text="Go!")
		else:
			prepareStretch_stopped = True
				
	def stop_timer():
		global prepareStretch_stopped
		prepareStretch_stopped = True
		
	update_timer()
	
def notif():

	notif_message = "Stretch Completed. Good Job!"
	result = messagebox.askokcancel("Stretch Complete", notif_message)
		
	if result:
		subprocess.Popen(['python3', 'main_win.py'])
		stretch_window.destroy()
	else:
		subprocess.Popen(['python3', 'main_win.py'])
		stretch_window.destroy()
		
### camera view ###
camera = tk.Label(stretch_window, border=2)
camera.place(x=700,y=200)

### camera Toggle Button ###
button_font = ("Helvetica", 12, 'bold')
cam_button = tk.Button(stretch_window,  bd=0, command=camera_toggle, image=on_image,bg='black',activebackground='black')
cam_button.place(x=900, y=600)		

### stretch name text ###
current_stretch_name = ""
label_font1 = ("Arial", 30, 'bold')
stretch_name = tk.Label(stretch_window, text=current_stretch_name, font=label_font1, fg="green",bg='black')
stretch_name.place(x=20, y=100)

### ready stretch text ###
label_font2 = ("Arial", 50, 'bold')
ready_stretch = tk.Label(stretch_window, text="Ready", bd=0,font=label_font2, fg="green",bg='black')
ready_stretch.place(x=20, y=600)
#lib.create_label(stretch_window,"Ready",20,600,font_size=50,font_family="Verdana",text_color="green")

### exercise for text ###
name = "Exercise for:"
label_font2 = ("Arial", 20, 'normal')
exercise = tk.Label(stretch_window, text=name, font=label_font2,fg='white',bg='black')
exercise.place(x=20, y=20)

### timer text ###
lib.create_label(stretch_window,"Timer: 00:15",850,20,font_size=50,font_family="Verdana",bg_color="gray",text_color="white", bd=2, rel="sunken")

### Stretch Image ###
stretch_image = tk.Label(stretch_window)
stretch_image.place(x=20, y=200)

### Start the video display ###
update_camera()

next_stretch()

### for closing the window
stretch_window.protocol("WM_DELETE_WINDOW", close)

stretch_window.mainloop()
