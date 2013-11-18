#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *

reportpatterns = patterns('logistics_project.apps.malawi.warehouse.views', 
    url(r'^r/home/$', 'home', name='malawi_dashboard'),
    url(r'^r/(?P<slug>[\w\s-]+)/$','get_report', name=''),
)
urlpatterns = patterns('',

    url(r'^management/$',
        "logistics_project.apps.malawi.views.organizations",
        name="malawi_management"),
    url(r'^management/organizations/$',
        "logistics_project.apps.malawi.views.organizations",
        name="malawi_organizations"),
    url(r'^management/organizations/new/$',
        "logistics_project.apps.malawi.views.new_organization",
        name="malawi_new_organization"),
    url(r'^management/organizations/edit/(?P<pk>\d+)/$',
        "logistics_project.apps.malawi.views.edit_organization",
        name="malawi_edit_organization"),
    url(r'^management/contacts/$',
        "logistics_project.apps.malawi.views.contacts",
        name="malawi_contacts"),
    url(r'^management/permissions/$',
        "logistics_project.apps.malawi.views.permissions",
        name="malawi_permissions"),
    url(r'^management/permissions/edit/(?P<pk>\d+)/$',
        "logistics_project.apps.malawi.views.edit_permission",
        name="malawi_edit_permissions"),
    url(r'^management/places/$',
        "logistics_project.apps.malawi.views.places",
        name="malawi_places"),
    url(r'^management/products/$',
        "logistics_project.apps.malawi.views.products",
        name="malawi_products"),
    url(r'^management/products/(?P<pk>\d+)/$',
        "logistics_project.apps.malawi.views.single_product",
        name="malawi_single_product"),
    url(r'^management/products/(?P<pk>\d+)/deactivate/$',
        "logistics_project.apps.malawi.views.deactivate_product_view",
        name="malawi_deactivate_product"),
    url(r'^management/sms-tracking/$',
        "logistics_project.apps.malawi.views.sms_tracking",
        name="malawi_sms_tracking"),
    url(r'^management/telco-tracking/$',
        "logistics_project.apps.malawi.views.telco_tracking",
        name="malawi_telco_tracking"),
    
    url(r'^management/facilities/$',
        'logistics_project.apps.malawi.views.manage_facilities',
        name='malawi_manage_facilities'),
    url(r'^management/download_facilities/$',
        'logistics_project.apps.malawi.views.download_facilities',
        name='download_facilities'),
    url(r'^management/upload_facilities/$',
        'logistics_project.apps.malawi.views.upload_facilities',
        name='upload_facilities'),
    url(r'^management/outreach/$',
        'logistics_project.apps.malawi.views.outreach',
        name='malawi_manage_outreach'),
    url(r'^management/outreach/send/$',
        'logistics_project.apps.malawi.views.send_outreach',
        name='malawi_manage_outreach_send'),

    url(r'^hsas/$',
        "logistics_project.apps.malawi.views.hsas",
        name="malawi_hsas"),
    url(r'^hsa/(?P<code>\d+)/$',
        "logistics_project.apps.malawi.views.hsa",
        name="malawi_hsa"),
    url(r'^deactivate/(?P<pk>\d+)/$',
         "logistics_project.apps.malawi.views.deactivate_hsa",
        name="deactivate_hsa"),
     url(r'^reactivate/(?P<code>\d+)/(?P<name>.+)/$',
         "logistics_project.apps.malawi.views.reactivate_hsa",
        name="reactivate_hsa"),
    url(r'^help/$',
        "logistics_project.apps.malawi.views.help",
        name="malawi_help"),
    url(r'^status/$',
        "logistics_project.apps.malawi.views.status",
        name="malawi_status"),
    url(r'^airtel-users/$',
        "logistics_project.apps.malawi.views.airtel_numbers",
        name="malawi_airtel"),
    url(r'^register-hsa/$',
        "logistics_project.apps.malawi.views.register_user",
        name="malawi_hsa"),
    url(r'^scmgr/receiver/$',
        "logistics_project.apps.malawi.views.scmgr_receiver",
        name="malawi_scmgr_receiver"),
    url(r'^facilities/$',
        "logistics_project.apps.malawi.views.facilities",
        name="malawi_facilities"),
    url(r'^facilities/(?P<code>\d+)/$',
        "logistics_project.apps.malawi.views.facility",
        name="malawi_facility"),
    url(r'^monitoring/$',
        "logistics_project.apps.malawi.views.monitoring",
        name="malawi_monitoring"),
    url("^monitoring/(?P<report_slug>[\w_]+)/$", 
        "logistics_project.apps.malawi.views.monitoring_report",
        name="malawi_monitoring_report"),
    url(r'^export_amc/$',
        "logistics_project.apps.malawi.views.export_amc_csv",
        name="export_amc_csv"),
    url(r'^global_stats/$',
        "logistics.views.global_stats",
        name="global_stats"),

) + reportpatterns

