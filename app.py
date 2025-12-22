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
            body { margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            #container { background: white; border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 600px; width: 100%; }
            h2 { color: #667eea; text-align: center; }
            #status { text-align: center; padding: 15px; border-radius: 10px; margin: 20px 0; font-weight: 500; }
            .connecting { background: #fff3cd; color: #856404; }
            .connected { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            button { padding: 12px 30px; border: none; border-radius: 25px; font-size: 16px; font-weight: 600; cursor: pointer; background: #667eea; color: white; display: block; margin: 20px auto; }
            button:hover { background: #5568d3; }
            #disconnect-btn { background: #dc3545; display: none; }
            #logs { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 10px; max-height: 200px; overflow-y: auto; font-size: 12px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div id="container">
            <h2>🎙️ Voice Assistant</h2>
            <div id="status" class="connecting">Ready</div>
            <button id="connect-btn">Start Conversation</button>
            <button id="disconnect-btn">End Conversation</button>
            <div id="logs"></div>
        </div>

        <script>
            const statusDiv = document.getElementById('status');
            const logsDiv = document.getElementById('logs');
            const connectBtn = document.getElementById('connect-btn');
            const disconnectBtn = document.getElementById('disconnect-btn');
            let room = null;

            function log(msg) {
                const time = new Date().toLocaleTimeString();
                logsDiv.innerHTML += '[' + time + '] ' + msg + '<br>';
                logsDiv.scrollTop = logsDiv.scrollHeight;
                console.log(msg);
            }

            connectBtn.onclick = async function() {
                try {
                    statusDiv.textContent = 'Connecting...';
                    statusDiv.className = 'connecting';
                    log('Starting connection...');

                    if (typeof LivekitClient === 'undefined') {
                        throw new Error('LiveKit library not loaded');
                    }

                    room = new LivekitClient.Room();
                    
                    room.on(LivekitClient.RoomEvent.Connected, () => {
                        log('Connected!');
                        statusDiv.textContent = '✅ Connected - Start speaking';
                        statusDiv.className = 'connected';
                        connectBtn.style.display = 'none';
                        disconnectBtn.style.display = 'block';
                    });
                    
                    room.on(LivekitClient.RoomEvent.TrackSubscribed, (track) => {
                        log('Received track: ' + track.kind);
                        if (track.kind === 'audio') {
                            const el = track.attach();
                            document.body.appendChild(el);
                            statusDiv.textContent = '🤖 Assistant speaking...';
                            log('Playing audio');
                        }
                    });
                    
                    room.on(LivekitClient.RoomEvent.Disconnected, () => {
                        log('Disconnected');
                        statusDiv.textContent = 'Disconnected';
                        statusDiv.className = 'connecting';
                        connectBtn.style.display = 'block';
                        disconnectBtn.style.display = 'none';
                    });

                    const url = 'wss://""" + clean_url + """';
                    const token = '""" + token_val + """';
                    
                    log('Connecting to: ' + url);
                    await room.connect(url, token);
                    
                    log('Enabling microphone...');
                    await room.localParticipant.setMicrophoneEnabled(true);
                    log('Microphone enabled');
                    
                } catch (err) {
                    log('ERROR: ' + err.message);
                    statusDiv.textContent = '❌ Failed: ' + err.message;
                    statusDiv.className = 'error';
                }
            };

            disconnectBtn.onclick = async function() {
                if (room) {
                    await room.disconnect();
                }
            };

            log('Ready. Click Start Conversation.');
        </script>
    </body>
    </html>
    """
    
    components.html(livekit_html, height=700)
    
    st.markdown(f"**Room:** `{st.session_state.room_name}`")
    st.markdown(f"**URL:** `{LIVEKIT_URL}`")
    
    if st.button("🔄 New Session"):
        st.session_state.clear()
        st.rerun()

if __name__ == '__main__':
    main()