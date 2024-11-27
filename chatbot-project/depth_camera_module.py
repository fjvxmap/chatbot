import pyrealsense2.pyrealsense2 as rs
import numpy as np
import os
import cv2


class DepthCamera:
    def __init__(self):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(
            rs.stream.color, 640, 480, rs.format.bgr8, 30
        )  # 1920 1080 640 480

        # config.enable_stream(rs.stream.accel)
        # config.enable_stream(rs.stream.gyro)

        self.pipeline.start(config)

        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        self.depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
        self.color_intrin = color_frame.profile.as_video_stream_profile().intrinsics
        self.depth_to_color_extrin = depth_frame.profile.get_extrinsics_to(
            color_frame.profile
        )
        self.depth_scale = device.first_depth_sensor().get_depth_scale()

        # Start streaming

    def gyro_data(self, gyro):
        return np.asarray([gyro.x, gyro.y, gyro.z])

    def accel_data(self, accel):
        return np.asarray([accel.x, accel.y, accel.z])

    def get_frame(self):
        align_to = rs.stream.color
        align = rs.align(align_to)

        frames = self.pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        # accel_frame = None
        # gyro_frame = None
        """
        for frame in frames:
            if frame.is_motion_frame():
                if frame.as_motion_frame().get_profile().stream_type() == rs.stream.accel:
                    accel_frame = frame
                elif frame.as_motion_frame().get_profile().stream_type() == rs.stream.gyro:
                    gyro_frame = frame

        if not accel_frame or not gyro_frame:
            raise RuntimeError("Motion frames are not available")

        accel = self.accel_data(accel_frame.as_motion_frame().get_motion_data())
        gyro = self.gyro_data(gyro_frame.as_motion_frame().get_motion_data())
        """
        # spatial = rs.spatial_filter()
        # spatial.set_option(rs.option.holes_fill, 3)
        # filtered_depth = spatial.process(depth_frame)
        # hole_filling = rs.hole_filling_filter()
        # filled_depth = hole_filling.process(filtered_depth)

        # Create colormap to show the depth of the Objects
        colorizer = rs.colorizer()
        depth_colormap = np.asanyarray(colorizer.colorize(depth_frame).get_data())

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # if not depth_frame or not color_frame:..
        #    return False, None, None
        return True, depth_image, color_image, depth_colormap  # , accel, gyro

    def get_depth_intrinsics(self):
        return self.depth_intrin

    def get_color_intrinsics(self):
        return self.color_intrin

    def get_depth_to_color_extrinsics(self):
        return self.depth_to_color_extrin

    def get_depth_scale(self):
        return self.depth_scale

    def get_fps(self):
        # Get profiles of the streaming streams
        profile = self.pipeline.get_active_profile()

        # Get the profile of the depth stream
        depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
        # Get the FPS of the depth stream
        fps = depth_profile.fps()

        return fps
