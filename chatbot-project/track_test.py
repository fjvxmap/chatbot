from ultralytics import YOLO
import cv2
from depth_camera_module import DepthCamera
import datetime

# from deep_sort_realtime.deepsort_tracker import DeepSort
import os
import torch
from ultralytics.trackers import bot_sort
from ultralytics.trackers import track
import time
import numpy as np
import open3d as o3d
import pyrealsense2.pyrealsense2 as rs
import serial


def process_global_multi_mean(
    global_multi_mean, depth_frame, depth_scale, color_intrin
):
    processed_data = []
    if global_multi_mean is not None:
        for item in global_multi_mean:
            center_x, center_y, _, _, vel_x, vel_y, _, _ = item

            # Ensure the coordinates are within the valid range
            center_x = np.clip(int(center_x), 1, depth_frame.shape[1] - 2)
            center_y = np.clip(int(center_y), 1, depth_frame.shape[0] - 2)

            # Extract a 3x3 region and compute the median depth value
            depth_region = depth_frame[
                center_y - 1 : center_y + 2, center_x - 1 : center_x + 2
            ]
            median_depth = np.median(depth_region) * depth_scale

            center_3d = rs.rs2_deproject_pixel_to_point(
                color_intrin, [center_x, center_y], median_depth
            )
            processed_data.append((center_3d, vel_x, vel_y))

    return processed_data


model = YOLO("best.pt")  # best.pt  test.pt ph_exp_2.pt
model.to("cuda")
dc = DepthCamera()  # *************Realsense 카메라 class dc로 정
dlc_live = DLCLive(model_path, display=False)
dlc_live.init_inference()
# global dlc_pose
dlc_pose = None
start = time.time()

# point cloud   **** 바닥 plane equation ransac 이용해서 구할 때
ret, depth_image, color_image, depth_colormap = dc.get_frame()
color = o3d.geometry.Image(color_image)
depth = o3d.geometry.Image(depth_image)
pinhole_camera_intrinsic = o3d.camera.PinholeCameraIntrinsic(
    dc.get_color_intrinsics().width,
    dc.get_color_intrinsics().height,
    dc.get_color_intrinsics().fx,
    dc.get_color_intrinsics().fy,
    dc.get_color_intrinsics().ppx,
    dc.get_color_intrinsics().ppy,
)
rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
    color, depth, convert_rgb_to_intensity=False
)
pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, pinhole_camera_intrinsic)
plane_model, inliers = pcd.segment_plane(
    distance_threshold=0.001, ransac_n=3, num_iterations=1000
)
p1, p2, p3, p4 = plane_model  # ***** p_1x + p_2y + p_3z = p_4
plane_normal = np.array([p1, p2, p3])
plane_normal /= np.linalg.norm(plane_normal)
z = np.array([0, 0, 1])
rotation_axis = np.cross(plane_normal, z)
rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
angle = np.arccos(np.dot(plane_normal, z))
rotation = R.from_rotvec(rotation_axis * angle)
rotation_matrix = rotation.as_matrix()

# Serial통신 MCU와 통신하는 부 COM10 == USB PORT번호 / 115200 == BAUDRATE 통신속도
ser = serial.Serial("COM10", 115200, timeout=1)

while True:
    # start = datetime.datetime.now()
    end = time.time()
    print(end - start)
    start = end

    ser.write(
        f"{state1},{state2},{state3}\n".encode()
    )  # 송신 예제 PC to MCU EX) 1,2,500를 보낸다고 치면 mot1, velocity_mode, 500속도 로 구동 / 이런식으로 전달 가능
    if ser.in_waiting > 0:
        data = ser.readline().decode().strip()
        encoder, arduino_state, tmp_value_arduino = data.split(
            ","
        )  # Split the received data
        encoder = float(encoder)  # Convert encoder to float
        arduino_state = int(arduino_state)  # Convert tension1 to float
        tmp_value_arduino = int(tmp_value_arduino)  # Convert tension2 to float
        # print(f"encoder: {encoder}, tension1: {tension1}, tension2: {tension2}")
        encoder_value = float(encoder) if isinstance(encoder, str) else encoder
        print("encoder", encoder)
        # MCU to PC 데이터 수신 예제

    _, depth_image, color_image, depth_colormap = dc.get_frame()
    print("start")
    results = model.track(color_image, persist=True, tracker="botsort.yaml")
    if results[0].masks is None:
        print("No detectable objects in frame. Skipping...")
        continue

    # YOLO + Tracking 알고리즘으로 output을 중심 x,y값을 받고 depth frame으로부터 해당 depth값을 안다고 가정했을 때
    # process_global_multi_mean function에서처럼 center_3d = rs.rs2_deproject_pixel_to_point(color_intrin, [center_x, center_y], median_depth) 사용
    # 다음의 function사용 시 xyd -> camera frame의 xyz로 변경 가능
    # color_intrin == 카메라에 내재되어있는 intrinsic value 고정
    global_mean_processed = process_global_multi_mean(
        bot_sort.global_multi_mean, depth_image, depth_scale, color_intrin
    )

    annotated_frame = results[0].plot()
    # print(results[0].boxes)
    cv2.imshow("YOLOv8 Tracking", annotated_frame)
    # cv2.imshow("dd", depth_image)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
