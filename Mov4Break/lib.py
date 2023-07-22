### Import Libraries ###
import tkinter as tk
from tkinter import Tk, Frame
import subprocess
import io
from PIL import ImageTk
from PIL import Image
import cv2

def center_window(window):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    window.geometry('{}x{}+{}+{}'.format(window_width, window_height, x, y))
    
### function for button ###
def create_button(window, text, command, x, y, color, border=1, font_size=12, height=2, width=15, activebackground=None, activeforeground=None, bg=None):
	button_font = ("Helvetica", font_size)
	button = tk.Button(window, text=text,width=width, height=height, fg=color, bd=border, font=button_font, command=command, activebackground=activebackground, activeforeground=activeforeground, bg=bg)
	button.place(x=x, y=y)
	
### function for label ###
def create_label(window, text, x, y,font_family="Helvetica",text_color="black", font_size=12, bg_color=None, bd=0, rel="flat", text_type="bold"):
	label_font = (font_family, font_size, text_type)
	label = tk.Label(window, text=text, fg=text_color, font=label_font, bg=bg_color,borderwidth=bd, relief=rel)
	label.place(x=x, y=y)
	

