from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool
from livekit.plugins import (
    openai,
    noise_cancellation,
)
# Agent framework components
# AgentServer   -> Runs the agent as a LiveKit worker
# AgentSession  -> Manages one live agent session per room
# Agent         -> Base class for creating AI agents
# room_io       -> Audio / room configuration helpers
# function_tool -> Decorator to expose Python functions as LLM tools

import random

from prompts import INSTRUCTIONS, WELCOME_MESSAGE



load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)

    # @function_tool
    # async def get_weather(self):
    #     return random.choice(["It's Sunny", "It's Rainy", "It's Snowy"])
    
    # @function_tool
    # async def get_news(self):
    #     return random.choice([
    #         "The latest news is about....",
    #         "There is an EarthQuake in Nepal",
    #         "A new Movie is released"
    #     ])


# Creates a LiveKit Agent Server
# This server listens for job requests from LiveKit rooms
server = AgentServer()

# RTC SESSION HANDLER
@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="shimmer" # Human-like voice for speech output
        )
    )

    # Start the agent session with room and agent configuration
    await session.start(
        room=ctx.room,   # LiveKit room object
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(), # Apply different noise cancellation based on participant type
            ),
        ),
    )


    # Send the welcome message after the agent joins
    # This triggers the first spoken response
    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )

# APPLICATION ENTRY POINT
if __name__ == "__main__":
    agents.cli.run_app(server) # Run the agent server as a LiveKit worker