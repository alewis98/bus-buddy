def build_response(text):
    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': text,
            }
        }
    }
    return response


def on_launch(intent_request, session):
    return build_response("Welcome to Bus Buddy")


def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]
    if intent_name == "GetNextBus":
        text = "Getting Next Bus"
    else:
        raise ValueError("Invalid intent")
    return build_response(text)


def lambda_handler(event, context):  
    if event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    else:
        return build_response("I think an error occurred")