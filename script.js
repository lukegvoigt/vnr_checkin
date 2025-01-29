// Set the worker path to point to the CDN
QrScanner.WORKER_PATH = 'https://unpkg.com/qr-scanner/qr-scanner-worker.min.js';

var resultContainer = document.getElementById('qr-reader-results');
var lastResult, countResults = 0;
const statusDisplay = document.getElementById('status-display');

const attendees = [
    { id: '1000', name: 'Alice', checkedIn: false },
    { id: '1001', name: 'Bob', checkedIn: false },
    { id: '1002', name: 'Charlie', checkedIn: false },
    { id: '1003', name: 'David', checkedIn: false },
    { id: '1004', name: 'Eve', checkedIn: false },
    { id: '1005', name: 'Frank', checkedIn: false }
];

let qrScanner = null;
let lastResult = null;

function isValidAttendeeId(id) {
    const numId = parseInt(id);
    return !isNaN(numId) && numId >= 1000 && numId <= 5000;
}

function showModal(message) {
    const modal = document.getElementById('confirmModal');
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.classList.remove('hidden');
}

function hideModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.add('hidden');
}

function processCheckIn(qrCodeData) {
    const attendeeId = qrCodeData;
    const attendee = attendees.find(attendee => attendee.id === attendeeId);

    if (attendee) {
        if (!attendee.checkedIn) {
            attendee.checkedIn = true;
            showModal(`${attendee.name} checked in successfully.`);
        } else {
            showModal(`${attendee.name} is already checked in.`);
        }
    } else {
        showModal(`Attendee ID ${attendeeId} not found.`);
    }

    if (qrScanner) qrScanner.pause();
}

async function initializeScanner() {
    console.log('Initializing scanner...');
    const videoElement = document.querySelector('video');
    
    try {
        qrScanner = new QrScanner(
            videoElement,
            result => {
                console.log('Scan result:', result);
                if (isValidAttendeeId(result.data)) {
                    processCheckIn(result.data);
                }
            },
            {
                returnDetailedScanResult: true,
                highlightScanRegion: true,
                highlightCodeOutline: true,
                preferredCamera: 'environment',
            }
        );

        const hasCamera = await QrScanner.hasCamera();
        console.log('Has camera:', hasCamera);
        
        if (!hasCamera) {
            showModal('No camera found on this device.');
            return false;
        }

        // List available cameras
        const cameras = await QrScanner.listCameras();
        console.log('Available cameras:', cameras);

        return true;
    } catch (error) {
        console.error('Scanner initialization error:', error);
        showModal('Error initializing scanner: ' + error.message);
        return false;
    }
}

const scanButton = document.getElementById('scanButton');
let scanning = false;

scanButton.addEventListener('click', async () => {
    console.log('Scan button clicked');
    
    if (!qrScanner) {
        console.log('Initializing scanner on first click');
        const initialized = await initializeScanner();
        if (!initialized) {
            console.error('Failed to initialize scanner');
            return;
        }
    }

    if (!scanning) {
        console.log('Starting scanner...');
        try {
            await qrScanner.start();
            scanButton.textContent = 'Stop Scan';
            scanning = true;
            console.log('Scanner started successfully');
        } catch (error) {
            console.error('Error starting camera:', error);
            showModal('Error starting camera: ' + error.message);
        }
    } else {
        console.log('Stopping scanner...');
        qrScanner.stop();
        scanButton.textContent = 'Start Scan';
        scanning = false;
    }
});

document.getElementById('confirmButton').addEventListener('click', () => {
    hideModal();
    if (qrScanner && scanning) {
        qrScanner.start();
    }
});

// Initialize scanner when page loads
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Page loaded, initializing scanner...');
    try {
        await initializeScanner();
        console.log('Scanner initialized on page load');
    } catch (error) {
        console.error('Error during initial scanner setup:', error);
    }
});
