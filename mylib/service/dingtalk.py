import json
import hashlib
import base64
import hmac
import os
import time
import requests
from urllib.parse import quote_plus


class DingtalkService:
    def __init__(self, webhook_url, secret=None):
        self.webhook_url = webhook_url
        self.secret = secret

    def sign(self, timestamp):
        secret = self.secret.encode('utf-8') if self.secret else None
        signature = '{}\n{}'.format(timestamp, self.secret)
        signature = hmac.new(secret, signature.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(signature).decode('utf-8')
        return signature

    def verify(self, signature, timestamp):
        expected_signature = self.sign(timestamp)
        return hmac.compare_digest(expected_signature, signature)

    def send(self, text):
        """
        :param text:
        :return:
        """
        headers = {'Content-Type': 'application/json'}
        if self.secret:
            timestamp = str(round(time.time() * 1000))
            signature = self.sign(timestamp)
            headers['timestamp'] = timestamp
            headers['sign'] = signature

        message = {
            'msgtype': 'text',
            'text': {
                'content': text
            }
        }

        response = requests.post(self.webhook_url, data=json.dumps(message), headers=headers)
        return response.json()

