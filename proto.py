import os
import serial
import speech_recognition as sr
import time
import cv2
import numpy as np
import pyrealsense2.pyrealsense2 as rs

from ultralytics import YOLO
from depth_camera_module import DepthCamera

# from track_test import process_global_multi_mean
from chatbot import Chatbot

# Define GPT prompt to interpret voice commands
GPT_PROMPT = """
You are a control system for a wearable glove that can understand the following commands:
- "power grasp" for a strong grip.
- "grasp" for a moderate grip.
- "precision grasp" for a light grip.
- "squeeze" to apply additional pressure on the grasped object.
- "tighten" to increase the grip strength without moving.
- "release" to let go of the object and return to the initial position.

Also, user can give some feedback to the system.
For example, "I want to grasp the object more tightly." Then, the system must give the appropriate position or tension integer between 0 and 9.

If the user want to start new instruction, respond with the exact command ("power grasp", "grasp", "precision grasp", "squeeze", "tighten", "release") based on user input.
Else, respond with the appropriate variable("position" or "tension") and integer between -9 and 9 based on user input if the user give feedback to the system.
i.e. "position 2" or "tension -1"
Do not include the quotation marks in your response.
"""


def initialize_chatbot(api_key):
    """Initialize Chatbot for command interpretation"""
    chatbot = Chatbot(api_key=api_key, gpt_prompt=GPT_PROMPT)
    return chatbot


def initialize_system(api_key):
    """Initialize all necessary components for the system"""
    # Initialize Serial communication with MCU
    ser = serial.Serial("COM10", 115200, timeout=1)

    # Initialize YOLO model and depth camera
    model = YOLO("best.pt")
    model.to("cuda")
    depth_camera = DepthCamera()

    # Initialize Speech Recognizer
    recognizer = sr.Recognizer()

    # Initialize Chatbot for command interpretation
    chatbot = Chatbot(api_key=api_key, gpt_prompt=GPT_PROMPT)

    return ser, model, depth_camera, recognizer, chatbot


def listen_for_command():
    """Continuously listen for user commands via microphone"""
    with sr.Microphone() as source:
        print("Listening for command...")
        audio = recognizer.listen(source)
    try:
        user_command = recognizer.recognize_google(audio)
        print(f"User said: {user_command}")
        return user_command
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return None


def send_command_to_mcu(interpreted_command):
    """Map interpreted commands to MCU serial communication"""
    split_command = interpreted_command.split(" ")
    command_type = split_command[0]
    if len(split_command) == 2:
        command_value = split_command[1]
        if command_type == "position":
            ser.write(f"position,{command_value},1,2\n".encode())
    else:
        if command_type == "power grasp":
            ser.write(b"3,3,1,3\n")  # Example command for power grasp
        elif command_type == "grasp":
            ser.write(b"3,2,1,2\n")  # Example command for grasp
        elif command_type == "precision grasp":
            ser.write(b"1,1,1,1\n")  # Example command for precision grasp
        elif command_type == "squeeze":
            ser.write(b"3,0,1,2\n")  # Command for squeeze (velocity mode)
        elif command_type == "tighten":
            ser.write(b"0,3,1,2\n")  # Command for tighten (tension mode)
        elif command_type == "release":
            ser.write(b"position,initial,1,2\n")  # Command for release (position mode)
        else:
            print("No valid command to send.")


def process_object_detection():
    """Capture frame and perform object detection with YOLO"""
    _, depth_image, color_image, _ = depth_camera.get_frame()
    results = model.track(color_image, persist=True, tracker="botsort.yaml")
    object_frame = results[0]

    if object_frame.masks is None:
        print("No detectable objects in frame. Skipping...")
        return None, None

    annotated_frame = object_frame.plot()
    cv2.imshow("YOLOv8 Tracking", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        return None, None

    return object_frame, depth_image


def process_grasp_action(detected_object, depth_image, grasp_type="grasp"):
    """Determines action based on depth and grasp type"""
    global_mean_processed = process_global_multi_mean(
        detected_object.global_multi_mean,
        depth_image,
        depth_camera.get_depth_scale(),
        depth_camera.get_color_intrinsics(),
    )

    # Example of grasp actions based on types
    if grasp_type == "power":
        send_command_to_mcu("power grasp")
    elif grasp_type == "grasp":
        send_command_to_mcu("grasp")
    elif grasp_type == "precision":
        send_command_to_mcu("precision grasp")


if __name__ == "__main__":
    # ser, model, depth_camera, recognizer, chatbot = initialize_system(
    #     "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"
    # )

    chatbot = initialize_chatbot(
        "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"
    )

    while True:
        # Listen for voice command and interpret
        # command_text = listen_for_command()
        # if command_text:
        #     interpreted_command = interpret_command(command_text)
        #     if interpreted_command:
        #         send_command_to_mcu(interpreted_command)

        # # Perform object detection and grasp control
        # detected_object, depth_image = process_object_detection()
        # if detected_object:
        #     # Example grasp based on object characteristics
        #     depth_value = np.mean(depth_image)  # Placeholder for depth analysis
        #     if depth_value < 1.0:
        #         process_grasp_action(detected_object, depth_image, "power")
        #     elif 1.0 <= depth_value < 2.0:
        #         process_grasp_action(detected_object, depth_image, "grasp")
        #     else:
        #         process_grasp_action(detected_object, depth_image, "precision")

        # # Exit condition
        # if command_text and "exit" in command_text.lower():
        #     print("Exiting program.")
        #     break

        # Test chatbot
        user_input = input("Enter command: ")
        if user_input == "exit":
            break
        elif user_input == "stop":
            chatbot.deactivate_chatbot()
        elif user_input == "start":
            chatbot.activate_chatbot()
        else:
            response = chatbot.interpret_command(user_input)
            print(response)

    cv2.destroyAllWindows()
    ser.close()
