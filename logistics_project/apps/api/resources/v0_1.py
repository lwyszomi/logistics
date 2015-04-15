from django.contrib.auth.models import User
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.bundle import Bundle
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.paginator import Paginator
from tastypie.resources import ModelResource, Resource
from dimagi.utils.dates import force_to_datetime
from logistics.warehouse_models import SupplyPointWarehouseRecord
from logistics_project.apps.tanzania.models import SupplyPointStatus, DeliveryGroupReport, DeliveryGroups
from logistics_project.apps.tanzania.reporting.models import OrganizationSummary, GroupSummary, ProductAvailabilityData, \
    Alert, OrganizationTree
from rapidsms.contrib.locations.models import Point, Location
from tastypie import fields
from logistics.models import Product, LogisticsProfile, SupplyPoint, StockTransaction, ProductStock
from rapidsms.models import Contact, Connection


class CustomResourceMeta(object):
    authorization = ReadOnlyAuthorization()
    authentication = BasicAuthentication()
    default_format = 'application/json'


class ProductResources(ModelResource):

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = Product.objects.all()
        include_resource_uri = False
        fields = ['name', 'units', 'sms_code', 'description', 'is_active']
        list_allowed_methods = ['get']


class UserResource(ModelResource):
    username = fields.CharField('username', null=True)

    class Meta(CustomResourceMeta):
        queryset = User.objects.all()
        list_allowed_methods = ['get']
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_staff', 'is_active', 'is_superuser',
                  'last_login', 'date_joined']
        include_resource_uri = False
        filtering = {
            'date_joined': ('gte', )
        }


