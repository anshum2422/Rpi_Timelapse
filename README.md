# Raspberry Pi Zero W Timelapse Camera

Timelapse camera with live streaming for Raspberry Pi Zero W and Camera V1.

## Features

- Captures photo every 5 seconds
- Live web streaming (30 FPS)
- Automatic timelapse video generation
- Retro sage green web interface
- Auto-starts on boot
- Saves all photos permanently

## Hardware Required

- Raspberry Pi Zero W
- Raspberry Pi Camera V1
- 8GB+ microSD card
- 5V power supply

## Installation

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-flask python3-pil ffmpeg

mkdir -p ~/timelapse/{photos,videos}
cp camera.py ~/timelapse/
chmod +x ~/timelapse/camera.py
