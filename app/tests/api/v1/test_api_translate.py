import json
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.tests.base_test_case import APIBaseTestCase


class TestTranslateApiV1(APIBaseTestCase):

    @pytest.fixture(autouse=True)
    def setup_before_each_test(self):
        self.setup()

    def test_list_languages(self):
        with TestClient(self.app) as client:
            response = client.get(url=self.get_endpoint('/'))
            assert response.status_code == status.HTTP_200_OK
            content = response.json()
            assert content['models'] == {'ca': {'es': ['ca-es']}, 'es': {'ca': ['es-ca']}}
            assert content['languages'] == {
                "es": "Spanish",
                "ca": "Catalan",
                "en": "English",
                "fr": "French",
                "de": "German",
                "it": "Italian",
                "pt": "Portuguese",
                "eu": "Euskera",
                "gl": "Galician",
                "bg": "Bulgarian",
                "cz": "Czech",
                "lt": "Lithuanian",
                "cr": "Croatian",
                "du": "Dutch",
                "ro": "Romanian",
                "da": "Danish",
                "gr": "Greek",
                "fi": "Finnish",
                "hu": "Hungarian",
                "sk": "Slovak",
                "sl": "Slovenian",
                "et": "Estonian",
                "pl": "Polish",
                "lv": "Latvian",
                "sv": "Swedish",
                "mt": "Maltese",
                "ga": "Irish",
                "arn": "Aranese",
                "arg": "Aragonese",
                "ast": "Asturian" 
            }

    def test_translate_text_valid_code(self):
        with TestClient(self.app) as client:
            options = {
                'src': 'es',
                'tgt': 'ca',
                'text': '¿Cómo estás?',
            }
            expected_translation = 'Com estàs?'
            response = client.post(self.get_endpoint('/'), content=json.dumps(options))
            assert response.status_code == status.HTTP_200_OK
            content = response.json()
            assert content['translation'] == expected_translation

    def test_translate_text_invalid_code(self):
        options = {
            'src': 'sfs',
            'tgt': 'xyz',
            'text': 'Hello there, how are you doing?',
        }
        response = self.client.post(self.get_endpoint('/'), content=json.dumps(options))
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_batch_translate_text_valid_code(self):
        options = {
            'src': 'es',
            'tgt': 'ca',
            'texts': ['Hola, ¿Cómo te llamas?', '¿Cómo estás?'],
        }
        expected_translations = ['Hola, com et dius?', 'Com estàs?']
        response = self.client.post(url=self.get_endpoint('/batch'), content=json.dumps(options))
        assert response.status_code == status.HTTP_200_OK
        content = response.json()
        assert content['translation'] == expected_translations

    def test_batch_translate_text_invalid_code(self):
        options = {
            'src': 'es',
            'tgt': 'xyz',
            'texts': ['Hola, ¿Cómo te llamas?', '¿Cómo estás?'],
        }
        response = self.client.post(url=self.get_endpoint('/batch'), content=json.dumps(options))
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
