"""Usage resource for handling any usage requests"""
from flask import jsonify
from webargs import fields
from webargs.flaskparser import use_kwargs
from flask_restful import Resource

from sqlalchemy import func, case
from src.models.base import db

from datetime import date

from src.models.cycles import BillingCycle
from src.models.usages import DataUsage
from src.models.service_codes import Plan

from src.models.subscriptions import Subscription
from src.models.utils import get_object_or_404
from src.schemas.subscriptions import SubscriptionSchema
from marshmallow import fields, Schema

class DataUsageAPI(Resource):
    """Resource/routes for subscriptions endpoints"""

    @use_kwargs(SubscriptionSchema(partial=True), locations=("query",))
    def get(self, **kwargs):
        """External facing subscription list endpoint GET

        Gets a list of Subscription object with given args

        Args:
            kwargs (dict): filters to apply to query Subscriptions

        Returns:
            json: serialized list of Subscription objects

CASE WHEN p.is_unlimited==0 THEN sum(mb_used)>p.mb_available ELSE 0 END AS is_over
from data_usages as du
LEFT JOIN subscriptions as s on s.id = du.subscription_id
LEFT JOIN plans as p on p.id = s.plan_id
#where from_date>='2019-09-01' and to_date<'2019-10-01' group by subscription_id

        """

        from_date = date.fromisoformat('2019-09-10')
        print("Today's date:", from_date)
        cycle = BillingCycle.get_current_cycle(from_date)

        xpr = case([(Plan.is_unlimited==0, func.sum(DataUsage.mb_used)>Plan.mb_available), ], else_=0).label('mb_used')
        data = db.session.query(DataUsage, \
                                xpr,   \
                                Plan.mb_available,\
                                Plan.is_unlimited) \
            .join(Subscription, Subscription.id == DataUsage.subscription_id) \
            .join(Plan, Plan.id == Subscription.plan_id) \
            .filter(DataUsage.from_date >= cycle.start_date) \
            .filter(DataUsage.to_date <= cycle.end_date) \
            .group_by(DataUsage.subscription_id)
        data2 = data.all();
        result = Schema().dump(data2, many=True)
        return jsonify(result)