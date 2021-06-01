import os
import uuid
import hug
import vonage
from dotenv import load_dotenv
from typing import List

load_dotenv()

class CallObjectServer():

    def __init__(self):
        self.conversation_name = str(uuid.uuid4())
        self.vonage_client = vonage.Client(
            application_id=os.getenv('VONAGE_APPLICATION_ID'),
            private_key='private.key'
        )

    def start(self) -> List[dict]:
        self.vonage_client.create_call({
            'to': [{'type': 'phone', 'number': os.getenv('TEST_HANDSET')}],
            'from': {'type': 'phone', 'number': os.getenv('VONAGE_FROM_NUMBER')},
            'answer_url': ['https://' + os.getenv('BASE_URL') + '/moderator']
        })

        self.ws_call = self.vonage_client.create_call({
            'to': [
                {
                    "type": "websocket",
                    "uri": "ws://" + os.getenv('SOCKET_BASE_URL') + "/audio",
                    "content-type": "audio/l16;rate=16000",
                    "headers": {}
                }
            ],
            'from': {'type': 'phone', 'number': os.getenv('VONAGE_FROM_NUMBER')},
            'answer_url': ['https://' + os.getenv('BASE_URL') + '/attendee']
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
                "musicOnHoldUrl": ["https://" + os.getenv('BASE_URL') + "/hold.mp3"]
            }
        ]

    def moderator(self) -> List[dict]:
        return [
            {
                "action": "conversation",
                "name": self.conversation_name,
                "record": "true",
                "endOnExit": "true"
            }
        ]

    def attendee(self) -> List[dict]:
        return [
            {
                "action": "conversation",
                "name": self.conversation_name,
                "startOnEnter": "false",
                "musicOnHoldUrl": ["https://" + os.getenv('BASE_URL') + "/hold.mp3"]
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