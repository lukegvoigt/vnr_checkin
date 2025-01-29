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

function onScanSuccess(decodedText, decodedResult) {
    if (decodedText !== lastResult) {
        ++countResults;
        lastResult = decodedText;
        console.log(`Scan result ${decodedText}`, decodedResult);
        processCheckIn(decodedText);
    }
}

function processCheckIn(qrCodeData) {
    const attendeeId = qrCodeData;
    const attendee = attendees.find(attendee => attendee.id === attendeeId);

    if (attendee) {
        if (!attendee.checkedIn) {
            attendee.checkedIn = true;
            statusDisplay.textContent = `${attendee.name} checked in successfully.`;
            statusDisplay.style.color = 'green';
        } else {
            statusDisplay.textContent = `${attendee.name} is already checked in.`;
            statusDisplay.style.color = 'orange';
        }
    } else {
        statusDisplay.textContent = `Attendee ID ${attendeeId} not found.`;
        statusDisplay.style.color = 'red';
    }
}

function startScanning() {
    html5QrcodeScanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 250 },
        onScanSuccess,
        (errorMessage) => {
            console.error(`QR scanning failed: ${errorMessage}`);
            statusDisplay.textContent = `QR scanning failed: ${errorMessage}`;
            statusDisplay.style.color = 'red';
        }
    );
}

function stopScanning() {
    html5QrcodeScanner.stop();
}

const scanButton = document.getElementById('scanButton');
let scanning = false;

scanButton.addEventListener('click', () => {
    if (!scanning) {
        startScanning();
        scanButton.textContent = 'Stop Scan';
    } else {
        stopScanning();
        scanButton.textContent = 'Start Scan';
    }
    scanning = !scanning;
});

startScanning();
