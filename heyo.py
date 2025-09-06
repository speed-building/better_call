import json
from twilio.rest import Client

account_sid = "AC673f51e5cdb701bf4092fbc2d267a95d"
auth_token = "86c19040cef23ba5d1d253dbd7671e6d"
client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+5533999942000",
    from_="+18576637141",
    url="https://handler.twilio.com/twiml/EH0ccb7a1d231ca96f31859460f376465d"
)

print("Created Call SID:", call.sid)

# Fetch the latest call record
fresh = client.calls(call.sid).fetch()

# Dump all attributes to JSON
print(f"call.trunk_sid {call.trunk_sid}")
print(f"caller_name {call.caller_name}")
print(f"parent_call_sid {call.parent_call_sid}")
print(f"subresource_uris {call.subresource_uris}")
print(f"answered_by {call.answered_by}")
print(f"phone_number_sid {call.phone_number_sid}")
print(f"group_sid {call.group_sid}")
