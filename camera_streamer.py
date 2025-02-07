import cv2
import numpy as np
import threading
import time
from pypylon import pylon
import subprocess

class CameraStreamer(threading.Thread):
    def __init__(self, serial_number, output_file, frame_rate=50):
        super().__init__()
        self.serial_number = serial_number
        self.output_file = output_file
        self.frame_rate = frame_rate
        self.camera = self.connect_camera()
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.frame = None

    def connect_camera(self):
        retries = 5
        for _ in range(retries):
            try:
                tl_factory = pylon.TlFactory.GetInstance()
                devices = tl_factory.EnumerateDevices()
                for device in devices:
                    if device.GetSerialNumber() == self.serial_number:
                        return pylon.InstantCamera(tl_factory.CreateDevice(device))
                raise ValueError(f"Camera with serial number {self.serial_number} not found.")
            except Exception as e:
                print(f"Failed to connect to camera: {e}. Retrying...")
                time.sleep(2)
        raise ValueError(f"Failed to connect to camera after {retries} retries.")

    def run(self):
        self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        ffmpeg_process = subprocess.Popen(
            [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-f", "rawvideo",
                "-pixel_format", "bgr24",
                "-video_size", "1280x720",  # Adjust based on your camera resolution
                "-framerate", str(self.frame_rate),
                "-i", "-",  # Read input from stdin
                "-c:v", "libx264",
                "-preset", "superfast",
                "-crf", "28",
                self.output_file
            ],
            stdin=subprocess.PIPE
        )
        while not self.stop_event.is_set():
            grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = self.converter.Convert(grab_result)
                frame = image.GetArray()
                with self.lock:
                    self.frame = frame
                ffmpeg_process.stdin.write(frame.tobytes())
            grab_result.Release()
            time.sleep(1 / self.frame_rate)
        self.camera.StopGrabbing()
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()

    def stop(self):
        self.stop_event.set()

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None