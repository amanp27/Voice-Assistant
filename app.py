import streamlit as st
import streamlit.components.v1 as components
from livekit import api
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

def generate_token():
    room_name = f"voice-assistant-{uuid.uuid4().hex[:8]}"
    participant_name = f"user-{uuid.uuid4().hex[:6]}"
    
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    token.with_identity(participant_name).with_name(participant_name).with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True
        )
    )
    
    return room_name, token.to_jwt()

def main():
    st.markdown("""
        <style>
        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .stButton>button { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎙️ AI Voice Assistant - SIM")
    
    if 'token' not in st.session_state:
        room_name, token = generate_token()
        st.session_state.token = token
        st.session_state.room_name = room_name
    
    clean_url = LIVEKIT_URL.replace('wss://', '').replace('ws://', '')
    token_val = st.session_state.token
    
    livekit_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script crossorigin src="https://cdn.jsdelivr.net/npm/livekit-client@2.5.8/dist/livekit-client.umd.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                padding: 20px;
            }
            #container { 
                background: rgba(255, 255, 255, 0.95); 
                border-radius: 24px; 
                padding: 40px; 
                box-shadow: 0 25px 50px rgba(0,0,0,0.25);
                max-width: 1000px; 
                width: 100%;
            }
            h2 { color: #667eea; text-align: center; margin-bottom: 20px; font-size: 28px; }
            
            #status { 
                text-align: center; 
                padding: 16px; 
                border-radius: 12px; 
                margin: 20px 0; 
                font-weight: 600;
            }
            .connecting { background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); color: #2d3436; }
            .connected { background: linear-gradient(135deg, #55efc4 0%, #00b894 100%); color: #fff; }
            .error { background: linear-gradient(135deg, #ff7675 0%, #d63031 100%); color: #fff; }
            .speaking { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: #fff; }
            
            #cost-display {
                background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
                color: white;
                padding: 16px;
                border-radius: 12px;
                margin: 20px 0;
                text-align: center;
                font-weight: 600;
                font-size: 18px;
            }
            
            #controls { display: flex; gap: 15px; justify-content: center; margin: 25px 0; }
            button { 
                padding: 14px 32px; 
                border: none; 
                border-radius: 12px; 
                font-size: 16px; 
                font-weight: 600; 
                cursor: pointer; 
                transition: all 0.3s;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            button:hover { transform: translateY(-2px); }
            #connect-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            #disconnect-btn { background: linear-gradient(135deg, #ff7675 0%, #d63031 100%); color: white; display: none; }
            #download-btn { background: linear-gradient(135deg, #00b894 0%, #00cec9 100%); color: white; display: none; }
            
            #transcript-container {
                background: #f8f9fa;
                border-radius: 16px;
                padding: 24px;
                margin: 25px 0;
                max-height: 450px;
                overflow-y: auto;
                border: 2px solid #e9ecef;
            }
            #transcript-container h3 { color: #2d3436; margin-bottom: 16px; font-size: 18px; }
            
            .transcript-msg {
                margin: 12px 0;
                padding: 14px 18px;
                border-radius: 12px;
                animation: slideIn 0.3s ease;
                word-wrap: break-word;
            }
            .user-msg {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-left: 60px;
                text-align: right;
            }
            .assistant-msg {
                background: white;
                color: #2d3436;
                margin-right: 60px;
                border: 2px solid #e9ecef;
            }
            .msg-label {
                font-size: 11px;
                opacity: 0.85;
                margin-bottom: 6px;
                font-weight: 700;
                text-transform: uppercase;
            }
            .msg-text { font-size: 15px; line-height: 1.6; }
            
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            #logs { 
                margin-top: 20px; 
                padding: 16px; 
                background: #2d3436; 
                color: #dfe6e9;
                border-radius: 12px; 
                max-height: 120px; 
                overflow-y: auto; 
                font-size: 11px; 
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🎙️ AI Voice Assistant</h2>
            
            <div id="cost-display">
                💰 Cost: $<span id="cost-amount">0.0000</span>
            </div>
            
            <div id="status" class="connecting">Ready to Connect</div>
            
            <div id="controls">
                <button id="connect-btn">🎤 Start Conversation</button>
                <button id="disconnect-btn">⏹️ End Conversation</button>
                <button id="download-btn">💾 Download Audio</button>
            </div>

            <div id="transcript-container">
                <h3>💬 Live Transcript</h3>
                <div id="transcript"></div>
            </div>
            
            <div id="logs"></div>
        </div>

        <script>
            const statusDiv = document.getElementById('status');
            const logsDiv = document.getElementById('logs');
            const transcriptDiv = document.getElementById('transcript');
            const costAmount = document.getElementById('cost-amount');
            const connectBtn = document.getElementById('connect-btn');
            const disconnectBtn = document.getElementById('disconnect-btn');
            const downloadBtn = document.getElementById('download-btn');
            
            let room = null;
            let mediaRecorder = null;
            let audioChunks = [];
            let assistantAudioChunks = [];
            let audioContext = null;
            let mixedRecorder = null;
            let mixedStream = null;

            function log(msg) {
                const time = new Date().toLocaleTimeString();
                logsDiv.innerHTML += '[' + time + '] ' + msg + '<br>';
                logsDiv.scrollTop = logsDiv.scrollHeight;
            }

            function addTranscript(speaker, text) {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'transcript-msg ' + (speaker === 'You' ? 'user-msg' : 'assistant-msg');
                msgDiv.innerHTML = '<div class="msg-label">' + speaker + '</div><div class="msg-text">' + text + '</div>';
                transcriptDiv.appendChild(msgDiv);
                transcriptDiv.scrollTop = transcriptDiv.scrollHeight;
            }

            connectBtn.onclick = async function() {
                try {
                    statusDiv.textContent = '🔄 Connecting...';
                    statusDiv.className = 'connecting';
                    log('Starting connection...');
                    audioChunks = [];
                    assistantAudioChunks = [];
                    transcriptDiv.innerHTML = '';

                    room = new LivekitClient.Room();
                    
                    // Setup audio mixing context
                    audioContext = new AudioContext();
                    const destination = audioContext.createMediaStreamDestination();
                    
                    room.on(LivekitClient.RoomEvent.Connected, async () => {
                        log('Connected!');
                        statusDiv.textContent = '✅ Connected - Start Speaking';
                        statusDiv.className = 'connected';
                        connectBtn.style.display = 'none';
                        disconnectBtn.style.display = 'inline-block';
                        
                        // Get user microphone
                        const userStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        const userSource = audioContext.createMediaStreamSource(userStream);
                        userSource.connect(destination);
                        
                        // Start recording mixed audio
                        mixedStream = destination.stream;
                        mixedRecorder = new MediaRecorder(mixedStream);
                        
                        mixedRecorder.ondataavailable = (e) => {
                            if (e.data.size > 0) audioChunks.push(e.data);
                        };
                        
                        mixedRecorder.start(1000);
                        log('Recording started (mixed audio)');
                    });
                    
                    room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
                        log('Track received: ' + track.kind);
                        if (track.kind === 'audio') {
                            const audioEl = track.attach();
                            audioEl.autoplay = true;
                            document.body.appendChild(audioEl);
                            
                            // Mix assistant audio into recording
                            const assistantSource = audioContext.createMediaElementSource(audioEl);
                            assistantSource.connect(destination);
                            assistantSource.connect(audioContext.destination);
                            
                            statusDiv.textContent = '🤖 Assistant Speaking...';
                            statusDiv.className = 'speaking';
                        }
                    });
                    
                    room.on(LivekitClient.RoomEvent.DataReceived, (data) => {
                        try {
                            const decoded = new TextDecoder().decode(data);
                            const parsed = JSON.parse(decoded);
                            
                            if (parsed.type === 'transcript') {
                                log('Transcript: ' + parsed.speaker + ' - ' + parsed.text);
                                addTranscript(parsed.speaker, parsed.text);
                            } else if (parsed.type === 'cost') {
                                costAmount.textContent = parsed.total.toFixed(4);
                                log('Cost updated: $' + parsed.total.toFixed(4));
                            }
                        } catch (e) {
                            log('Data decode error: ' + e.message);
                        }
                    });
                    
                    room.on(LivekitClient.RoomEvent.TrackUnsubscribed, () => {
                        statusDiv.textContent = '✅ Listening...';
                        statusDiv.className = 'connected';
                    });
                    
                    room.on(LivekitClient.RoomEvent.Disconnected, () => {
                        log('Disconnected');
                        statusDiv.textContent = '⏹️ Conversation Ended';
                        statusDiv.className = 'connecting';
                        connectBtn.style.display = 'inline-block';
                        disconnectBtn.style.display = 'none';
                        
                        if (mixedRecorder && mixedRecorder.state !== 'inactive') {
                            mixedRecorder.stop();
                            downloadBtn.style.display = 'inline-block';
                            log('Recording stopped');
                        }
                    });

                    const url = 'wss://""" + clean_url + """';
                    const token = '""" + token_val + """';
                    
                    await room.connect(url, token);
                    await room.localParticipant.setMicrophoneEnabled(true);
                    log('Microphone enabled');
                    
                } catch (err) {
                    log('ERROR: ' + err.message);
                    statusDiv.textContent = '❌ Failed: ' + err.message;
                    statusDiv.className = 'error';
                }
            };

            disconnectBtn.onclick = async function() {
                if (room) await room.disconnect();
            };

            downloadBtn.onclick = function() {
                if (audioChunks.length > 0) {
                    const blob = new Blob(audioChunks, { type: 'audio/webm' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'conversation_' + new Date().getTime() + '.webm';
                    a.click();
                    log('Full conversation audio downloaded');
                } else {
                    log('No audio to download');
                }
            };

            log('Ready.');
        </script>
    </body>
    </html>
    """
    
    components.html(livekit_html, height=900)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Room:** `{st.session_state.room_name}`")
    with col2:
        if st.button("🔄 New Session"):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()