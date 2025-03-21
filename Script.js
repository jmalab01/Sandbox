let uploadedData = []; // Store uploaded data for later access
let anomalyLowerBound = -2000;  // Default lower bound
let anomalyUpperBound = 2800;   // Default upper bound

// Handle file upload and parse the file
document.getElementById("fileInput").addEventListener("change", handleFileUpload);

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });

        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        uploadedData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        console.log("✅ Data uploaded successfully:", uploadedData);
    };
    reader.readAsArrayBuffer(file);
}

// Save the user-defined anomaly range
function saveAnomalyRange() {
    anomalyLowerBound = parseFloat(document.getElementById("anomalyLower").value);
    anomalyUpperBound = parseFloat(document.getElementById("anomalyUpper").value);

    if (isNaN(anomalyLowerBound) || isNaN(anomalyUpperBound)) {
        alert("Please enter valid numbers for anomaly range.");
        return;
    }

    alert(`✅ Anomaly range saved!\nLower Bound: ${anomalyLowerBound}\nUpper Bound: ${anomalyUpperBound}`);
}

// Validate the uploaded file and show the validation modal
function uploadFileForValidation() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("lower_bound", anomalyLowerBound);
    formData.append("upper_bound", anomalyUpperBound);

    console.log(`🚀 Sending file with custom anomaly range: ${anomalyLowerBound} to ${anomalyUpperBound}`);

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("✅ Backend response:", data);

        let validationResult = document.getElementById("validationResult");
        if (!validationResult) {
            alert("Error: Validation report element not found.");
            return;
        }

        let resultText = `<div style="font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.5em;">`;
        resultText += `📊 **Financial Data Validation Report**\n\n`;
        resultText += `**Total Anomalies Found:** ${data.anomalies_found}\n\n`;

        if (data.error) {
            resultText += `<b>🚨 Error:</b> ${data.error}\n`;
        } else if (data.anomalies.length > 0) {
            resultText += `**Anomalies Detected:**\n\n`;
            data.anomalies.forEach((anomaly, index) => {
                let rowIndex = anomaly.row_index !== undefined ? `Row ${anomaly.row_index}` : "Unknown Row";
                let reason = anomaly.reason !== undefined ? anomaly.reason : "No specific reason provided";
                
                let dataDetails = anomaly.data ? formatDataDetails(anomaly.data) : "No data available";

                resultText += `<b>#${index + 1} - ${rowIndex}</b>\n`;
                resultText += `<b>Reason:</b> ${reason}\n`;
                resultText += `<b>Data:</b>\n${dataDetails}\n\n`;
            });
        } else {
            resultText += "✅ **No anomalies detected. Your data looks good!**\n";
        }

        resultText += `</div>`;
        validationResult.innerHTML = resultText;

        // Open the modal
        $("#validationModal").modal("show");
    })
    .catch(error => {
        console.error("❌ Fetch Error:", error);
        alert("Validation failed: " + error.message);
    });
}

// Function to format data details for readability
function formatDataDetails(data) {
    let formatted = "";
    Object.entries(data).forEach(([key, value]) => {
        formatted += `  ${key}: ${value},\n`;
    });
    return formatted.trim();
}

// Open Data in a Table Popup
function openDataWindow() {
    if (uploadedData.length === 0) {
        alert("No data uploaded to display.");
        return;
    }

    let popup = window.open("", "Data Preview", "width=800,height=600");
    popup.document.write("<html><head><title>Data Preview</title>");
    popup.document.write("<style> table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid black; padding: 8px; text-align: left; } </style>");
    popup.document.write("</head><body><h2>Data Preview</h2><table>");

    let headers = uploadedData[0];
    popup.document.write("<tr>");
    headers.forEach(header => popup.document.write(`<th>${header}</th>`));
    popup.document.write("</tr>");

    uploadedData.slice(1).forEach(row => {
        popup.document.write("<tr>");
        row.forEach(cell => popup.document.write(`<td>${cell}</td>`));
        popup.document.write("</tr>");
    });
    popup.document.write("</table></body></html>");
    popup.document.close();
}

// Clear Data
function clearUpload() {
    document.getElementById("fileInput").value = "";
    uploadedData = [];
    document.getElementById("anomalyLower").value = "";
    document.getElementById("anomalyUpper").value = "";
    alert("✅ Data cleared successfully.");
}

// Toggle Dark Mode
function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
    document.querySelectorAll(".card").forEach(card => card.classList.toggle("dark-mode"));
    document.querySelectorAll(".navbar").forEach(navbar => navbar.classList.toggle("dark-mode"));
    document.querySelectorAll(".modal-content").forEach(modal => modal.classList.toggle("dark-mode"));
    document.querySelectorAll(".table").forEach(table => table.classList.toggle("dark-mode"));
    document.querySelectorAll("input[type='file']").forEach(input => input.classList.toggle("dark-mode"));

    localStorage.setItem("darkMode", document.body.classList.contains("dark-mode"));
}

// Apply Dark Mode if previously enabled
document.addEventListener("DOMContentLoaded", function () {
    if (localStorage.getItem("darkMode") === "true") {
        toggleDarkMode();
    }
});
