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
"""This module holds model data and database operations for financing statements."""

# pylint: disable=too-many-statements, too-many-branches

from __future__ import annotations

from enum import Enum
from http import HTTPStatus

#from sqlalchemy import event

from ppr_api.exceptions import BusinessException
from ppr_api.utils.datetime import format_ts, now_ts_offset, expiry_dt_from_years,\
                                   expiry_ts_from_iso_format
from ppr_api.models import utils as model_utils

from .db import db
from .registration import Registration  # noqa: F401 pylint: disable=unused-import; needed by the SQLAlchemy relationship
from .trust_indenture import TrustIndenture  # noqa: F401 pylint: disable=unused-import; needed by the SQLAlchemy relationship
from .party import Party  # noqa: F401 pylint: disable=unused-import; needed by the SQLAlchemy relationship
from .general_collateral import GeneralCollateral  # noqa: F401 pylint: disable=unused-import; needed by the SQLAlchemy relationship
from .vehicle_collateral import VehicleCollateral  # noqa: F401 pylint: disable=unused-import; needed by the SQLAlchemy relationship


class FinancingStatement(db.Model):  # pylint: disable=too-many-instance-attributes
    """This class maintains financing statement information."""

    class FinancingTypes(Enum):
        """Render an Enum of the financing statement types."""

        SECURITY_AGREEMENT = 'SA'
        SALE_OF_GOODS = 'SG'
        REPAIRERS_LIEN = 'RL'
        MARRIAGE_MH = 'FR'
        LAND_TAX_LIEN = 'LT'
        MANUFACTURED_HOME_LIEN = 'MH'
        FORESTRY_CONTRACTOR_LIEN = 'FL'
        FORESTRY_CONTRACTOR_CHARGE = 'FA'
        FORESTRY_SUBCONTRACTOR_LIEN = 'FS'
        MISCELLANEOUS = 'MR'

    __versioned__ = {}
    __tablename__ = 'financing_statement'

#    financing_id = db.Column('financing_id', db.Integer, primary_key=True, server_default=db.FetchedValue())
    financing_id = db.Column('financing_id', db.Integer,
                             db.Sequence('financing_id_seq'), primary_key=True)
    state_type_cd = db.Column('state_type_cd', db.String(3), nullable=False)
                              #, db.ForeignKey('state_type.state_type_cd'))
    registration_num = db.Column('registration_number', db.String(10), nullable=False)
    life = db.Column('life', db.Integer, nullable=True)
    expire_date = db.Column('expire_date', db.DateTime, nullable=True)
    discharged = db.Column('discharged', db.String(1), nullable=True)
    renewed = db.Column('renewed', db.String(1), nullable=True)

    type_claim = db.Column('type_claim', db.String(2), nullable=True)
    crown_charge_type = db.Column('crown_charge_type', db.String(2), nullable=True)
    crown_charge_other = db.Column('crown_charge_other', db.String(70), nullable=True)
    prev_reg_type = db.Column('prev_reg_type', db.Integer, nullable=True)
    prev_reg_cr_nbr = db.Column('prev_reg_cr_nbr', db.String(7), nullable=True)
    prev_reg_cr_date = db.Column('prev_reg_cr_date', db.String(7), nullable=True)
    prev_reg_cb_nbr = db.Column('prev_reg_cb_nbr', db.String(10), nullable=True)
    prev_reg_cb_date = db.Column('prev_reg_cb_date', db.String(7), nullable=True)
    prev_reg_mh_nbr = db.Column('prev_reg_mh_nbr', db.String(7), nullable=True)
    prev_reg_mh_date = db.Column('prev_reg_mh_date', db.String(7), nullable=True)

    # Parent keys

    # Relationships
    registration = db.relationship("Registration", order_by="asc(Registration.registration_ts)",
                                   back_populates="financing_statement")
    parties = db.relationship("Party", back_populates="financing_statement")
    vehicle_collateral = db.relationship("VehicleCollateral", back_populates="financing_statement")
    general_collateral = db.relationship("GeneralCollateral", back_populates="financing_statement")
    trust_indenture = db.relationship("TrustIndenture", back_populates="financing_statement")


    @property
    def json(self) -> dict:
        """Return the financing statement as a json object."""
        statement = {
        }

        if self.registration and self.registration[0]:
            reg = self.registration[0]
            registration_id = reg.registration_id
            statement['type'] = reg.registration_type_cd
            statement['baseRegistrationNumber'] = reg.registration_num
            statement['createDateTime'] = format_ts(reg.registration_ts)

            if reg.client_reference_id:
                statement['clientReferenceId'] = reg.client_reference_id

