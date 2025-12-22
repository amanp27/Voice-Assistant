from livekit.agents import llm
from typing import Annotated
import enum
import logging
from db_driver import DatabaseDriver


logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()