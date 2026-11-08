import json
from langchain_core.callbacks import AsyncCallbackHandler


class TokenProbe(AsyncCallbackHandler):
    async def on_chat_model_start(self, serialized, messages, **kwargs):
        tools = kwargs.get("invocation_params", {}).get("tools", [])
        print(f"[probe] tools: {len(tools)} schemas, {len(json.dumps(tools))} chars")
        total = 0
        for msg in messages[0]:
            size = len(str(msg.content))
            total += size
            print(f"[probe] {msg.type:>6}: {size} chars")
        print(f"[probe] message chars: {total}")