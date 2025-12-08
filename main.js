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
    const backendPath = path.join(__dirname, 'backend', 'app.py');
    // Assume 'python3' is in path and dependencies installed
    pythonProcess = spawn('python3', [backendPath]);

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Backend exited with code ${code}`);
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
