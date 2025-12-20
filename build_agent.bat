@echo off
echo "Attempting to build the project..."

echo "Step 1: Installing Python dependencies"
pip install -r backend/requirements.txt
if errorlevel 1 (
    echo "Failed to install python requirements."
    exit /b 1
)

pip install pyinstaller
if errorlevel 1 (
    echo "Failed to install pyinstaller."
    exit /b 1
)

echo "Step 2: Installing Node.js dependencies"
npm install
if errorlevel 1 (
    echo "Failed to install node modules."
    exit /b 1
)

echo "Step 3: Building the application"
npm run build
if errorlevel 1 (
    echo "Failed to build the application."
    exit /b 1
)

echo "Build successful!"
