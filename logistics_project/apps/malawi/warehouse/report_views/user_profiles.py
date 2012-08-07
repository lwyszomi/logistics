from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.models import UserProfileData

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        district_table = {
            "id": "district_table",
            "is_datatable": True,
            "header": ["District", "Code", "Facilities", "HSA supervisors", "HSAs", "Contacts"],
            "data": [],
        }
        facility_table = {
            "id": "facility_table",
            "is_datatable": True,
            "header": ["Facility", "Code", "GPS coordinate", "In Charge", "HSA supervisors", "Supervisor Contacts", "HSAs"],
            "data": [],
        }
        hsa_table = {
            "id": "hsa_table",
            "is_datatable": True,
            "header": ["HSA Name", "Id", "Contact Info", "Products", "Date of last message", "Last Message"],
            "data": [],
        }
        district = SupplyPoint.objects.none()
        facility = SupplyPoint.objects.none()
        if request.GET.get('district'):
            district = SupplyPoint.objects.get(code=request.GET.get('district'))
        if request.GET.get('facility'):
            facility = SupplyPoint.objects.get(code=request.GET.get('facility'))

        for up in UserProfileData.objects.all():
            if up.supply_point.type.code == 'd':
                district_table["data"].append({ "url": _get_url(up.supply_point), "data":
                        [up.supply_point.name, up.supply_point.code, up.facility_children, 
                        up.hsa_supervisors, up.hsa_children, up.contacts]})
            elif up.supply_point.type.code == 'hf':
                if request.GET.get('district'):
                    if up.supply_point.supplied_by.code == request.GET.get('district'):
                        gps_coord = "No Data"
                        if up.supply_point.location.point:
                            if up.supply_point.location.point.latitude and up.supply_point.location.point.longitude:
                                gps_coord = "(%.2f,%.2f)" % (up.supply_point.location.point.latitude,
                                    up.supply_point.location.point.longitude)
                        facility_table["data"].append({ "url": _get_url(up.supply_point), "data":
                                [up.supply_point.name, up.supply_point.code, gps_coord, 
                                up.in_charge, up.hsa_supervisors, up.supervisor_contacts, up.hsa_children]})
            elif up.supply_point.type.code == 'hsa':
                if request.GET.get('facility'):
                    if up.supply_point.supplied_by.code == request.GET.get('facility'):
                        hsa_table["data"].append([up.supply_point.name, up.supply_point.code,
                                up.contact_info, up.products_managed,
                                up.last_message.date.strftime("%b-%d-%Y"), up.last_message.text])

        return {
                "district": district,
                "facility": facility,
                "district_table": district_table,
                "facility_table": facility_table,
                "hsa_table": hsa_table,
                }

def _get_url(supply_point):
    querystring = 'district=%s' % supply_point.code\
        if supply_point.type.code == 'd' else 'district=%s&facility=%s' % (supply_point.supplied_by.code, supply_point.code)
    return '/malawi/r/user-profiles/?%s' % querystring

