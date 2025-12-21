from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import datetime

# ==========================================
# 1. DATA STRUCTURES (The "Protocol Capture")
# ==========================================

class ApplicationType(Enum):
    PURCHASE = "Purchase"
    REFINANCE = "Refinance"
    SWITCH = "Switch"

@dataclass
class Liability:
    name: str
    monthly_payment: float
    balance: float
    months_remaining: int
    is_being_consolidated: bool = False # Strategy: Strategic Liability Restructuring

@dataclass
class Property:
    address: str
    value: float
    annual_taxes: float
    monthly_heat: float
    remaining_economic_life: int
    is_subject_to_sale: bool = False # Strategy: Conditional Approval Framework

@dataclass
class Applicant:
    applicant_id: str
    name: str
    credit_score: int
    annual_income: float
    liabilities: List[Liability] = field(default_factory=list)

@dataclass
class MortgageApplication:
    app_id: str
    app_type: ApplicationType
    applicant: Applicant
    subject_property: Property
    loan_amount: float
    amortization_years: int
    interest_rate: float
    down_payment: float
    
    # Linkage for Conjunctive Deals
    linked_app_id: Optional[str] = None 

# ==========================================
# 2. THE LOGIC ENGINE (The "Cognitive Compiler" Output)
# ==========================================

class AdjudicationResult:
    def __init__(self, passed: bool, message: str, metrics: Dict):
        self.passed = passed
        self.message = message
        self.metrics = metrics # Audit trail data

class MortgageAdjudicator:
    """
    Deterministic Adjudication Engine based on 'Mortgage Adjudication Agent' rules.
    """
    
    # Decision Thresholds (Configurable Rulebook)
    MAX_TDS = 0.44  # 44%
    MAX_GDS = 0.39  # 39%
    MIN_CREDIT_SCORE = 680
    LTV_HIGH_RATIO_LIMIT = 0.95
    
    def calculate_monthly_mortgage(self, principal, annual_rate, years):
        if years == 0: return 0
        r = annual_rate / 100 / 12
        n = years * 12
        return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

    def _validate_property_data(self, prop: Property) -> List[str]:
        """Check for Missing Expense Identification (Error 1)"""
        warnings = []
        if prop.annual_taxes <= 0:
            warnings.append(f"CRITICAL: Property {prop.address} has $0 taxes. Verify.")
        if prop.monthly_heat <= 0:
            warnings.append(f"CRITICAL: Property {prop.address} has $0 heating cost. Verify.")
        return warnings

    def _check_property_age_compatibility(self, app: MortgageApplication) -> bool:
        """Rule: Property Age Compatibility (High Priority Subgoal)"""
        # Economic life must exceed amortization
        return app.subject_property.remaining_economic_life > app.amortization_years

    def _calculate_ratios(self, app: MortgageApplication, simulate_consolidation: bool = False):
        """
        Calculates GDS/TDS.
        Strategy: Strategic Liability Restructuring (filters out consolidated debts if valid).
        """
        # 1. Mortgage Payment
        p_i = self.calculate_monthly_mortgage(app.loan_amount, app.interest_rate, app.amortization_years)
        
        # 2. Housing Costs (P.I.T.H.)
        taxes_mo = app.subject_property.annual_taxes / 12
        heat_mo = app.subject_property.monthly_heat
        housing_costs = p_i + taxes_mo + heat_mo
        
        # 3. Outside Liabilities
        total_outside_debt = 0
        for debt in app.applicant.liabilities:
            # Logic: Liability Timing and Consolidation
            if simulate_consolidation and debt.is_being_consolidated:
                continue # Skip this debt in calculation
            
            # Logic: Don't count debts expiring very soon (unless specifically flagged)
            if debt.months_remaining < 6 and not debt.is_being_consolidated:
                continue 
                
            total_outside_debt += debt.monthly_payment

        monthly_income = app.applicant.annual_income / 12
        
        gds = housing_costs / monthly_income
        tds = (housing_costs + total_outside_debt) / monthly_income
        
        return gds, tds

    def adjudicate_application(self, app: MortgageApplication, context_apps: List[MortgageApplication] = []) -> AdjudicationResult:
        """
        Main deterministic logic flow.
        """
        audit_log = {}
        
        # 1. Data Integrity Check (Missing Expense Identification)
        data_warnings = self._validate_property_data(app.subject_property)
        if data_warnings:
            return AdjudicationResult(False, f"Data Integrity Fail: {data_warnings}", {})

        # 2. Conjunctive Deal Linkage Check
        linked_deal_note = ""
        if app.linked_app_id:
            # Find the linked app
            linked_app = next((a for a in context_apps if a.app_id == app.linked_app_id), None)
            if not linked_app:
                return AdjudicationResult(False, f"Error: Linked Application {app.linked_app_id} missing from queue.", {})
            linked_deal_note = f"(Linked to {linked_app.app_type.value} Deal {linked_app.app_id})"
            # In a full system, we would cross-verify equity flow here

        # 3. Property Age & Amortization Check
        if not self._check_property_age_compatibility(app):
            return AdjudicationResult(False, f"Decline: Amortization ({app.amortization_years}y) exceeds property economic life ({app.subject_property.remaining_economic_life}y).", {})

        # 4. Standard Calculation (The "Happy Path")
        gds, tds = self._calculate_ratios(app, simulate_consolidation=False)
        audit_log['initial_tds'] = f"{tds:.2%}"
        
        if tds <= self.MAX_TDS:
            return AdjudicationResult(True, f"Approved {linked_deal_note}", {"TDS": tds, "GDS": gds})
        
        # ============================================================
        # STRATEGY: Proactive Scenario Simulation (The "Agentic" Part)
        # ============================================================
        # If standard path fails, the code automatically attempts to restructure
        
        audit_log['simulation_attempted'] = True
        
        # Simulation A: Consolidate Debts marked for consolidation
        sim_gds, sim_tds = self._calculate_ratios(app, simulate_consolidation=True)
        
        if sim_tds <= self.MAX_TDS:
             return AdjudicationResult(
                 True, 
                 f"Conditional Approval: Approved Subject to Debt Consolidation {linked_deal_note}", 
                 {"TDS": sim_tds, "Condition": "Must pay off marked liabilities", "Initial_TDS": tds}
             )

        # Simulation B: Check for High Net Worth / Credit Exception
        if app.applicant.credit_score > 780 and tds < (self.MAX_TDS + 0.04):
             return AdjudicationResult(
                 True, 
                 f"Exception Approval: High Credit Score Exception Applied {linked_deal_note}", 
                 {"TDS": tds, "Score": app.applicant.credit_score}
             )

        return AdjudicationResult(False, "Decline: TDS exceeds limits even after simulation.", {"Final_TDS": sim_tds})

