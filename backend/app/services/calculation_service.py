import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import json

from app.core.config import settings
from app.models.schemas import CalculationResult, PortfolioCompany, LPAllocation, SessionInfo, CalculationStatus
from app.services.file_service import FileService


class CalculationService:
    """Handle SALT calculations and results management"""
    
    def __init__(self):
        self.file_service = FileService()
        self.results_dir = settings.results_dir
        
        # Mock EY SALT data (in real implementation, this would come from database)
        self.salt_rules = {
            'CA': {'tax_rate': 0.089, 'apportionment_formula': 'single_factor_sales'},
            'TX': {'tax_rate': 0.0, 'apportionment_formula': 'no_tax'},  # No corporate income tax
            'NY': {'tax_rate': 0.063, 'apportionment_formula': 'three_factor'},
            'FL': {'tax_rate': 0.055, 'apportionment_formula': 'single_factor_sales'},
            'IL': {'tax_rate': 0.094, 'apportionment_formula': 'three_factor'},
        }
    
    async def calculate_salt(self, file_path: str, session_id: str) -> CalculationResult:
        """Perform SALT calculation on uploaded portfolio data"""
        try:
            # Read portfolio data
            df = self.file_service.read_portfolio_data(file_path)
            
            # Perform calculations
            portfolio_companies = []
            lp_allocations = {}
            total_salt = 0.0
            
            for _, row in df.iterrows():
                company_name = row['Company Name']
                state = row['State']
                revenue = row['Revenue']
                lp_name = row['LP Name']
                ownership_pct = row['Ownership Percentage'] / 100
                
                # Get SALT rules for state
                salt_rule = self.salt_rules.get(state, {'tax_rate': 0.05, 'apportionment_formula': 'default'})
                
                # Calculate SALT for this company/state
                salt_amount = revenue * salt_rule['tax_rate']
                lp_salt_amount = salt_amount * ownership_pct
                
                # Track portfolio company data
                portfolio_companies.append(PortfolioCompany(
                    name=company_name,
                    state=state,
                    revenue=revenue,
                    tax_allocation={state: salt_amount}
                ))
                
                # Track LP allocations
                if lp_name not in lp_allocations:
                    lp_allocations[lp_name] = {
                        'ownership_percentage': ownership_pct * 100,
                        'salt_allocation': {},
                        'total_allocation': 0
                    }
                
                if state not in lp_allocations[lp_name]['salt_allocation']:
                    lp_allocations[lp_name]['salt_allocation'][state] = 0
                
                lp_allocations[lp_name]['salt_allocation'][state] += lp_salt_amount
                lp_allocations[lp_name]['total_allocation'] += lp_salt_amount
                
                total_salt += lp_salt_amount
            
            # Convert LP allocations to schema format
            lp_allocation_list = [
                LPAllocation(
                    lp_name=lp_name,
                    ownership_percentage=data['ownership_percentage'],
                    salt_allocation=data['salt_allocation'],
                    total_allocation=data['total_allocation']
                )
                for lp_name, data in lp_allocations.items()
            ]
            
            # Create calculation result
            result = CalculationResult(
                session_id=session_id,
                filename=os.path.basename(file_path),
                status=CalculationStatus.COMPLETED,
                portfolio_companies=portfolio_companies,
                lp_allocations=lp_allocation_list,
                total_salt_amount=total_salt,
                calculation_summary={
                    'total_companies': len(portfolio_companies),
                    'total_lps': len(lp_allocation_list),
                    'states_involved': list(set(pc.state for pc in portfolio_companies)),
                    'calculation_date': datetime.now().isoformat()
                },
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            # Save result to file
            await self._save_result(result)
            await self._generate_excel_result(result)
            
            return result
            
        except Exception as e:
            # Create failed result
            result = CalculationResult(
                session_id=session_id,
                filename=os.path.basename(file_path),
                status=CalculationStatus.FAILED,
                portfolio_companies=[],
                lp_allocations=[],
                total_salt_amount=0.0,
                calculation_summary={'error': str(e)},
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            await self._save_result(result)
            raise e
    
    async def get_results(self, session_id: str) -> Optional[CalculationResult]:
        """Get calculation results for a session"""
        try:
            result_file = os.path.join(self.results_dir, f"{session_id}_result.json")
            
            if not os.path.exists(result_file):
                return None
            
            with open(result_file, 'r') as f:
                data = json.load(f)
                return CalculationResult(**data)
                
        except Exception:
            return None
    
    async def get_results_file(self, session_id: str) -> Optional[str]:
        """Get path to Excel results file"""
        excel_file = os.path.join(self.results_dir, f"{session_id}_result.xlsx")
        return excel_file if os.path.exists(excel_file) else None
    
    async def list_sessions(self) -> List[SessionInfo]:
        """List all calculation sessions"""
        sessions = []
        
        if not os.path.exists(self.results_dir):
            return sessions
        
        for filename in os.listdir(self.results_dir):
            if filename.endswith('_result.json'):
                session_id = filename.replace('_result.json', '')
                result = await self.get_results(session_id)
                
                if result:
                    sessions.append(SessionInfo(
                        session_id=result.session_id,
                        filename=result.filename,
                        status=result.status,
                        created_at=result.created_at,
                        completed_at=result.completed_at
                    ))
        
        return sorted(sessions, key=lambda x: x.created_at, reverse=True)
    
    async def _save_result(self, result: CalculationResult) -> None:
        """Save calculation result to JSON file"""
        os.makedirs(self.results_dir, exist_ok=True)
        
        result_file = os.path.join(self.results_dir, f"{result.session_id}_result.json")
        
        with open(result_file, 'w') as f:
            json.dump(result.model_dump(mode='json'), f, indent=2, default=str)
    
    async def _generate_excel_result(self, result: CalculationResult) -> None:
        """Generate Excel file with calculation results"""
        excel_file = os.path.join(self.results_dir, f"{result.session_id}_result.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total SALT Amount', 'Number of Companies', 'Number of LPs', 'States Involved'],
                'Value': [
                    f"${result.total_salt_amount:,.2f}",
                    len(result.portfolio_companies),
                    len(result.lp_allocations),
                    ', '.join(result.calculation_summary.get('states_involved', []))
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # LP Allocations sheet
            lp_data = []
            for lp in result.lp_allocations:
                for state, amount in lp.salt_allocation.items():
                    lp_data.append({
                        'LP Name': lp.lp_name,
                        'State': state,
                        'SALT Amount': amount,
                        'Ownership %': lp.ownership_percentage
                    })
            
            if lp_data:
                pd.DataFrame(lp_data).to_excel(writer, sheet_name='LP Allocations', index=False)
            
            # Portfolio Companies sheet
            company_data = []
            for company in result.portfolio_companies:
                for state, amount in company.tax_allocation.items():
                    company_data.append({
                        'Company Name': company.name,
                        'State': state,
                        'Revenue': company.revenue,
                        'SALT Tax': amount
                    })
            
            if company_data:
                pd.DataFrame(company_data).to_excel(writer, sheet_name='Companies', index=False)