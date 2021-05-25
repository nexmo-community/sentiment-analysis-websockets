import os
import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import requests
from logzero import logger
from ibm_watson import ToneAnalyzerV3
from ibm_watson.tone_analyzer_v3 import ToneInput
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv

load_dotenv()

class DashboardHandler(tornado.websocket.WebSocketHandler):

    waiters = set()

    def check_origin(self, origin):
        return True

    def open(self):
        logger.warning('Dashboard socket open')
        DashboardHandler.waiters.add(self)

    def on_close(self):
        logger.warning('Dashboard socket closed')
        DashboardHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, tones):
        logger.warning('Sending update')
        logger.warning(tones)

        for waiter in cls.waiters:
            try:
                waiter.write_message(tones)
            except:
                pass


class AudioHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, **kwargs):
        pass

    def open(self):
        logger.warning('Audio socket open')
        self.transcriber = tornado.websocket.websocket_connect(
            'wss://api.{location}.speech-to-text.watson.cloud.ibm.com/instances/{instance}/v1/recognize?access_token={token}&model={model}'.format(
                location=os.environ['TRANSCRIBER_SERVER_LOCATION'],
                instance=os.environ['TRANSCRIBER_SERVER_INSTANCE_ID'],
                token=self.transcriber_token(),
                model='en-UK_NarrowbandModel'
            ),
            on_message_callback=self.on_transcriber_message
        )

        authenticator = IAMAuthenticator(os.environ['TONE_ANALYZER_API_KEY'])
        self.tone_analyzer = ToneAnalyzerV3(
            version='2017-09-21',
            authenticator=authenticator
        )
        self.tone_analyzer.set_service_url(os.environ['TONE_ANALYZER_URL'])

    def transcriber_token(self):
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': os.environ['TRANSCRIBER_API_KEY']
        }

        resp = requests.post(
            url='https://iam.cloud.ibm.com/identity/token',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data
            )
            
        respJson = json.loads(resp.content.decode('utf-8'))
        return respJson['access_token']

    @gen.coroutine
    def on_message(self, message):
        transcriber = yield self.transcriber

        if type(message) != str:
            transcriber.write_message(message, binary=True)
        else:
            logger.error(message)
            data = json.loads(message)
            data['action'] = "start"
            data['continuous'] = True
            data['interim_results'] = True
            transcriber.write_message(json.dumps(data), binary=False)

    @gen.coroutine
    def on_close(self):
        logger.warning('Audio socket closed')

        transcriber = yield self.transcriber
        data = {'action': 'stop'}
        transcriber.write_message(json.dumps(data), binary=False)
        transcriber.close()

    def on_transcriber_message(self, message):
        if message:
            message = json.loads(message)
            if 'results' in message:
                transcript = message['results'][0]['alternatives'][0]['transcript']
                tone_results = self.tone_analyzer.tone(
                    tone_input=ToneInput(transcript),
                    content_type="application/json").get_result()
                tones = tone_results['document_tone']['tones']

                DashboardHandler.send_updates(json.dumps(tones))



if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/audio", AudioHandler),
        (r"/dashboard", DashboardHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 3000))
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
