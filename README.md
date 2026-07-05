# Personalized Networking Assistant 🤝

An AI-powered web application that helps users generate smart, context-aware, and tailored conversation starters for professional or social networking events. 

The application uses **FastAPI** for the backend service, **Streamlit** for a premium responsive frontend dashboard, and **Hugging Face Transformers** models locally for event analysis and text generation.

---

## Key Features

1. **Bespoke Conversation Starters**: Generates 3 personalized starters tailored to both the event description and the user's specific topics of interest.
2. **AI-Powered Event Analyzer**: Extracts high-level professional/social themes (e.g., *Technology*, *Business*, *Design*, *Finance*) using zero-shot classification via a pre-trained **DistilBERT** model.
3. **Wikipedia AI Fact-Checker**: Checks topics, claims, or conversation prompts. It fetches the top Wikipedia article summary via the Wikipedia API and runs a **Natural Language Inference (NLI)** verification step using DistilBERT to classify the claim as *Supported*, *Refuted*, or *Neutral*.
4. **Local Data Persistence**: Automatically logs generated prompts and user likes/dislikes feedback to local JSON stores for session persistence and analysis.
5. **Interactive Analytics Dashboard**: Visualizes feedback response metrics (Like/Dislike count and positive ratio) and full chronological logs of past interactions.
6. **Offline/Mock AI Mode**: Includes a toggle in the frontend settings to run the application using fast, rule-based matching and templates. This allows testing all API workflows instantly and offline without downloading large model weights.

---

## Tech Stack
- **Python 3.11+**
- **FastAPI** (Backend REST API)
- **Streamlit** (Frontend Dashboard UI)
- **Hugging Face Transformers** (`distilbert-base-uncased-mnli` & `gpt2` models)
- **Pytest** & **Httpx** (Testing Suite)
- **Pandas** (Analytics formatting)

---

## Project Architecture 

User  
  ↓  
Streamlit Frontend  
  ↓  
FastAPI Backend  
  ↓  
Services Layer  
   ├── Event Analyzer (DistilBERT)  
   ├── Topic Generator (GPT-2)  
   ├── Fact Checker (Wikipedia API)  
   ├── History Logger  
   └── Feedback Logger  
  ↓  
Data Layer  
   ├── JSON Storage (history.json, feedback.json)  
   └── Wikipedia API

---

## Project Structure

```text
Personalized_Networking_Assistant/
├── backend/
│   ├── __init__.py
│   ├── event_analyzer.py      # Theme extraction using DistilBERT zero-shot pipeline
│   ├── topic_generator.py     # Prompt generation using GPT-2 / Templates fallback
│   ├── fact_checker.py        # Wikipedia search & NLI verification
│   ├── history_logger.py      # Appends generation records to local JSON
│   ├── feedback_logger.py     # Appends and aggregates user feedback
│   └── main.py                # FastAPI endpoints (/generate-conversation, /fact-check, etc.)
├── frontend/
│   ├── app.py                 # Streamlit frontend styled with premium CSS
├── images/
│   ├── Backend Terminal.png
│   ├── Conversation Generator.png
│   ├── Fact Checker.png
│   ├── History And Feedback.png
│   ├── Home Page.png
│   ├── Swagger UI.png
│   └── Test Results.png
├── tests/
│   ├── __init__.py
│   └── test_backend.py        # Automated Pytest suite with mocked transformer pipelines
├── data/
│   ├── .gitkeep               # Directory for history.json and feedback.json
│   ├── history.json           # Logged conversation starter data (auto-generated)
│   └── feedback.json          # Logged feedback ratings data (auto-generated)
├── requirements.txt           # Python package requirements
├── README.md                  # Project documentation & instructions
└── .gitignore                 # Standard Python and Streamlit git exclusions
```

---

## Installation & Setup

### Prerequisites
Make sure you have **Python 3.11** or higher installed on your system.
- Download Python from the [official website](https://www.python.org/downloads/).
- Verify your installation by running:
  ```bash
  python --version
  ```

### Step 1: Clone or Navigate to the Directory
Ensure you are inside the project root folder:
```bash
cd Personalized_Networking_Assistant
```

### Step 2: Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
Install all required libraries (including Hugging Face Transformers, FastAPI, Streamlit, and Torch):
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(Note: Installing PyTorch might take a few minutes depending on your internet connection).*

---

## Running the Application

### 1. Launch the FastAPI Backend
Start the backend server on `http://localhost:8000`:
```bash
uvicorn backend.main:app --reload
```

### 2. Launch the Streamlit Frontend
In a new terminal window (with the virtual environment active), start the Streamlit app:
```bash
streamlit run frontend/app.py
```
This will open the application in your default browser at `http://localhost:8501`.

---

## Running the Test Suite

The project includes unit and integration tests written in `pytest`. The test suite mocks heavy transformer pipelines and Wikipedia network requests to run instantly without internet or model downloads.

Run the tests inside your terminal:
```bash
pytest tests/
```

---

## How It Works Under the Hood

### 1. Zero-Shot Theme Classification
In `backend/event_analyzer.py`, we use the model `typeform/distilbert-base-uncased-mnli`. When a description is input, the model scores its semantic similarity to our candidate categories (e.g. *Technology*, *Design*, *Finance*) without requiring category-specific training.

### 2. Few-Shot GPT-2 Prompts
In `backend/topic_generator.py`, we feed a formatted few-shot prompt to the `gpt2` model. This structure guides the completion engine to output conversation starters in a structured format:
```text
Context: Networking Event
Themes: Technology
Interests: Python, AI
Conversation Starters:
1. "..."
2. "..."
```

### 3. NLI Fact-Checking
In `backend/fact_checker.py`, we fetch the top summary paragraph of a Wikipedia search. We input the summary as the **Premise** and the user's claim as the **Hypothesis** directly to the DistilBERT MNLI model. The classifier outputs probabilities for three categories:
- **Entailment (Supported)**: The Wikipedia context logically proves the statement.
- **Contradiction (Refuted)**: The Wikipedia context logically contradicts the statement.
- **Neutral**: The Wikipedia context does not have enough information to confirm or deny.

---

## Screenshots

### Home Page
![Home Page](images/Home%20Page.png)

### Conversation Generator
![Conversation Generator](images/Conversation%20Generator.png)
### Fact Checker
![Fact Checker](images/Fact%20Checker.png)

### History and Feedback
![History and Feedback](images/History%20And%20Feedback.png)

### Swagger UI
![Swagger UI](images/Swagger%20UI%20.png)

### Backend Terminal
![Backend Terminal](images/Backend%20Terminal%20.png)

### Test Results
![Test Results](images/Test%20Results.png)

---

## Future Improvements
- Add more fact-checking sources besides Wikipedia.
- Improve conversation personalization using user preferences.
- Deploy the application on cloud platforms.


---

## Author
**Somya Chauhan**
Bachelor of Computer Application


---

## License
This project is developed for educational purposes.
