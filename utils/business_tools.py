import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BusinessAnalyzer:
    """Analyze business and financial data from uploaded documents"""
    
    def __init__(self):
        self.financial_data = {}
        self.expense_categories = {
            'office': ['office', 'supplies', 'equipment', 'furniture'],
            'travel': ['travel', 'hotel', 'flight', 'transportation', 'uber', 'taxi'],
            'meals': ['restaurant', 'food', 'lunch', 'dinner', 'meal', 'catering'],
            'marketing': ['marketing', 'advertising', 'promotion', 'social media', 'ads'],
            'utilities': ['electricity', 'water', 'gas', 'internet', 'phone', 'utilities'],
            'professional': ['legal', 'accounting', 'consulting', 'professional'],
            'software': ['software', 'subscription', 'saas', 'license', 'app'],
            'miscellaneous': []
        }
    
    def add_document_data(self, file_path: str, doc_data: Dict[str, Any]) -> bool:
        """Add financial data from a processed document"""
        try:
            if doc_data['type'] in ['excel', 'csv']:
                # Try to extract financial data
                df = self._load_dataframe(file_path, doc_data['type'])
                
                if df is not None and not df.empty:
                    # Detect financial columns
                    financial_info = self._detect_financial_columns(df)
                    
                    if financial_info:
                        document_id = doc_data['filename']
                        self.financial_data[document_id] = {
                            'dataframe': df,
                            'financial_columns': financial_info,
                            'upload_date': datetime.now().isoformat(),
                            'type': doc_data['type']
                        }
                        
                        logger.info(f"Added financial data from {document_id}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding document data: {str(e)}")
            return False
    
    def _load_dataframe(self, file_path: str, file_type: str) -> Optional[pd.DataFrame]:
        """Load dataframe from file"""
        try:
            if file_type == 'excel':
                # Try to read the first sheet that has data
                excel_data = pd.read_excel(file_path, sheet_name=None)
                for sheet_name, df in excel_data.items():
                    if not df.empty and len(df.columns) > 1:
                        return df
            elif file_type == 'csv':
                return pd.read_csv(file_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading dataframe from {file_path}: {str(e)}")
            return None
    
    def _detect_financial_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect columns that contain financial data"""
        financial_columns = {
            'amount': [],
            'date': [],
            'description': [],
            'category': []
        }
        
        # Convert column names to lowercase for matching
        columns_lower = [col.lower() for col in df.columns]
        
        # Detect amount columns
        amount_keywords = ['amount', 'cost', 'price', 'total', 'value', 'expense', 'revenue', 'sales']
        for i, col in enumerate(columns_lower):
            if any(keyword in col for keyword in amount_keywords):
                # Check if column contains numeric data
                if pd.api.types.is_numeric_dtype(df.iloc[:, i]):
                    financial_columns['amount'].append(df.columns[i])
        
        # Detect date columns
        date_keywords = ['date', 'time', 'created', 'transaction', 'when']
        for i, col in enumerate(columns_lower):
            if any(keyword in col for keyword in date_keywords):
                financial_columns['date'].append(df.columns[i])
        
        # Detect description columns
        desc_keywords = ['description', 'desc', 'item', 'product', 'service', 'note', 'memo']
        for i, col in enumerate(columns_lower):
            if any(keyword in col for keyword in desc_keywords):
                financial_columns['description'].append(df.columns[i])
        
        # Detect category columns
        cat_keywords = ['category', 'type', 'class', 'group', 'department']
        for i, col in enumerate(columns_lower):
            if any(keyword in col for keyword in cat_keywords):
                financial_columns['category'].append(df.columns[i])
        
        # Remove empty lists
        return {k: v for k, v in financial_columns.items() if v}
    
    def categorize_expenses(self, description: str) -> str:
        """Automatically categorize an expense based on description"""
        description_lower = description.lower()
        
        for category, keywords in self.expense_categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return 'miscellaneous'
    
    def generate_insights(self, query: str = None) -> Dict[str, Any]:
        """Generate business insights from available financial data"""
        try:
            if not self.financial_data:
                return {
                    'message': 'No financial data available. Please upload Excel or CSV files with financial information.',
                    'insights': []
                }
            
            insights = []
            
            for doc_id, data in self.financial_data.items():
                df = data['dataframe']
                financial_cols = data['financial_columns']
                
                # Basic statistics
                doc_insights = {
                    'document': doc_id,
                    'insights': []
                }
                
                # Amount analysis
                if 'amount' in financial_cols:
                    for amount_col in financial_cols['amount']:
                        amounts = df[amount_col].dropna()
                        if len(amounts) > 0:
                            doc_insights['insights'].extend([
                                f"Total {amount_col}: ${amounts.sum():,.2f}",
                                f"Average {amount_col}: ${amounts.mean():.2f}",
                                f"Highest {amount_col}: ${amounts.max():.2f}",
                                f"Lowest {amount_col}: ${amounts.min():.2f}",
                                f"Number of transactions: {len(amounts)}"
                            ])
                
                # Time-based analysis
                if 'date' in financial_cols and 'amount' in financial_cols:
                    try:
                        date_col = financial_cols['date'][0]
                        amount_col = financial_cols['amount'][0]
                        
                        df_time = df[[date_col, amount_col]].copy()
                        df_time[date_col] = pd.to_datetime(df_time[date_col], errors='coerce')
                        df_time = df_time.dropna()
                        
                        if len(df_time) > 1:
                            df_time = df_time.sort_values(date_col)
                            
                            # Monthly trends
                            monthly = df_time.groupby(df_time[date_col].dt.to_period('M'))[amount_col].sum()
                            if len(monthly) > 1:
                                trend = "increasing" if monthly.iloc[-1] > monthly.iloc[0] else "decreasing"
                                doc_insights['insights'].append(f"Monthly trend: {trend}")
                    
                    except Exception as e:
                        logger.warning(f"Error in time analysis: {str(e)}")
                
                # Category analysis
                if 'description' in financial_cols and 'amount' in financial_cols:
                    try:
                        desc_col = financial_cols['description'][0]
                        amount_col = financial_cols['amount'][0]
                        
                        # Auto-categorize expenses
                        categories = df[desc_col].apply(self.categorize_expenses)
                        category_totals = df.groupby(categories)[amount_col].sum().sort_values(ascending=False)
                        
                        doc_insights['insights'].append("Top expense categories:")
                        for cat, total in category_totals.head(5).items():
                            doc_insights['insights'].append(f"  • {cat.title()}: ${total:,.2f}")
                    
                    except Exception as e:
                        logger.warning(f"Error in category analysis: {str(e)}")
                
                insights.append(doc_insights)
            
            return {
                'message': f"Analysis complete for {len(self.financial_data)} financial documents",
                'insights': insights,
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {
                'error': str(e),
                'message': 'Error generating business insights'
            }
    
    def get_insights_context(self) -> str:
        """Get a summary of business insights for chat context"""
        try:
            if not self.financial_data:
                return ""
            
            context_parts = []
            
            for doc_id, data in self.financial_data.items():
                df = data['dataframe']
                financial_cols = data['financial_columns']
                
                if 'amount' in financial_cols:
                    amount_col = financial_cols['amount'][0]
                    amounts = df[amount_col].dropna()
                    
                    context_parts.append(
                        f"Financial data from {doc_id}: "
                        f"${amounts.sum():,.2f} total, "
                        f"{len(amounts)} transactions, "
                        f"avg ${amounts.mean():.2f}"
                    )
            
            return "Business Context: " + "; ".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting insights context: {str(e)}")
            return ""
    
    def generate_forecast(self, document_id: str, periods: int = 12) -> Dict[str, Any]:
        """Generate simple forecast based on historical data"""
        try:
            if document_id not in self.financial_data:
                return {'error': 'Document not found'}
            
            data = self.financial_data[document_id]
            df = data['dataframe']
            financial_cols = data['financial_columns']
            
            if 'date' not in financial_cols or 'amount' not in financial_cols:
                return {'error': 'Date and amount columns required for forecasting'}
            
            date_col = financial_cols['date'][0]
            amount_col = financial_cols['amount'][0]
            
            # Prepare time series data
            df_forecast = df[[date_col, amount_col]].copy()
            df_forecast[date_col] = pd.to_datetime(df_forecast[date_col], errors='coerce')
            df_forecast = df_forecast.dropna().sort_values(date_col)
            
            if len(df_forecast) < 3:
                return {'error': 'Insufficient data for forecasting (need at least 3 data points)'}
            
            # Simple linear trend forecast
            df_forecast['period'] = range(len(df_forecast))
            
            # Calculate trend
            x = df_forecast['period'].values
            y = df_forecast[amount_col].values
            
            # Linear regression
            slope = np.polyfit(x, y, 1)[0]
            intercept = np.polyfit(x, y, 1)[1]
            
            # Generate forecast
            last_period = len(df_forecast) - 1
            forecast_periods = range(last_period + 1, last_period + 1 + periods)
            forecast_values = [slope * p + intercept for p in forecast_periods]
            
            # Calculate confidence based on historical variance
            historical_variance = np.var(y)
            confidence_interval = np.sqrt(historical_variance) * 1.96  # 95% confidence
            
            return {
                'forecast_values': forecast_values,
                'periods': periods,
                'trend': 'increasing' if slope > 0 else 'decreasing',
                'slope': slope,
                'confidence_interval': confidence_interval,
                'r_squared': np.corrcoef(x, y)[0, 1] ** 2 if len(x) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about business data"""
        try:
            return {
                'documents_loaded': len(self.financial_data),
                'document_types': [data['type'] for data in self.financial_data.values()],
                'total_records': sum(
                    len(data['dataframe']) 
                    for data in self.financial_data.values()
                ),
                'categories_available': list(self.expense_categories.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting business stats: {str(e)}")
            return {}
    
    def export_analysis(self, format: str = 'json') -> str:
        """Export business analysis results"""
        try:
            insights = self.generate_insights()
            
            if format == 'json':
                return json.dumps(insights, indent=2)
            elif format == 'text':
                text_output = []
                for doc_insight in insights.get('insights', []):
                    text_output.append(f"\n{doc_insight['document']}:")
                    for insight in doc_insight['insights']:
                        text_output.append(f"  {insight}")
                return '\n'.join(text_output)
            else:
                return "Unsupported format. Use 'json' or 'text'."
                
        except Exception as e:
            logger.error(f"Error exporting analysis: {str(e)}")
            return f"Error: {str(e)}"
