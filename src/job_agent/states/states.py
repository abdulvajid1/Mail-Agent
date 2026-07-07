import operator
from typing_extensions import TypedDict, Annotated
from langchain.messages import AnyMessage


class AgentState(TypedDict): # Can be replaced using MessageState
    messages: Annotated[list[AnyMessage], operator.add]