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

// Initialize the scanner with smaller QR box for mobile
const html5QrcodeScanner = new Html5QrcodeScanner(
    "qr-reader",
    { 
        fps: 10,
        qrbox: { width: 200, height: 200 }, // Smaller QR box
        aspectRatio: 1.0,
        defaultCamera: "environment",
        formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ]
    }
);

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

function onScanSuccess(decodedText, decodedResult) {
    if (!isValidAttendeeId(decodedText)) {
        console.log('Invalid QR code value:', decodedText);
        return;
    }

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
            showModal(`${attendee.name} checked in successfully.`);
        } else {
            showModal(`${attendee.name} is already checked in.`);
        }
    } else {
        showModal(`Attendee ID ${attendeeId} not found.`);
    }

    html5QrcodeScanner.pause();
}

function startScanning() {
    html5QrcodeScanner.render(onScanSuccess, (error) => {
        console.error(`QR scanning failed: ${error}`);
        if (!error.includes("QR code parse error")) {
            const statusDisplay = document.getElementById('status-display');
            statusDisplay.textContent = `Camera error. Please try again.`;
            statusDisplay.classList.add('text-red-500');
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

document.getElementById('confirmButton').addEventListener('click', () => {
    hideModal();
    html5QrcodeScanner.clear().then(() => {
        setTimeout(() => {
            startScanning();
        }, 1000);
    });
});

startScanning();
