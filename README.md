# UIUC ECE479 Sp25 Lab 3: Wireless & Wearable Glove Controller 

## Motivation

It's **SUPER COOL**!

## Hardware Components

- Raspberry Pi 4B (can be replaced by smaller boards)
- Multiple (3 in our design) MPU 6050(6-axis IMU). More powerful IMUs (e.g. MPU 9050) are preferred.
- MPU multiplexer (CJMCU 9548), needed to support read from more than 2 IMUs simultaneously.
- Buttons & Wires

## Communication

Support 2 types of communication (can be configured in config.py):

- **Wi-Fi**: Suitable for long-distance and low latency communication with network connection.
- **Bluetooth**: Suitable for short-distance communication with low power consumption. Pairing is needed between the glove and the computer.

## Buttons' Functionality

1. Start/Stop: Start/stop the glove controller.
2. Reset: Reset the controller status (cursor position, filter status, etc.)
3. Boss Key: Return to the desktop.
4. More functions can be easily defined by reading the button status in the main loop.

## Usage

Customize settings in config.py. Then run `receiver.py` and `sender.py` on the computer and raspberry pi respectively. Extra libraries are needed to run the code. Pairing beforehand is needed for Bluetooth communication.

Press the start button to start the glove controller. Move your hand around to control the cursor. Tap your index finger to left-click, tap your middle finger to right-click.

## Demo



https://github.com/user-attachments/assets/5a1f4780-abdc-4f57-a095-b9b0a8c7ae8e

