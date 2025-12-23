from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import openai, noise_cancellation
from prompts import INSTRUCTIONS, WELCOME_MESSAGE
import json
import asyncio

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

server = AgentServer()

@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="shimmer",
            temperature=0.8,
        )
    )

    # Track for transcripts
    async def send_transcript(speaker: str, text: str):
        data = json.dumps({
            "type": "transcript",
            "speaker": speaker,
            "text": text
        })
        try:
            await ctx.room.local_participant.publish_data(data.encode(), reliable=True)
        except:
            pass

    # Listen for agent speech
    @session.on("agent_speech_committed")
    def on_agent_speech(msg):
        asyncio.create_task(send_transcript("Assistant", msg.content if hasattr(msg, 'content') else str(msg)))

    # Listen for user speech  
    @session.on("user_speech_committed")
    def on_user_speech(msg):
        asyncio.create_task(send_transcript("You", msg.content if hasattr(msg, 'content') else str(msg)))

    # Send cost updates
    async def cost_tracker():
        await asyncio.sleep(2)
        while True:
            try:
                cost_data = json.dumps({
                    "type": "cost",
                    "total": 0.0050  # Placeholder - update with real cost tracking
                })
                await ctx.room.local_participant.publish_data(cost_data.encode(), reliable=True)
                await asyncio.sleep(10)
            except:
                break

    asyncio.create_task(cost_tracker())

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() 
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP 
                else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(instructions=WELCOME_MESSAGE)

if __name__ == "__main__":
    agents.cli.run_app(server)