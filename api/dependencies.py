from fastapi import Request


def get_agent(request: Request):
    return request.app.state.agente


def get_checkpointer(request: Request):
    return request.app.state.checkpointer