# ==========================================
# 3. EXECUTION DEMO (What runs in the demo)
# ==========================================

# Setup: Expert "Think Aloud" translated into Data
# Scenario: Client is buying a new house but has credit card debt.
# Strategy: Use a "Conjunctive" Refinance on old home to pay off debt + down payment? 
# (Simplifying here to a single purchase with consolidation for brevity)

# Define Liabilities
visa_debt = Liability("Visa Gold", monthly_payment=450, balance=15000, months_remaining=36, is_being_consolidated=True)
car_loan = Liability("Ford Credit", monthly_payment=600, balance=20000, months_remaining=24, is_being_consolidated=False)

# Define Applicant
client = Applicant(
    applicant_id="A101", 
    name="John Doe", 
    credit_score=720, 
    annual_income=110000, 
    liabilities=[visa_debt, car_loan]
)

# Define Property
new_house = Property(
    address="123 Maple Dr", 
    value=600000, 
    annual_taxes=4500, 
    monthly_heat=150, 
    remaining_economic_life=40
)

# Define Application
app_01 = MortgageApplication(
    app_id="APP-001",
    app_type=ApplicationType.PURCHASE,
    applicant=client,
    subject_property=new_house,
    loan_amount=480000,
    amortization_years=25,
    interest_rate=4.99,
    down_payment=120000
)

# Run the Engine
engine = MortgageAdjudicator()
result = engine.adjudicate_application(app_01)

# Output for the "Glass Box" slide
print(f"Decision: {result.message}")
print(f"Audit Trace: {result.metrics}")