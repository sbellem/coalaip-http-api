from flask import Blueprint
from flask_restful import reqparse, Resource, Api

from coalaip import CoalaIp, ModelDataError, models
from coalaip_bigchaindb.plugin import Plugin
from web.models import right_model, user_model
from web.utils import get_bigchaindb_api_url


coalaip = CoalaIp(Plugin(get_bigchaindb_api_url()))

right_views = Blueprint('right_views', __name__)
right_api = Api(right_views)


class RightApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('right', type=right_model, required=True,
                            location='json')
        parser.add_argument('sourceRightId', type=str, required=True,
                            location='json')
        parser.add_argument('currentHolder', type=user_model, required=True,
                            location='json')
        args = parser.parse_args()

        source_right_id = args['sourceRightId']
        right = args['right']
        right['allowedBy'] = source_right_id

        current_holder = args['currentHolder']
        current_holder['verifying_key'] = current_holder.pop('verifyingKey')
        current_holder['signing_key'] = current_holder.pop('signingKey')

        right = coalaip.derive_right(right_data=right,
                                     current_holder=current_holder)

        res = {'right': right.to_jsonld()}

        return res


class RightTransferApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('rightId', type=right_model, required=True,
                            location='json')
        parser.add_argument('currentHolder', type=user_model, required=True,
                            location='json')
        parser.add_argument('to', type=user_model, required=True,
                            location='json')
        parser.add_argument('rightsAssignment', type=dict, location='json')
        args = parser.parse_args()

        right_id = args['rightId']
        current_holder = args['currentHolder']
        to = args['to']
        rights_assignment = args['rights_assignment']

        for user in [current_holder, to]:
            user['verifying_key'] = user.pop('verifyingKey')
            user['signing_key'] = user.pop('signingKey')

        # We can't be sure of the type of Right that's given by using just the
        # id, so let's assume it's a normal Right first before trying to make a
        # Copyright
        try:
            right = models.Right.from_persist_id(right_id,
                                                 plugin=coalaip.plugin,
                                                 force_load=True)
        except ModelDataError:
            right = models.Copyright.from_persist_id(right_id,
                                                     plugin=coalaip.plugin,
                                                     force_load=True)

        res = coalaip.transfer_right(right=right,
                                     rights_assignment_data=rights_assignment,
                                     current_holder=current_holder,
                                     to=to)

        res = {'rightsAssignment': res.to_jsonld()}

        return res


right_api.add_resource(RightApi, '/rights', strict_slashes=False)
right_api.add_resource(RightTransferApi, '/rights/transfer', strict_slashes=False)
