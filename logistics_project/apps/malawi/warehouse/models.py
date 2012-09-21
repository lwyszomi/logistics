from django.db import models
from logistics.warehouse_models import ReportingModel, BaseReportingModel
from logistics_project.apps.malawi.util import fmt_pct, pct, hsas_below
from static.malawi.config import TimeTrackerTypes
from datetime import datetime
from dimagi.utils.dates import first_of_next_month, delta_secs

class MalawiWarehouseModel(ReportingModel):
    
    class Meta:
        abstract = True
        app_label = "malawi"

class ProductAvailabilityData(MalawiWarehouseModel):
    """
    This will be used to generate the "current stock status" table,
    as well as anything that needs to compute percent with / without 
    stock, oversupplied, undersupplied, etc.
    """
    # NOTE/DRAGONS: there's some hard-coded stuff that depends on this list 
    # matching up with fields below, and in the summary model. Be careful
    # changing property names.
    STOCK_CATEGORIES = ['with_stock', 'under_stock', 'good_stock',
                        'over_stock', 'without_stock', 'without_data', 'emergency_stock']
    
    # Dashboard: current stock status
    # Resupply Qts: % with stockout
    # Stock status: all
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    managed = models.PositiveIntegerField(default=0)
    
    with_stock = models.PositiveIntegerField(default=0)
    under_stock = models.PositiveIntegerField(default=0)
    good_stock = models.PositiveIntegerField(default=0)
    over_stock = models.PositiveIntegerField(default=0)
    without_stock = models.PositiveIntegerField(default=0)
    without_data = models.PositiveIntegerField(default=0)
    emergency_stock = models.PositiveIntegerField(default=0)

    # unfortunately, we need to separately keep these for the aggregates
    managed_and_with_stock = models.PositiveIntegerField(default=0)
    managed_and_under_stock = models.PositiveIntegerField(default=0)
    managed_and_good_stock = models.PositiveIntegerField(default=0)
    managed_and_over_stock = models.PositiveIntegerField(default=0)
    managed_and_without_stock = models.PositiveIntegerField(default=0)
    managed_and_without_data = models.PositiveIntegerField(default=0)
    managed_and_emergency_stock = models.PositiveIntegerField(default=0)
    
    def set_managed_attributes(self):
        if self.managed:
            for f in ProductAvailabilityData.STOCK_CATEGORIES:
                setattr(self, 'managed_and_%s' % f, getattr(self, f))
        else: 
            for f in ProductAvailabilityData.STOCK_CATEGORIES:
                setattr(self, 'managed_and_%s' % f, 0)                
                            
class ProductAvailabilityDataSummary(MalawiWarehouseModel):
    """
    Aggregates the product availability up to the supply point level,
    no longer dealing with individual products, but just whether anything
    is managed and anything managed falls into the various categories.
    """
    # Sidebar: % with stockout
    # Dashboard: % with stockout
    # Stock status: district/facility breakdowns
    total = models.PositiveIntegerField(default=0)
    any_managed = models.PositiveIntegerField(default=0)
    any_without_stock = models.PositiveIntegerField(default=0)
    any_with_stock = models.PositiveIntegerField(default=0)
    any_under_stock = models.PositiveIntegerField(default=0)
    any_over_stock = models.PositiveIntegerField(default=0)
    any_good_stock = models.PositiveIntegerField(default=0)
    any_without_data = models.PositiveIntegerField(default=0)
    any_emergency_stock = models.PositiveIntegerField(default=0)

class ReportingRate(MalawiWarehouseModel):
    """
    Records information used to calculate the reporting rates
    """
    # Dashboard: Reporting Rates
    # Reporting Rates: all
    total = models.PositiveIntegerField(default=0)
    reported = models.PositiveIntegerField(default=0)
    on_time = models.PositiveIntegerField(default=0)
    complete = models.PositiveIntegerField(default=0)
    
    @property
    def late(self): 
        return self.reported - self.on_time
    
    @property
    def missing(self): 
        return self.total - self.reported
    
    @property 
    def incomplete(self):
        return self.reported - self.complete
    
    # report helpers
    @property
    def pct_reported(self): return fmt_pct(self.reported, self.total)
    
    @property
    def pct_on_time(self):  return fmt_pct(self.on_time, self.total)
    
    @property
    def pct_late(self):     return fmt_pct(self.late, self.total)
    
    @property
    def pct_missing(self):  return fmt_pct(self.missing, self.total)
    
    @property
    def pct_complete(self): return fmt_pct(self.complete, self.reported)
        


TIME_TRACKER_TYPES = ((TimeTrackerTypes.ORD_READY, 'order - ready'),
                      (TimeTrackerTypes.READY_REC, 'ready - received'))            

class TimeTracker(MalawiWarehouseModel):
    """
    For keeping track of a time between two events. Currently used for 
    lead times. We keep the number of data points around so that we can
    include multiple values into an average.
    """
    # Lead times: all 
    type = models.CharField(max_length=10, choices=TIME_TRACKER_TYPES) 
    total = models.PositiveIntegerField(default=0) # number of contributions to this
    time_in_seconds = models.BigIntegerField(default=0)
    
    @property
    def avg_time_in_days(self):
        if self.total:
            return float(self.time_in_seconds) / float(self.total * 60 * 60 * 24)
        return None

