from . import LabstatsTestCase
from .. import utils
from django.test.utils import override_settings
from mock import patch, call
import oauth2 as oauth
import json


def sample_valid_space():
    return {
        'id': 5,
        'etag': 'this is the etag',
        'extended_info': {},
        'name': 'space name'
    }


@override_settings(SS_WEB_SERVER_HOST='foo',
                   SS_WEB_OAUTH_KEY='bar',
                   SS_WEB_OAUTH_SECRET='baz')
class UploadTest(LabstatsTestCase):

    def test_upload_sample_spaces(self):
        """Assert that a proper space is sent to the server"""

        fake_space_0 = sample_valid_space()
        fake_spaces = [fake_space_0]

        # Fake a success from the server
        with patch.object(oauth.Client, 'request') as mock:

            mock.return_value = ({'status': 200}, 'it worked')
            result = utils.upload_data(fake_spaces)

        last_call = mock.mock_calls[-1]
        name, args, kwargs = last_call

        # Ensure arguments to Client.request were correct
        self.assertEqual(args[0], 'foo/api/v1/spot/5', 'URL was not correct')
        self.assertEqual(args[1], 'PUT', 'Expected PUT as the method')
        self.assertEqual(json.loads(args[2]), fake_space_0,
                         'Expected PUT as the method')
        expected_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-OAuth-User': 'labstats_daemon',
            'If-Match': fake_space_0['etag']
        }
        self.assertEqual(kwargs['headers'], expected_headers)

        # Ensure our space was listed under 'puts' and 'success_names'
        self.assertIn(fake_space_0['name'], result['puts'])
        self.assertIn({'name': fake_space_0['name'], 'method': 'PUT'},
                      result['success_names'])

    def test_bad_data(self):
        """Assert that several bad spaces are rejected"""
        # id missing
        no_id_space = sample_valid_space()
        del no_id_space['id']
        # id as str instead of int
        bad_id_space = sample_valid_space()
        bad_id_space['id'] = '5'
        # no name
        no_name_space = sample_valid_space()
        del no_name_space['name']
        # not a dictionary
        not_a_dict = [1, 2, 3]
        # cause json.loads to fail
        string_not_valid_json = '{incomplete'

        bad_spaces = (no_id_space, bad_id_space, no_name_space, not_a_dict,
                      string_not_valid_json)

        # Make sure we get warnings
        with patch.object(utils.logger, 'warning') as mock_warnings:
            with patch.object(utils.logger, 'error') as mock_errors:
                result = utils.upload_data(bad_spaces)

        # Assert nothing was successful
        self.assertEqual(len(result['success_names']), 0)
        self.assertEqual(len(result['puts']), 0)

        # Assert errors and warnings were logged
        self.assertEqual(mock_warnings.call_count, 1)
        self.assertEqual(mock_errors.call_count, 7)
