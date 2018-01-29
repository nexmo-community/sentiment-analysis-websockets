import os
import json

from watson_developer_cloud import ToneAnalyzerV3
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import requests
from logzero import logger


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
            'wss://stream.watsonplatform.net/speech-to-text/api/v1/recognize?watson-token={token}&model={model}'.format(
                token=self.transcriber_token(),
                model='en-UK_NarrowbandModel'
            ),
            on_message_callback=self.on_transcriber_message
        )

        self.tone_analyzer = ToneAnalyzerV3(
            username=os.environ['TONE_ANALYZER_USERNAME'],
            password=os.environ['TONE_ANALYZER_PASSWORD'],
            version='2016-05-19'
        )

    def transcriber_token(self):
        resp = requests.get(
            'https://stream.watsonplatform.net/authorization/api/v1/token',
            auth=(os.environ['TRANSCRIBER_USERNAME'], os.environ['TRANSCRIBER_PASSWORD']),
            params={'url': "https://stream.watsonplatform.net/speech-to-text/api"}
        )

        return resp.content.decode('utf-8')

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
                tone_results = self.tone_analyzer.tone(text=transcript)
                tones = tone_results['document_tone']['tone_categories'][0]['tones']

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
