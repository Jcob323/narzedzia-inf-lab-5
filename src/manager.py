from src.models import Apartment, Bill, Parameters, Tenant, Transfer, ApartmentSettlement, TenantSettlement


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True
    
    def get_apartment_costs(self, apartment_key, year=None, month=None):
        if apartment_key not in self.apartments:
            return None
        total_costs = 0.0
        for bill in self.bills:
            if bill.apartment == apartment_key:
                if (year is None or bill.settlement_year == year) and (
                    month is None or bill.settlement_month == month
                ):
                    total_costs += bill.amount_pln

        return total_costs

    def create_apartment_settlement(self, apartment_key, year, month):
        total_bills = self.get_apartment_costs(apartment_key, year, month)
        if total_bills is None:
            return None

        total_rent = 0.0
        total_due = total_rent - total_bills

        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=total_due,
        )

    def _is_tenant_active(self, tenant, year, month):
        period = f"{year}-{month:02d}"
        return tenant.date_agreement_from[:7] <= period <= tenant.date_agreement_to[:7]
    
    def create_tenant_settlements(self, apartment_settlement):
        active_tenants = [tenant for tenant in self.tenants.values() if tenant.apartment == apartment_settlement.apartment and self._is_tenant_active(tenant, apartment_settlement.year, apartment_settlement.month)]

        if not active_tenants:
            return []

        bills_share = apartment_settlement.total_bills_pln / len(active_tenants)
        rent_pln = 0.0
        total_due_pln = rent_pln + bills_share
        balance_pln = 0.0 - total_due_pln

        return [
            TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_settlement.apartment,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                rent_pln=rent_pln,
                bills_pln=bills_share,
                total_due_pln=total_due_pln,
                balance_pln=balance_pln,
            )
            for tenant in active_tenants
        ]