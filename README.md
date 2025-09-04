# Niqatech نقاطك: Teacher's Voice Grading App
## Vision
An application that assists teachers in recording their students' grades using a speech-to-text interface, making the grading process faster and more efficient.
## Concept
### Problem statement
Teachers spend a significant amount of time manually entering grades, which can be time-consuming and prone to errors.
### Proposed Solution
A speech-to-text application that allows teachers to verbally input grades, which are then transcribed and recorded automatically. This tool aims to streamline the grading process, reduce errors, and save valuable time for educators.
## Goals

- Short-term: Develop a basic prototype that can accurately transcribe spoken grades and store them in a database.The database is an Excel file .xls .
- Long-term: Enhance the app with additional features, improve accuracy, and make it widely available for educators.
- Niqatech

## 🛠️ How to Install
1. **Clone the repository**  
   ```bash
   git clone https://github.com/aspirant2018/niqatech-backend.git
   cd niqatech-backend

2. **Create a and activate virtual envirement venv**
   ```bash
   python3 -m venv venv
   source venv/bin/activate```

4. **Install dependencies**
    ```bash
    # in Terminal run
    pip install -r requirements.txt

## Run the Backend Application
1. it will run on port 8000 
    ```bash
    python3 app/main.py

    running on http://localhost:8000 

## Run easily with docker
    ```bash
    docker compose up -d
    ```



## ✅ How to Test the Endpoints

FastAPI provides an interactive API documentation where you can explore and test all available endpoints easily.

### ▶️ Step-by-Step

1. Make sure the backend server is running:

   ```bash
   python3 main.py
2. Make sur to Create a database:

   ```bash
   python3 database/create_db.py 

3. Open your browser to Browse all available endpoints:
   ```bash
   http://localhost:8000/docs
