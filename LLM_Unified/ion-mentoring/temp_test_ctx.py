from persona_system.models import ChatContext
ctx = ChatContext(user_id="u", session_id="s", custom_context={})
ctx.custom_context["running_summary"] = "hello"
print(ctx.custom_context)
