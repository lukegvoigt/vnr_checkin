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

function isValidAttendeeId(id) {
    // Check if the ID is a number and within valid range (1000-5000)
    const numId = parseInt(id);
    return !isNaN(numId) && numId >= 1000 && numId <= 5000;
}

function onScanSuccess(decodedText, decodedResult) {
    // Validate the scanned text
    if (!isValidAttendeeId(decodedText)) {
        console.log('Invalid QR code value:', decodedText);
        return; // Silently ignore invalid codes and continue scanning
    }

    if (decodedText !== lastResult) {
        ++countResults;
        lastResult = decodedText;
        console.log(`Scan result ${decodedText}`, decodedResult);
        processCheckIn(decodedText);
        
        // Restart scanner after successful check-in
        html5QrcodeScanner.clear().then(() => {
            setTimeout(() => {
                startScanning();
            }, 2000); // Wait 1 second before restarting
        });
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

// Initialize the scanner
const html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader",
    { 
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
        defaultCamera: "environment",
        formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ] // Only support QR codes
    }
);

function startScanning() {
    html5QrcodeScanner.render(onScanSuccess, (error) => {
        // Only show errors in console, not to user
        console.error(`QR scanning failed: ${error}`);
        
        // Don't update status display for parsing errors
        if (!error.includes("QR code parse error")) {
            statusDisplay.textContent = `Camera error. Please try again.`;
            statusDisplay.style.color = 'red';
        }
    });
}

const scanButton = document.getElementById('scanButton');
let scanning = false;

scanButton.addEventListener('click', () => {
    if (!scanning) {
        startScanning();
        scanButton.textContent = 'Stop Scan';
    } else {
        html5QrcodeScanner.clear();
        scanButton.textContent = 'Start Scan';
    }
    scanning = !scanning;
});

// Start scanning automatically when page loads
startScanning();