#            if reg.document_number:
#                statement['documentId'] = reg.document_number

            if self.parties:
                debtors = []
                secured = []
                for party in self.parties:
                    if party.party_type_cd == 'RG' and party.registration_id == registration_id:
                        statement['registeringParty'] = party.json
                    elif party.party_type_cd == 'SP' and not party.registration_id_end:
                        secured.append(party.json)
                    elif (party.party_type_cd == 'DB' or party.party_type_cd == 'DI') and \
                            not party.registration_id_end:
                        debtors.append(party.json)

                statement['securedParties'] = secured
                statement['debtors'] = debtors

            if self.general_collateral:
                gen_collateral = []
                for collateral in self.general_collateral:
                    if not collateral.registration_id_end:
                        gen_collateral.append(collateral.json)

                if gen_collateral:
                    statement['generalCollateral'] = gen_collateral

            if self.vehicle_collateral:
                v_collateral = []
                for collateral in self.vehicle_collateral:
                    if not collateral.registration_id_end:
                        v_collateral.append(collateral.json)

                if v_collateral:
                    statement['vehicleCollateral'] = v_collateral

            if reg.registration_type_cd == model_utils.REG_TYPE_REPAIRER_LIEN:
                if reg.lien_value:
                    statement['lienAmount'] = reg.lien_value
                if reg.surrender_date:
                    statement['surrenderDate'] = format_ts(reg.surrender_date)

        if self.trust_indenture:
            for trust in self.trust_indenture:
                if not trust.registration_id_end:
                    if trust.trust_indenture == 'Y':
                        statement['trustIndenture'] = True
                    else:
                        statement['trustIndenture'] = False
        else:
            statement['trustIndenture'] = False

        if self.life and self.life == model_utils.LIFE_INFINITE:
            statement['lifeInfinite'] = True
        elif self.life:
            statement['lifeYears'] = self.life

        if self.expire_date:
            statement['expiryDate'] = format_ts(self.expire_date)

        return statement


    def validate_base_debtor(self, base_debtor_json, staff: bool = False):
        """Verify supplied base debtor when registering non-financing statements. Bypass the check for staff."""
        valid = False

        if staff:
            return True

        if not base_debtor_json:
            return False

        bus_name = None
        last = None
        first = None
        middle = None
        if 'businessName' in base_debtor_json:
            bus_name = base_debtor_json['businessName'].strip().upper()
        elif 'personName' in base_debtor_json:
            last = base_debtor_json['personName']['last'].strip().upper()
            first = base_debtor_json['personName']['first'].strip().upper()
            if 'middle' in base_debtor_json['personName']:
                middle = base_debtor_json['personName']['middle'].strip().upper()

        if self.parties:
            for party in self.parties:
                if (party.party_type_cd == 'DB' or party.party_type_cd == 'DI') and \
                        not party.registration_id_end:
                    if bus_name and party.business_name and \
                            bus_name == party.business_name.upper():
                        valid = True
                    else:
                        last_match = (last and party.last_name and last == party.last_name.upper())
                        first_match = (first and party.first_name and first == party.first_name.upper())
                        middle_match = (not middle and not party.middle_name) or \
                                       (middle and party.middle_name and middle == party.middle_name.upper())
                        if last_match and first_match and middle_match:
                            valid = True

        return valid


    def save(self):
        """Save the object to the database immediately."""

        db.session.add(self)
        db.session.commit()

        # Now save draft.registration_id
        draft = self.registration[0].draft
        draft.registration_id = self.registration[0].registration_id
        db.session.add(draft)
        db.session.commit()



    @classmethod
    def find_all_by_account_id(cls, account_id: str = None, staff: bool = False):
        """Return a summary list of recent financing statements belonging to an account."""
        statement_list = None
        if account_id:
            # No date range restriction for staff?
            if staff:
                statement_list = db.session.query(Registration.registration_ts,\
                                                  Registration.registration_num,\
                                                  Registration.registration_type_cd,\
                                                  FinancingStatement.state_type_cd).\
                                    filter(FinancingStatement.financing_id == Registration.financing_id,\
                                           Registration.account_id == account_id,\
                                           Registration.registration_type_cl.in_(['PPSALIEN', 'MISCLIEN'])).\
                                    order_by(FinancingStatement.financing_id).all()
            else:
                days_ago = now_ts_offset(10, False)
                statement_list = db.session.query(Registration.registration_ts,\
                                                  Registration.registration_num,\
                                                  Registration.registration_type_cd,\
                                                  FinancingStatement.state_type_cd).\
                                    filter(FinancingStatement.financing_id == Registration.financing_id,\
                                           Registration.account_id == account_id,\
                                           Registration.registration_type_cl.in_(['PPSALIEN', 'MISCLIEN']),\
                                           Registration.registration_ts > days_ago).\
                                    order_by(FinancingStatement.financing_id).all()

        if not statement_list:
            raise BusinessException(
                error=f'No Financing Statements found for Account ID {account_id}.',
                status_code=HTTPStatus.NOT_FOUND
            )

        results_json = []
        # only staff may view historical
        for statement in statement_list:
            if staff or statement.state_type_cd == model_utils.STATE_ACTIVE:
                statement_json = {
                    'matchType': 'EXACT',
                    'createDateTime': format_ts(statement.registration_ts),
                    'baseRegistrationNumber': statement.registration_num,
                    'registrationType': statement.registration_type_cd
                }
                results_json.append(statement_json)

        # Non-staff, all historical/discharged
        if not results_json:
            raise BusinessException(
                error=f'No active Financing Statements found for Account ID {account_id}.',
                status_code=HTTPStatus.NOT_FOUND
            )

        return results_json


    @classmethod
    def find_by_id(cls, financing_id: int = None):
        """Return a financing statement object by financing ID."""
        statement = None
        if financing_id:
            statement = cls.query.get(financing_id)

        return statement


    @classmethod
    def find_by_registration_number(cls, registration_num: str = None,
                                    staff: bool = False):
        """Return a financing statement by registration number."""
        statement = None
        if registration_num:
            statement = cls.query.filter(FinancingStatement.financing_id == Registration.financing_id, \
                                          Registration.registration_num == registration_num, \
                                          Registration.registration_type_cl.in_(['PPSALIEN', 'MISCLIEN'])).one_or_none()

        if not statement:
            raise BusinessException(
                error=f'No Financing Statement found for registration number {registration_num}.',
                status_code=HTTPStatus.NOT_FOUND
            )

        if not staff and statement.state_type_cd != model_utils.STATE_ACTIVE:
            raise BusinessException(
                error=f'The Financing Statement for registration number {registration_num} has been discharged.',
                status_code=HTTPStatus.BAD_REQUEST
            )

        return statement


    @classmethod
    def find_by_financing_id(cls, financing_id: int = None):
        """Return a financing statement by financing statement ID."""
        statement = None
        if financing_id:
            statement = cls.query.filter(FinancingStatement.financing_id == Registration.financing_id, \
                                         FinancingStatement.financing_id == financing_id).one_or_none()

        return statement


    @staticmethod
    def create_from_json(json_data, account_id: str):
        """Create a draft object from a json Draft schema object: map json to db."""
        # Perform all addtional data validation checks.
        FinancingStatement.validate(json_data)

        statement = FinancingStatement()
        statement.state_type_cd = model_utils.STATE_ACTIVE

        # Do this early as it also checks the party codes and may throw an exception
        statement.parties = Party.create_from_financing_json(json_data, None)

        reg_type = json_data['type']
        if reg_type == model_utils.REG_TYPE_REPAIRER_LIEN:
            statement.expire_date = now_ts_offset(model_utils.REPAIRER_LIEN_DAYS, True)
            statement.life = model_utils.REPAIRER_LIEN_YEARS
        elif 'lifeInfinite' in json_data and json_data['lifeInfinite']:
            statement.life = model_utils.LIFE_INFINITE
        else:
            if 'lifeYears' in json_data:
                statement.life = json_data['lifeYears']
                if statement.life > 0:
                    statement.expire_date = expiry_dt_from_years(statement.life)
            if 'expiryDate' in json_data and not statement.expire_date:
                statement.expire_date = expiry_ts_from_iso_format(json_data['expiryDate'])

        statement.registration = [Registration.create_financing_from_json(json_data, account_id)]
        statement.registration_num = statement.registration[0].registration_num
        registration_id = statement.registration[0].registration_id
        statement.trust_indenture = TrustIndenture.create_from_json(json_data, registration_id)
        if 'vehicleCollateral' in json_data:
            statement.vehicle_collateral = VehicleCollateral.create_from_financing_json(json_data, registration_id)
        if 'generalCollateral' in json_data:
            statement.general_collateral = GeneralCollateral.create_from_financing_json(json_data, registration_id)

        for party in statement.parties:
            party.registration_id = registration_id

        return statement



    @staticmethod
    def validate(json_data):
        """Perform any extra data validation here, either because it is too

        complicated for the schema, or because it requires existing data (client party codes).
        """

        error_msg = ''

        # Verify the party codes.
        error_msg = error_msg + FinancingStatement.validate_parties(json_data)

        if error_msg != '':
            raise BusinessException(
                error=error_msg,
                status_code=HTTPStatus.BAD_REQUEST
            )


    @staticmethod
    def validate_parties(json_data):
        """Verify party codes."""
        error_msg = ''
        code = None

        if 'registeringParty' in json_data and 'code' in json_data['registeringParty']:
            code = json_data['registeringParty']['code']
            if not Party.verify_party_code(code):
                error_msg = error_msg + 'No registering party client party found for code ' + code + '. '

        if 'securedParties' in json_data:
            for party in json_data['securedParties']:
                if 'code' in party:
                    code = party['code']
                    if not Party.verify_party_code(code):
                        error_msg = error_msg + 'No secured party client party found for code ' + code + '. '

        return error_msg
