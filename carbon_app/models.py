from django.db import models

class CompanyConfig(models.Model):
    """Global configuration for the company's sustainability metrics."""
    total_monthly_electricity_bill_kwh = models.FloatField(default=1000.0, help_text="Total office electricity usage in kWh")
    grid_intensity = models.FloatField(default=0.82, help_text="kg CO2 per kWh (India Default: 0.82)")
    # Assuming 'Total Bill' means money, but for emissions we need kWh. Prompt says 'Total Monthly Electricity Bill'. 
    # Usually bills are in cost, but we need kWh for CO2. Let's assume input is kWh directly or we need a cost/kWh factor. 
    # Let's assume input is Total Consumption in kWh for now as it's more direct for carbon.
    
    total_cloud_usage_kwh = models.FloatField(default=500.0, help_text="Total cloud infrastructure usage in kWh")
    server_count = models.IntegerField(default=10, help_text="Number of physical on-premise servers")
    
    def save(self, *args, **kwargs):
        if not self.pk and CompanyConfig.objects.exists():
            return # Ensure singleton
        return super(CompanyConfig, self).save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Global Carbon Settings"

class Employee(models.Model):
    name = models.CharField(max_length=100)
    home_address = models.CharField(max_length=255, default="Home")
    # Simulation: We'll store a pre-calculated distance for Home to Office
    home_commute_distance_km = models.FloatField(default=10.0, help_text="One-way distance from Home to Office")
    
    def __str__(self):
        return self.name

class DailyLog(models.Model):
    # Commute Modes
    EV = 'EV'
    CAR = 'CAR'
    AUTO = 'AUTO'
    BIKE = 'BIKE'
    METRO = 'METRO'
    BUS = 'BUS'
    WFH = 'WFH'
    
    COMMUTE_MODES = [
        (EV, 'Electric Vehicle (0.01 kg/km)'),
        (CAR, 'Car (0.18 kg/km)'),
        (AUTO, 'Auto Rickshaw (0.08 kg/km)'),
        (BIKE, 'Motorbike (0.04 kg/km)'),
        (METRO, 'Metro (0.02 kg/km)'),
        (BUS, 'Bus (0.05 kg/km)'),
        (WFH, 'Work From Home (0.00 kg/km)'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(auto_now_add=True)
    
    # Productivity
    hours_worked = models.FloatField(default=8.0)
    
    # Commute
    is_home_commute = models.BooleanField(default=True, verbose_name="Commuting from Home?")
    start_location = models.CharField(max_length=255, blank=True, null=True, help_text="If not home, where from?")
    commute_mode = models.CharField(max_length=10, choices=COMMUTE_MODES, default=METRO)
    commute_distance_km = models.FloatField(default=0.0, help_text="One-way distance")
    
    # Digital Factory
    vcpu_hours = models.FloatField(default=0.0, help_text="vCPU hours used today")
    storage_gb = models.FloatField(default=0.0, help_text="GB of storage used today")

    @property
    def commute_emissions(self):
        """Returns kg CO2 for the round trip."""
        mode_factors = {
            'EV': 0.01,
            'CAR': 0.18,
            'AUTO': 0.08,
            'BIKE': 0.04,
            'METRO': 0.02,
            'BUS': 0.05,
            'WFH': 0.00,
        }
        factor = mode_factors.get(self.commute_mode, 0.0)
        # Round trip = distance * 2
        return self.commute_distance_km * 2 * factor
    
    @property
    def digital_carbon_footprint(self):
        """
        Estimate based on vCPU and Storage.
        Rough factors (Scientific approx):
        - vCPU: ~0.02 kg CO2 per hour (varies by region, using India grid for now)
        - Storage: ~0.0001 kg CO2 per GB per day
        """
        vcpu_factor = 0.02 
        storage_factor = 0.0001
        return (self.vcpu_hours * vcpu_factor) + (self.storage_gb * storage_factor)

    def save(self, *args, **kwargs):
        # Auto-calculate distance logic simulation
        if self.is_home_commute:
            if self.employee:
                 self.commute_distance_km = self.employee.home_commute_distance_km
        elif self.start_location:
            # Simulate distance: deterministic hash for prototype
            # logic: length of string * 1.5
            if not self.commute_distance_km: # Only auto-calc if not set
                self.commute_distance_km = len(self.start_location) * 1.5 
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"
