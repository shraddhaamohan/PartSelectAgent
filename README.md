# PartSelectAgent - AI-Powered Parts Selection Assistant

## Overview

The PartSelectAgent is an AI-powered assistant designed to help users with part selection, troubleshooting, and general inquiries related to appliance parts on the PartSelect e-commerce platform. It leverages large language models (LLMs) and a suite of tools to provide accurate, efficient, and user-friendly support.

### Key Features

*   **Intelligent Part Selection:** Assists users in identifying the correct parts for their appliances based on model numbers, symptoms, and descriptions.
*   **Troubleshooting Support:** Provides guidance on diagnosing and resolving common appliance issues using a comprehensive troubleshooting knowledge base.
*   **Order Assistance:** Guides users through the ordering process, checks part availability, and provides direct links to product pages.
*   **Comprehensive Part Information:** Delivers detailed information about specific parts, including compatibility, pricing, installation instructions, and customer reviews.

### Architecture

The project consists of two main components:

*   **Frontend (React):** A user-friendly interface built with React, allowing users to interact with the AI assistant through a chat window.
*   **Backend (FastAPI):** A robust backend built with FastAPI, responsible for handling user requests, interacting with the LLM, and managing the knowledge base.

## Setup Instructions

Follow these steps to set up the PartSelectAgent project:

### Prerequisites

*   Node.js and npm (Node Package Manager)
*   Python 3.7+
*   pip (Python Package Installer)
*   Git

### Installation

1.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd PartSelectAgent
    ```

2.  **Backend Setup:**

    a.  Navigate to the `backend` directory:

    ```bash
    cd backend
    ```

    b.  Create a virtual environment (recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

    c.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

    d.  Configure environment variables:

    *   Create a `.env` file in the `backend` directory.
    *   Add the necessary environment variables, such as:

    ```
    OPENAI_API_KEY=<your_openai_api_key>
    DEEPSEEK_API_KEY=<your_deepseek_api_key>
    DEEPSEEK_BASE_URL=https://api.deepseek.com
    PORT=8000
    USE_MOCK_RESPONSES=false
    LOG_LEVEL=INFO
    SUPABASE_URL=<your_supabase_url>
    SUPABASE_SERVICE_KEY=<your_supabase_service_key>
    LLM_MODEL=gpt-4o-mini
    API_BEARER_TOKEN=<your_api_bearer_token>
    ```

    e.  Run the backend server:

    ```bash
    python app.py
    ```

3.  **Frontend Setup:**

    a.  Navigate to the `frontend` directory:

    ```bash
    cd frontend
    ```

    b.  Install the required Node.js packages:

    ```bash
    npm install
    ```

    c.  Configure environment variables:

    *   Create a `.env` file in the `frontend` directory.
    *   Add the necessary environment variables, such as:

    ```
    REACT_APP_API_BEARER_TOKEN=<your_api_bearer_token>
    REACT_APP_API_BASE_URL=http://localhost:8001
    ```

    d.  Start the frontend development server:

    ```bash
    npm start
    ```

## Usage

1.  **Access the Application:**

    *   Open your web browser and navigate to `http://localhost:3000` (or the appropriate address if the frontend is running on a different port).

2.  **Interact with the Chat Assistant:**

    *   Type your questions or requests in the chat input field.
    *   Click the "Send" button or press "Enter" to submit your message.
    *   The AI assistant will respond with relevant information and guidance.

### Example Queries

*   "How can I install part number PS11752778?"
*   "Is this part compatible with my WDT780SAEM1 model?"
*   "The ice maker on my Whirlpool fridge is not working. How can I fix it?"
*   "What is the price and availability of this part?"


## Project Structure

```
PartSelectAgent/
├── backend/                # FastAPI backend
│   ├── app.py              # Main application file
│   ├── parts_select_ai_expert.py # Agent definition and tools
│   ├── crawler/            # Web scraping tools
│   ├── knowledge_base/     # Knowledge base management
│   ├── .env                # Environment variables
│   ├── requirements.txt    # Python dependencies
│   └── ...
├── frontend/               # React frontend
│   ├── src/                # React components and logic
│   ├── public/             # Static assets
│   ├── .env                # Environment variables
│   ├── package.json        # Node.js dependencies
│   └── ...
├── README.md               # This file
└── LICENSE                 # License information
```

## Contact

If you have any questions or suggestions, please feel free to contact me.
