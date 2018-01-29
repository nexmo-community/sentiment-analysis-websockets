import os
import uuid
import hug
import nexmo


class CallObjectServer():

    def __init__(self):
        self.conversation_name = str(uuid.uuid4())
        self.nexmo_client = nexmo.Client(
            application_id=os.environ['NEXMO_APPLICATION_ID'],
            private_key='private.key'
        )

    def start(self):

        self.nexmo_client.create_call({
            'to': [{'type': 'phone', 'number': os.environ['TEST_HANDSET']}],
            'from': {'type': 'phone', 'number': os.environ['NEXMO_FROM_NUMBER']},
            'answer_url': ['https://nexmo-sentiment.ngrok.io/moderator']
        })

        self.ws_call = self.nexmo_client.create_call({
            'to': [
                {
                    "type": "websocket",
                    "uri": "ws://nexmo-sentiment-sockets.ngrok.io/audio",
                    "content-type": "audio/l16;rate=16000",
                    "headers": {}
                }
            ],
            'from': {'type': 'phone', 'number': os.environ['NEXMO_FROM_NUMBER']},
            'answer_url': ['https://nexmo-sentiment.ngrok.io/attendee']
        })

        return [
            {
                "action": "talk",
                "text": "Please wait while we connect you"
            },
            {
                "action": "conversation",
                "name": self.conversation_name,
                "startOnEnter": "false",
                "musicOnHoldUrl": ["https://nexmo-sentiment.ngrok.io/hold.mp3"]
            }
        ]

    def moderator(self):
        return [
            {
                "action": "conversation",
                "name": self.conversation_name,
                "record": "true",
                "endOnExit": "true"
            }
        ]

    def attendee(self):
        return [
            {
                "action": "conversation",
                "name": self.conversation_name,
                "startOnEnter": "false",
                "musicOnHoldUrl": ["https://nexmo-sentiment.ngrok.io/hold.mp3"]
            }
        ]

    def static(self):
        return open('bensound-acousticbreeze.mp3', mode='rb')


server = CallObjectServer()

router = hug.route.API(__name__)
router.get('/')(server.start)
router.get('/hold.mp3', output=hug.output_format.file)(server.static)
router.get('/moderator')(server.moderator)
router.get('/attendee')(server.attendee)
