// Configuration
const SOCKET_SERVER_URL = 'http://localhost:7777';
const RECORDING_TIME_SLICE = 100; // Send audio chunks every 100ms

// Global variables
let socket;
let mediaRecorder;
let audioChunks = [];
let isConnected = false;

// DOM Elements
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const status = document.getElementById('status');
const connectionStatus = document.getElementById('connectionStatus');

// Socket.IO setup
function setupSocket() {
    socket = io(SOCKET_SERVER_URL);

    socket.on('connect', () => {
        console.log('Connected to server');
        isConnected = true;
        updateConnectionStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isConnected = false;
        updateConnectionStatus(false);
    });

    socket.on('error', (error) => {
        console.error('Socket error:', error);
        status.textContent = 'Connection error occurred';
    });
}

// Update UI to show connection status
function updateConnectionStatus(connected) {
    connectionStatus.textContent = connected ? 'Connected' : 'Disconnected';
    connectionStatus.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
}

// Initialize socket connection
setupSocket();

// Start recording function
async function startRecording() {
    try {
        // Reset the chunks array
        audioChunks = [];
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Create the MediaRecorder instance
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        // Handle data available event
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                // Store chunk locally
                audioChunks.push(event.data);
                
                // Send chunk to server if connected
                if (isConnected) {
                    socket.emit('audioChunk', event.data);
                }
            }
        };
        
        // Start recording with timeslice to get data periodically
        mediaRecorder.start(RECORDING_TIME_SLICE);
        
        // Update UI
        startButton.disabled = true;
        stopButton.disabled = false;
        status.textContent = 'Recording...';
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        status.textContent = 'Error: Could not access microphone';
    }
}

// Stop recording function
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        
        mediaRecorder.onstop = () => {
            // Create final blob from recorded chunks
            const audioBlob = new Blob(audioChunks, { 
                type: 'audio/webm;codecs=opus' 
            });
            
            // Send final chunk to server
            if (isConnected) {
                socket.emit('recordingComplete', audioBlob);
            }
            
            // Create download link
            const audioUrl = URL.createObjectURL(audioBlob);
            const link = document.createElement('a');
            link.href = audioUrl;
            link.download = `recording-${new Date().getTime()}.webm`;
            
            // Trigger download
            link.click();
            
            // Cleanup
            URL.revokeObjectURL(audioUrl);
            
            // Stop all audio tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            // Reset UI
            startButton.disabled = false;
            stopButton.disabled = true;
            status.textContent = 'Recording saved!';
        };
    }
}

// Event listeners
startButton.addEventListener('click', startRecording);
stopButton.addEventListener('click', stopRecording);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (socket) {
        socket.disconnect();
    }
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
});