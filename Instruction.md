# Application Launch Instructions

## 1. Clone the Repository
Open your terminal and clone the project repository:
```bash
git clone <repository-url>
cd CompMethodsLab
```

## 2. Environment Setup
This project is configured to run in a **Visual Studio Code Dev Container**, which automates the installation of all dependencies (Python, Node.js, libraries).

1. Open the project in **VS Code**.
2. When prompted "Reopen in Container", click **Reopen**.
   - *Alternatively: Press `F1` and select `Dev Containers: Reopen in Container`.*
3. Wait for the container to build.
   - The system will automatically install:
     - Python dependencies (`backend/requirements.txt`)
     - Node.js dependencies (`package.json`)

## 3. Running the Application
Once the container is ready and the terminal is active:

1. Run the start command:
   ```bash
   npm start
   ```
   *This script (`start_web.sh`) will automatically launch the Flask backend and the Frontend server.*

2. Access the application in your browser:
   - **URL**: [http://localhost:8000](http://localhost:8000)

## Troublehsooting
- If the port is busy, ensure no other python processes are running (`pkill -f python3`).
- If you are running locally (not in a container), ensure you have Python 3.10+ and Node.js installed, then run:
  ```bash
  pip install -r backend/requirements.txt
  npm install
  npm start
  ```