class WebUserResources(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    location = fields.IntegerField('location_id', null=True)
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['user'].data['location'] = bundle.data['location']
        bundle.data['user'].data['supply_point'] = bundle.data['supply_point']
        bundle.data = bundle.data['user'].data
        return bundle

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = LogisticsProfile.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['location', 'supply_point']
        filtering = {
            'user': ALL_WITH_RELATIONS
        }


class PointResource(ModelResource):
    latitude = fields.CharField('latitude')
    longitude = fields.CharField('longitude')

    class Meta(CustomResourceMeta):
        queryset = Point.objects.all()
        list_allowed_methods = ['get']
        fields = ['latitude', 'longitude']
        include_resource_uri = False


class Group(object):

    def __init__(self, location_id=None, groups=None):
        self.location_id = location_id
        self.groups = groups


class CustomPaginator(Paginator):

    def get_slice(self, limit, offset):
        return self.objects

    def get_count(self):
        return SupplyPoint.objects.filter(active=True).count()


class GroupResources(Resource):

    location_id = fields.IntegerField(attribute='location_id')
    groups = fields.DictField(attribute='groups')

    class Meta(CustomResourceMeta):
        resource_name = 'groups'
        list_allowed_methods = ['get']
        object_class = Group
        include_resource_uri = False
        paginator_class = CustomPaginator

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.supply_point
        else:
            kwargs['pk'] = bundle_or_obj.supply_point

        return kwargs

    def _get_object(self, supply_point):
        summaries = GroupSummary.objects.filter(
            org_summary__supply_point=supply_point,
            total=1
        ).only('org_summary__date', 'title', 'total')
        groups = {}
        for summary in summaries:
            date_string = str(summary.org_summary.date.date())
            if date_string not in groups:
                groups[date_string] = []

            if summary.title == 'rr_fac':
                groups[date_string].append(
                    DeliveryGroups(summary.org_summary.date.month).current_submitting_group()
                )
            if summary.title == 'del_fac':
                groups[date_string].append(
                    DeliveryGroups(summary.org_summary.date.month).current_delivering_group()
                )

        for k, v in groups.iteritems():
            if not v:
                groups[k] = [DeliveryGroups(force_to_datetime(k).month).current_processing_group()]
        return Group(supply_point.location.id, groups)

    def obj_get(self, bundle, **kwargs):
        return self._get_object(SupplyPoint.objects.get(pk=kwargs['pk']))

    def get_object_list(self, request):
        group_list = []
        limit = int(request.GET.get('limit', 1000))
        offset = int(request.GET.get('offset', 0))
        for supply_point in SupplyPoint.objects.filter(active=True).order_by('id')[offset:(offset + limit)]:
            group_list.append(self._get_object(supply_point))
        return group_list

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class LocationResources(ModelResource):
    id = fields.IntegerField('id')
    name = fields.CharField('name')
    type = fields.CharField('type')
    parent_id = fields.IntegerField('parent_id', null=True)
    points = fields.ToOneField(PointResource, 'point', full=True, null=True)
    code = fields.CharField('code')
    groups = fields.ListField(null=True, default=[])

    class Meta(CustomResourceMeta):
        queryset = Location.objects.filter(supplypoint__active=True)
        list_allowed_methods = ['get']
        details_allowed_methods = ['get']
        fields = ['id', 'name', 'parent_id', 'code', 'groups', 'date_updated']
        include_resource_uri = False
        filtering = {
            'date_updated': ('gte', ),
            'type': ('exact', )
        }

    def dehydrate(self, bundle):
        try:
            sp = SupplyPoint.objects.get(pk=bundle.data['id'])
            bundle.data['groups'] = list(sp.groups.all())
            bundle.data['created_at'] = sp.created_at
        except SupplyPoint.DoesNotExist:
            bundle.data['groups'] = []
            bundle.data['historical_groups'] = {}
        bundle.data['latitude'] = ""
        bundle.data['longitude'] = ""
        if bundle.data['points']:
            bundle.data['latitude'] = bundle.data['points'].data['latitude']
            bundle.data['longitude'] = bundle.data['points'].data['longitude']
        del bundle.data['points']
        return bundle


class SMSUserResources(ModelResource):
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.IntegerField('supply_point_id', null=True)
    is_active = fields.CharField('is_active')

    def dehydrate(self, bundle):
        connection = bundle.obj.default_connection
        if connection:
            bundle.data['backend'] = str(connection.backend)
            bundle.data['phone_numbers'] = [connection.identity]
        else:
            bundle.data['backend'] = ""
            bundle.data['phone_numbers'] = []
        return bundle

    class Meta(CustomResourceMeta):
        queryset = Contact.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['id', 'language', 'name', 'email', 'role', 'supply_point', 'is_active', 'date_updated']
        filtering = {
            'date_updated': ('gte', )
        }


class StockTransactionResources(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['product'] = bundle.obj.product.sms_code
        bundle.data['report_type'] = bundle.obj.product_report.report_type
        return bundle

    class Meta(CustomResourceMeta):
        queryset = StockTransaction.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        excludes = ['id', ]
        filtering = {
            "date": ('gte', ),
            "supply_point": ('exact', )
        }
        ordering = ['date']


class ProductStockResources(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['product'] = bundle.obj.product.sms_code
        return bundle

    class Meta(CustomResourceMeta):
        queryset = ProductStock.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        excludes = ['id', 'days_stocked_out', 'manual_monthly_consumption', 'use_auto_consumption']
        filtering = {
            "last_modified": ('gte', ),
            "supply_point": ('exact', )
        }


class SupplyPointStatusResource(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    class Meta(CustomResourceMeta):
        queryset = SupplyPointStatus.objects.all().order_by('status_date')
        include_resource_uri = False
        list_allowed_methods = ['get']
        ordering = ['status_date']

        filtering = {
            "status_date": ('gte', ),
            "supply_point": ('exact', )
        }


class DeliveryGroupReportResources(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['delivery_group'] = bundle.obj.delivery_group
        return bundle

    class Meta(CustomResourceMeta):
        queryset = DeliveryGroupReport.objects.all().order_by('report_date')
        include_resource_uri = False
        list_allowed_methods = ['get']

        filtering = {
            "report_date": ('gte', ),
            "supply_point": ('exact', )
        }


class OrganizationSummaryResource(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    class Meta(CustomResourceMeta):
        queryset = OrganizationSummary.objects.all()
        include_resource_uri = False
        filtering = {
            "supply_point": ('exact', ),
            "update_date": ('gte', 'lte'),
            "create_date": ('gte', 'lte'),
            "date": ('gte', 'lte')
        }


class GroupSummaryResource(ModelResource):
    org_summary = fields.ToOneField(OrganizationSummaryResource, 'org_summary', full=True, null=True)

    class Meta(CustomResourceMeta):
        queryset = GroupSummary.objects.all()
        include_resource_uri = False
        filtering = {
            'org_summary': ALL_WITH_RELATIONS
        }


class ProductAvailabilityDataResource(ModelResource):

    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['product'] = bundle.obj.product.sms_code
        return bundle

    class Meta(CustomResourceMeta):
        queryset = ProductAvailabilityData.objects.all().order_by('update_date')
        include_resource_uri = False
        filtering = {
            "supply_point": ('exact', ),
            "update_date": ('gte', 'lte'),
            "create_date": ('gte', 'lte'),
            "date": ('gte', 'lte'),
        }


class AlertResources(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    class Meta(CustomResourceMeta):
        queryset = Alert.objects.all().order_by('update_date')
        include_resource_uri = False
        filtering = {
            "supply_point": ('exact', ),
            "update_date": ('gte', 'lte'),
            "create_date": ('gte', 'lte'),
            "date": ('gte', 'lte'),
            "expires": ('gte', 'lte'),
        }


class OrganizationTreeResources(ModelResource):
    below = fields.IntegerField('below_id', null=True)
    above = fields.IntegerField('above_id', null=True)

    class Meta(CustomResourceMeta):
        include_resource_uri = False
        queryset = OrganizationTree.objects.all()
        filtering = {
            "below": ('exact', ),
            "above": ('exact', )
        }


class SPWarehouseRecordResource(ModelResource):
    supply_point_id = fields.IntegerField('supply_point_id', null=True)
    
    class Meta(CustomResourceMeta):
        include_resource_uri = False
        fields = ['id', 'create_date', 'supply_point_id']
        resource_name = 'supply_point_warehouse_records'
        queryset = SupplyPointWarehouseRecord.objects.all()
