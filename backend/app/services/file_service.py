import os
import pandas as pd
from fastapi import UploadFile
import aiofiles
from typing import Optional

from app.core.config import settings


class FileService:
    """Handle file upload, validation, and template generation"""
    
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.results_dir = settings.results_dir
        self.templates_dir = settings.templates_dir
    
    async def save_upload(self, file: UploadFile, session_id: str) -> str:
        """Save uploaded file and return file path"""
        # Create filename with session ID
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{session_id}_{file.filename}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    def validate_excel_format(self, file_path: str) -> dict:
        """Validate Excel file format and return validation results"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Required columns for portfolio data
            required_columns = [
                'Company Name', 
                'State', 
                'Revenue',
                'LP Name',
                'Ownership Percentage'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            validation_result = {
                'valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'row_count': len(df),
                'columns': list(df.columns)
            }
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'missing_columns': [],
                'row_count': 0,
                'columns': []
            }
    
    async def create_template(self, template_path: str) -> None:
        """Create a basic portfolio template Excel file"""
        # Sample data for template
        template_data = {
            'Company Name': ['Acme Corp', 'Beta Industries', 'Gamma Services'],
            'State': ['CA', 'TX', 'NY'],
            'Revenue': [1000000, 750000, 500000],
            'LP Name': ['LP Fund A', 'LP Fund A', 'LP Fund A'],
            'Ownership Percentage': [40, 40, 40]
        }
        
        df = pd.DataFrame(template_data)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        
        # Create Excel file with formatting
        with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Portfolio Data', index=False)
            
            # Get workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets['Portfolio Data']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_name = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 20)
                worksheet.column_dimensions[column_name].width = adjusted_width
    
    def read_portfolio_data(self, file_path: str) -> pd.DataFrame:
        """Read and parse portfolio data from Excel file"""
        try:
            df = pd.read_excel(file_path)
            
            # Basic data cleaning
            df = df.dropna(subset=['Company Name', 'State', 'Revenue'])
            
            # Ensure numeric columns are properly typed
            df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce')
            df['Ownership Percentage'] = pd.to_numeric(df['Ownership Percentage'], errors='coerce')
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading portfolio data: {str(e)}")