class OrderRequest(MalawiWarehouseModel):
    """
    Each time an order is made, used to count both regular and emergency
    orders for a particular month.
    """
    # Emergency Orders: all
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    emergency = models.PositiveIntegerField(default=0)
    
class OrderFulfillment(MalawiWarehouseModel):
    """
    Each time an order is fulfilled, add up the amount requested and
    the amount received so we can determine order fill rates.
    """
    # Order Fill Rates: all 
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    quantity_requested = models.PositiveIntegerField(default=0)
    quantity_received = models.PositiveIntegerField(default=0)
    
    @property 
    def average_fill_rate(self):
        return pct(self.quantity_received, self.quantity_requested) \
            if self.quantity_requested else None

class UserProfileData(models.Model):
    supply_point = models.ForeignKey('logistics.SupplyPoint')
    facility_children = models.PositiveIntegerField(default=0)
    hsa_children = models.PositiveIntegerField(default=0)
    hsa_supervisors = models.PositiveIntegerField(default=0)
    contacts = models.PositiveIntegerField(default=0)
    supervisor_contacts = models.PositiveIntegerField(default=0)
    in_charge = models.PositiveIntegerField(default=0)
    contact_info = models.CharField(max_length=50, null=True, blank=True)
    products_managed = models.TextField()
    last_message = models.ForeignKey('messagelog.Message', null=True)

    class Meta:
        app_label = "malawi"

class CalculatedConsumption(MalawiWarehouseModel):
    """
    Class for storing calculated consumption data
    """
    product = models.ForeignKey('logistics.Product')
    calculated_consumption = models.PositiveIntegerField(default=0)
    
    # needing data is always either the same as "with data"
    # if the person doesn't manage the product, otherwise it is the period
    # time (seconds in the month, except for the current month)
    time_with_data = models.BigIntegerField(default=0)    # in seconds
    time_needing_data = models.BigIntegerField(default=0) # in seconds
    time_stocked_out = models.BigIntegerField(default=0)  # in seconds
    
    _total = None
    @property
    def total(self):
        if self._total is None:
            # TODO: this should be replaced with the warehouse property
            self._total = hsas_below(self.supply_point.location).count()
        return self._total
    
    @property
    def avg_so_time(self):
        assert self.total
        return float(self.time_stocked_out) / float(self.total) 
    
    @property
    def period_secs(self):
        now = datetime.utcnow()
        end = now if self.date.year == now.year and \
                     self.date.month == now.month \
                  else first_of_next_month(self.date)
        return delta_secs(end - self.date)
        
    @property
    def _so_adjusted_consumption(self):
        # adjusted for stockouts
        adjusted_secs = self.period_secs - self.avg_so_time
        return self.calculated_consumption * (self.period_secs / adjusted_secs)

    @property
    def adjusted_consumption(self):
        # adjusted for stockouts and data
        scale_factor = float(self.time_with_data) / float(self.time_needing_data) \
            if self.time_needing_data != 0 else 0
        return self._so_adjusted_consumption / scale_factor \
                if scale_factor != 0 else self._so_adjusted_consumption 
         
    @property
    def average_adjusted_consumption(self):
        return self.adjusted_consumption / self.total
         
                    
class CurrentConsumption(BaseReportingModel):
    """
    Class for storing actual current consumption data and stock on hand.
    
    This is not a warehouse model because it only stores current data.
    """
    product = models.ForeignKey('logistics.Product')
    total = models.PositiveIntegerField(default=0)
    current_daily_consumption = models.FloatField(default=0) 
    stock_on_hand = models.BigIntegerField(default=0)
    
    @property
    def current_monthly_consumption(self):
        return self.current_daily_consumption * 30
    
    @property
    def months_of_stock(self):
        if self.current_monthly_consumption > 0:
            return self.stock_on_hand / self.current_monthly_consumption
        return None
    
    @property
    def stock_status(self):
        mos = self.months_of_stock
        if mos is None:
            return "No Data"
        elif mos == 0:
            return "Stockout"
        elif mos <= 1:
            return "Under"
        elif mos <= 2:
            return "Adequate"
        else:
            assert mos > 2
            return "Overstocked"
    
    class Meta:
        app_label = "malawi"

            
class Alert(models.Model):
    supply_point = models.ForeignKey('logistics.SupplyPoint')
    num_hsas = models.PositiveIntegerField(default=0)
    have_stockouts = models.PositiveIntegerField(default=0)
    eo_total = models.PositiveIntegerField(default=0)
    eo_with_resupply = models.PositiveIntegerField(default=0)
    eo_without_resupply = models.PositiveIntegerField(default=0)
    total_requests = models.PositiveIntegerField(default=0)
    reporting_receipts = models.PositiveIntegerField(default=0)
    order_readys = models.PositiveIntegerField(default=0)
    without_products_managed = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "malawi"


class HistoricalStock(ReportingModel):
    """
    A simple class to cache historical stock levels by month/year 
    per product/supply point
    """        
    product = models.ForeignKey('logistics.Product')
    stock = models.BigIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    
    class Meta:
        app_label = "malawi"

    