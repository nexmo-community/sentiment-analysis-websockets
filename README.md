Sentiment analysis of voice calls using IBM Watson
==================================================

This is the companion code for the ["Add Sentiment Analysis to Your Inbound Call Flow with IBM Watson and Nexmo" webinar](https://attendee.gotowebinar.com/recording/7952180850491069704). Please view the webinar
recording for full details on how to run this example.

Quickstart
----------

There are several environment variables in `call_objects.py` and `ws_server.py` which should be
set to the correct values in your environment.

    NEXMO_APPLICATION_ID
    TEST_HANDSET
    NEXMO_FROM_NUMBER
    TONE_ANALYZER_USERNAME
    TONE_ANALYZER_PASSWORD
    TRANSCRIBER_USERNAME
    TRANSCRIBER_PASSWORD

You should also update all urls within `call_objects.py` to point to your ngrok address.

    # This code has been tested with Python 3.6.3
    # Install dependencies
    pip install -r requirements.txt

    # Run Hug server
    hug -f call_objects.py

    # Run Tornado server
    python ws_server.py

