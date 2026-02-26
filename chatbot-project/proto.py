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
from chatbot.chatbot import Chatbot


def initialize_chatbot(api_key, prompt_file_path):
    """Initialize Chatbot for command interpretation"""
    with open(prompt_file_path, "r") as file:
        gpt_prompt = file.read()
        chatbot = Chatbot(api_key=api_key, gpt_prompt=gpt_prompt)
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY. Set it in your .env file.")

    # ser, model, depth_camera, recognizer, chatbot = initialize_system(
    #     api_key
    # )

    chatbot = initialize_chatbot(
        api_key,
        "data/task_data_set_prompt.txt",
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
            response = chatbot.process_image("test/test_image.jpg")
            print(response)

    cv2.destroyAllWindows()
    ser.close()
