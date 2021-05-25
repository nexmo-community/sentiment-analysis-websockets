import os
import uuid
import hug
import vonage
from dotenv import load_dotenv

load_dotenv()

class CallObjectServer():

    def __init__(self):
        self.conversation_name = str(uuid.uuid4())
        self.vonage_client = vonage.Client(
            application_id=os.environ['VONAGE_APPLICATION_ID'],
            private_key='private.key'
        )

    def start(self):
        self.vonage_client.create_call({
            'to': [{'type': 'phone', 'number': os.environ['TEST_HANDSET']}],
            'from': {'type': 'phone', 'number': os.environ['VONAGE_FROM_NUMBER']},
            'answer_url': ['https://' + os.environ['BASE_URL'] + '/moderator']
        })

        self.ws_call = self.vonage_client.create_call({
            'to': [
                {
                    "type": "websocket",
                    "uri": "ws://" + os.environ['SOCKET_BASE_URL'] + "/audio",
                    "content-type": "audio/l16;rate=16000",
                    "headers": {}
                }
            ],
            'from': {'type': 'phone', 'number': os.environ['VONAGE_FROM_NUMBER']},
            'answer_url': ['https://' + os.environ['BASE_URL'] + '/attendee']
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
                "musicOnHoldUrl": ["https://" + os.environ['BASE_URL'] + "/hold.mp3"]
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
                "musicOnHoldUrl": ["https://" + os.environ['BASE_URL'] + "/hold.mp3"]
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
