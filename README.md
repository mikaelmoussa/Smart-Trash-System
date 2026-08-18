# Smart Trash System

A senior project (Lebanese International University, Spring 2025–2026) that combines AI, IoT, and embedded systems to automate waste classification and sorting.

**Authors:** Mikael Moussa · Ali Hamieh
**Supervisor:** Dr. Hussein Nasrallah

## Overview

Traditional waste management relies heavily on manual sorting, which is inefficient and error-prone. This project automates that process: an ESP32 camera captures images of waste items, sends them wirelessly to an AI image classification model, and based on the result, an Arduino Uno drives servo motors to sort the item into the correct compartment (plastic, metal, glass, or paper). Ultrasonic sensors track fill levels for each compartment and trigger alerts through a mobile app dashboard when a bin is full, letting staff monitor bin status, sorting history, and maintenance in real time.

Testing confirmed reliable Wi-Fi communication, accurate waste classification, and timely full-bin alerts — demonstrating a low-cost, scalable approach to smart waste management for homes, schools, public spaces, and smart cities.

## How It Works

1. A **motion sensor** detects when an item is inserted into the bin.
2. The **ESP32 camera module** captures an image and sends it over Wi-Fi to a server running the AI classification model.
3. The model classifies the waste as plastic, metal, glass, or paper.
4. The **Arduino Uno** receives the result and drives **servo motors** to direct the item into the matching compartment.
5. **Ultrasonic sensors** continuously monitor each compartment's fill level.
6. When a compartment is full, an alert is pushed to the **mobile app**, where staff/admins can view bin status, sorting history, and manage maintenance.

## Tech Stack

- **Hardware:** ESP32 camera module, Arduino Uno, servo motors, ultrasonic sensors, motion sensor, Wi-Fi module — housed in a wood-and-cardboard bin structure with 4 sorting compartments
- **AI:** Image classification model for waste sorting
- **Backend:** PHP
- **Database:** MySQL (via XAMPP)
- **Mobile App:** Android (built in Android Studio)
- **Firmware:** Arduino IDE
- **Development:** Python, Visual Studio Code

## Project Structure

```
Smart-Trash-System/
├── Source/
│   └── Software code/
│       ├── recycling-company-website/   # Web/dashboard front end
│       └── AIChatComponent-main/        # AI chat component
├── Final_Report.docx                    # Full senior project report
└── Smart_Trash_System_Presentation.pptx # Project presentation slides
```

## Getting Started

### Hardware
See `Source` for Arduino/ESP32 firmware and wiring details. Flash the ESP32 and Arduino Uno using the Arduino IDE.

### Web / Backend
```bash
cd "Source/Software code/recycling-company-website"
```
Requires a PHP + MySQL environment (e.g., XAMPP) to run the backend and database locally.

## Documentation

- 📄 [Final Report](./Final_Report.docx) — full write-up of background, design, implementation, and testing
- 📊 [Presentation Slides](./Smart_Trash_System_Presentation%20(1).pptx) — project overview deck

## License

Developed as a senior project at the Lebanese International University. Add a license here if you'd like to open it up for reuse (e.g., MIT, Apache 2.0).
