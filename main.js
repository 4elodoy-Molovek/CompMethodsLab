const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false // For simple prototype. In prod, use preload.
        }
    });

    mainWindow.loadFile('index.html');

    // Open DevTools
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', function () {
        mainWindow = null;
    });
}

function startPythonBackend() {
    let backendPath;
    let pythonCommand;
    
    // Check if we're in development or production (packaged)
    if (app.isPackaged) {
        // In production: use bundled Python executable
        // Backend exe should be in resources/backend/
        if (process.platform === 'win32') {
            backendPath = path.join(process.resourcesPath, 'backend', 'backend.exe');
        } else {
            backendPath = path.join(process.resourcesPath, 'backend', 'backend');
        }
        pythonCommand = backendPath;
        
        console.log('Starting packaged backend from:', backendPath);
    } else {
        // In development: use system Python
        backendPath = path.join(__dirname, 'backend', 'app.py');
        pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
        
        console.log('Starting development backend:', backendPath);
    }
    
    // Start backend
    if (app.isPackaged) {
        pythonProcess = spawn(pythonCommand, [], {
            cwd: path.dirname(backendPath),
            stdio: 'pipe' // Use pipe to capture output
        });
    } else {
        pythonProcess = spawn(pythonCommand, [backendPath], {
            stdio: 'pipe' // Use pipe to capture output
        });
    }

    // Check if process was created successfully
    if (!pythonProcess) {
        console.error('Failed to start Python backend process');
        return;
    }

    // Handle stdout if available
    if (pythonProcess.stdout) {
        pythonProcess.stdout.on('data', (data) => {
            console.log(`Backend stdout: ${data}`);
        });
    }

    // Handle stderr if available
    if (pythonProcess.stderr) {
        pythonProcess.stderr.on('data', (data) => {
            console.error(`Backend stderr: ${data}`);
        });
    }

    // Handle process close
    pythonProcess.on('close', (code) => {
        console.log(`Backend exited with code ${code}`);
    });

    // Handle process errors
    pythonProcess.on('error', (error) => {
        console.error(`Failed to start backend: ${error.message}`);
    });
}

app.on('ready', () => {
    startPythonBackend();
    setTimeout(createWindow, 2000); // Wait for backend to init
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        if (pythonProcess) pythonProcess.kill();
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) createWindow();
});
