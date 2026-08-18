# AI Chat Widget with FastAPI and Groq

This project provides a fully functional, embeddable AI chat widget. It features a modern web interface, a robust Python backend using FastAPI, and lightning-fast responses from language models powered by the Groq API.

The widget first asks the user for their name and email, then uses that information to create a personalized and engaging conversation.

## ✨ Features

* **Pre-chat User Form:** Captures user name and email to personalize the experience.
* **Personalized AI Responses:** The AI is aware of the user's name and can use it in conversation.
* **High-Speed Inference:** Utilizes the Groq API for extremely fast, real-time AI responses.
* **Input Safety:** Integrates Llama Guard to screen user inputs for malicious content before processing.
* **Easy to Embed:** The widget can be added to any existing website with a single line of JavaScript.
* **Modern Backend:** Built with FastAPI, offering high performance and automatic API documentation.

***

## 📂 Project Structure

To ensure the application works correctly, your files must be organized in the following structure:

/your-project-folder

├── appfast.py           <-- The main FastAPI server

├── functions.py         <-- The core AI and prompting logic

├── requirements.txt     <-- You will create this file for dependencies

└── static/

├────── chat.html        <-- The chat interface UI for the iframe

├────── index.html       <-- A test page to host the widget

├────── liveChatEntry.js <-- The script that injects the widget

└────── style.css        <-- CSS for the chat interface


***

## 🚀 Getting Started

Follow these instructions to get the project running on your local machine.

### Prerequisites

Before you begin, make sure you have the following installed:
* **Python 3.8+**
* **pip** (Python's package installer)
* A **Groq API Key**: You can get a free API key from the [Groq Console](https://console.groq.com/keys).

### Installation and Setup

**Step 1: Create a Virtual Environment** 🖥️

It is highly recommended to use a virtual environment to manage project dependencies. Open your terminal in the project's root directory and run:

```bash
# Create the virtual environment
python -m venv venv

# Activate it (on Windows)
.\venv\Scripts\activate

# Activate it (on macOS/Linux)
source venv/bin/activate
```

Create a new file named requirements.txt in the root of your project folder and add the following lines to it. This file lists all the Python packages the project needs.

```
fastapi
uvicorn[standard]
langchain
groq
pydantic
```

With your virtual environment active, install all the required packages by running the following command in your terminal:

```bash
pip install -r requirements.txt
```

The application needs your Groq API key to function. You must set this key as an environment variable so the application can access it securely.

## Running the Application
You are now ready to run the server!

#### Make sure your virtual environment is active and you have set the API key.

#### Run the following command in your terminal from the project's root directory:
```bash
uvicorn appfast:app --reload
```
#### Open your web browser and navigate to:

http://127.0.0.1:8000

