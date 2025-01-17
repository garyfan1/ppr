# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests to verify the V2 registration PDF report setup.

Test-Suite to ensure that the report service registration report is working as expected.
"""
from http import HTTPStatus
import json

from flask import current_app

from mhr_api.reports.v2.report import Report
from mhr_api.reports.v2.report_utils import ReportTypes


REGISTRATON_SOLE_DATAFILE = 'tests/unit/reports/data/registration-sole-example.json'
REGISTRATON_SOLE_PDFFILE = 'tests/unit/reports/data/registration-sole-example.pdf'
REGISTRATON_COMMON_DATAFILE = 'tests/unit/reports/data/registration-common-example.json'
REGISTRATON_COMMON_PDFFILE = 'tests/unit/reports/data/registration-common-example.pdf'
REPORT_VERSION_V2 = '2'


def test_registration_sole(session, client, jwt):
    """Assert that generation of a sole owner report is as expected."""
    # setup
    if is_report_v2():
        json_data = get_json_from_file(REGISTRATON_SOLE_DATAFILE)
        report = Report(json_data, 'PS12345', ReportTypes.MHR_REGISTRATION, 'Account Name')
        # test
        content, status, headers = report.get_pdf()
        assert headers
        # verify
        check_response(content, status, REGISTRATON_SOLE_PDFFILE)


def test_registration_common(session, client, jwt):
    """Assert that generation of a tenants in common owner report is as expected."""
    # setup
    if is_report_v2():
        json_data = get_json_from_file(REGISTRATON_COMMON_DATAFILE)
        report = Report(json_data, 'PS12345', ReportTypes.MHR_REGISTRATION, 'Account Name')
        # test
        content, status, headers = report.get_pdf()
        assert headers
        # verify
        check_response(content, status, REGISTRATON_COMMON_PDFFILE)


def get_json_from_file(data_file: str):
    """Get json data from report data file."""
    text_data = None
    with open(data_file, 'r') as data_file:
        text_data = data_file.read()
        data_file.close()
    # print(text_data)
    json_data = json.loads(text_data)
    return json_data


def check_response(content, status_code, filename: str = None):
    """Assert that report api response is as expected."""
    assert status_code
    assert content
    if status_code != HTTPStatus.OK:
        err_content = content.decode('ascii')
        current_app.logger.warn(f'RS Status code={status_code}. Response: {err_content}.')
    elif filename:
        with open(filename, "wb") as pdf_file:
            pdf_file.write(content)
            pdf_file.close()
    current_app.logger.debug('PDF report generation completed.')


def is_report_v2() -> bool:
    return  current_app.config.get('REPORT_VERSION', '') == REPORT_VERSION_V2
