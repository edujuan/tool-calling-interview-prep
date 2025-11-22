"""
Data Analysis Tools
===================

Tool implementations for the data analyst bot.
"""

import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataAnalystTools:
    """Collection of tools for data analysis"""
    
    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
        self.current_file: Optional[str] = None
    
    def get_tool_definitions(self) -> List[Dict]:
        """Return OpenAI function calling tool definitions"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "load_dataset",
                    "description": "Load a dataset from a file (CSV, JSON, or Excel). Must be called before any analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filepath": {
                                "type": "string",
                                "description": "Path to the data file (e.g., 'data/sales.csv')"
                            },
                            "file_type": {
                                "type": "string",
                                "description": "Type of file: 'csv', 'json', or 'excel'. If not specified, inferred from extension.",
                                "enum": ["csv", "json", "excel"]
                            }
                        },
                        "required": ["filepath"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_data_info",
                    "description": "Get detailed information about the loaded dataset including columns, types, missing values, and summary statistics.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_data",
                    "description": "Query or analyze data using various operations like filtering, aggregating, or grouping.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "Type of operation to perform",
                                "enum": ["filter", "aggregate", "groupby", "sort", "top_n"]
                            },
                            "column": {
                                "type": "string",
                                "description": "Column name to operate on"
                            },
                            "operator": {
                                "type": "string",
                                "description": "For filter: comparison operator (==, >, <, >=, <=, !=)",
                                "enum": ["==", ">", "<", ">=", "<=", "!="]
                            },
                            "value": {
                                "description": "Value to compare against (for filter) or function name (for aggregate)"
                            },
                            "group_column": {
                                "type": "string",
                                "description": "Column to group by (for groupby operation)"
                            },
                            "agg_column": {
                                "type": "string",
                                "description": "Column to aggregate (for groupby operation)"
                            },
                            "agg_function": {
                                "type": "string",
                                "description": "Aggregation function",
                                "enum": ["sum", "mean", "count", "min", "max", "median"]
                            },
                            "n": {
                                "type": "integer",
                                "description": "Number of top items to return (for top_n operation)"
                            }
                        },
                        "required": ["operation"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_visualization",
                    "description": "Create a chart or plot from the data. Saves the image to the output/ directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chart_type": {
                                "type": "string",
                                "description": "Type of chart to create",
                                "enum": ["bar", "line", "scatter", "histogram", "pie"]
                            },
                            "x_column": {
                                "type": "string",
                                "description": "Column for X-axis (not needed for histogram/pie)"
                            },
                            "y_column": {
                                "type": "string",
                                "description": "Column for Y-axis (not needed for histogram/pie)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Chart title"
                            },
                            "column": {
                                "type": "string",
                                "description": "Column name (for histogram or pie chart)"
                            }
                        },
                        "required": ["chart_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": "Generate a comprehensive markdown report with dataset overview, statistics, and findings. Saves to output/ directory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "include_sections": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Sections to include in report",
                                "default": ["overview", "statistics", "missing_data", "insights"]
                            }
                        },
                        "required": []
                    }
                }
            }
        ]
    
    def execute(self, tool_name: str, arguments: Dict) -> str:
        """Execute a tool by name"""
        if tool_name == "load_dataset":
            return self.load_dataset(**arguments)
        elif tool_name == "get_data_info":
            return self.get_data_info(**arguments)
        elif tool_name == "query_data":
            return self.query_data(**arguments)
        elif tool_name == "create_visualization":
            return self.create_visualization(**arguments)
        elif tool_name == "generate_report":
            return self.generate_report(**arguments)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    
    def load_dataset(self, filepath: str, file_type: Optional[str] = None) -> str:
        """Load dataset from file"""
        try:
            # Infer file type if not specified
            if file_type is None:
                if filepath.endswith('.csv'):
                    file_type = 'csv'
                elif filepath.endswith('.json'):
                    file_type = 'json'
                elif filepath.endswith(('.xlsx', '.xls')):
                    file_type = 'excel'
                else:
                    return json.dumps({"error": "Could not infer file type. Specify file_type parameter."})
            
            # Load data
            if file_type == 'csv':
                self.current_df = pd.read_csv(filepath)
            elif file_type == 'json':
                self.current_df = pd.read_json(filepath)
            elif file_type == 'excel':
                self.current_df = pd.read_excel(filepath)
            else:
                return json.dumps({"error": f"Unsupported file type: {file_type}"})
            
            self.current_file = filepath
            
            return json.dumps({
                "success": True,
                "filepath": filepath,
                "rows": len(self.current_df),
                "columns": len(self.current_df.columns),
                "column_names": list(self.current_df.columns),
                "preview": self.current_df.head(3).to_dict('records')
            }, default=str)
        
        except FileNotFoundError:
            return json.dumps({"error": f"File not found: {filepath}"})
        except Exception as e:
            return json.dumps({"error": f"Failed to load dataset: {str(e)}"})
    
    def get_data_info(self) -> str:
        """Get dataset information"""
        if self.current_df is None:
            return json.dumps({"error": "No dataset loaded. Use load_dataset first."})
        
        df = self.current_df
        
        info = {
            "shape": {
                "rows": len(df),
                "columns": len(df.columns)
            },
            "columns": {},
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
        }
        
        # Column information
        for col in df.columns:
            info["columns"][col] = {
                "type": str(df[col].dtype),
                "unique_values": int(df[col].nunique()),
                "sample_values": df[col].dropna().head(3).tolist()
            }
        
        # Summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            info["summary_statistics"] = df[numeric_cols].describe().to_dict()
        
        return json.dumps(info, default=str)
    
    def query_data(self, operation: str, **kwargs) -> str:
        """Query/analyze data"""
        if self.current_df is None:
            return json.dumps({"error": "No dataset loaded. Use load_dataset first."})
        
        df = self.current_df
        
        try:
            if operation == "filter":
                column = kwargs.get("column")
                operator = kwargs.get("operator")
                value = kwargs.get("value")
                
                if operator == "==":
                    result = df[df[column] == value]
                elif operator == ">":
                    result = df[df[column] > value]
                elif operator == "<":
                    result = df[df[column] < value]
                elif operator == ">=":
                    result = df[df[column] >= value]
                elif operator == "<=":
                    result = df[df[column] <= value]
                elif operator == "!=":
                    result = df[df[column] != value]
                else:
                    return json.dumps({"error": f"Unknown operator: {operator}"})
                
                return json.dumps({
                    "operation": "filter",
                    "rows_matched": len(result),
                    "data": result.head(20).to_dict('records')
                }, default=str)
            
            elif operation == "aggregate":
                column = kwargs.get("column")
                func = kwargs.get("value")  # Function name
                
                if func == "sum":
                    value = df[column].sum()
                elif func == "mean":
                    value = df[column].mean()
                elif func == "count":
                    value = df[column].count()
                elif func == "min":
                    value = df[column].min()
                elif func == "max":
                    value = df[column].max()
                elif func == "median":
                    value = df[column].median()
                else:
                    return json.dumps({"error": f"Unknown function: {func}"})
                
                return json.dumps({
                    "operation": "aggregate",
                    "column": column,
                    "function": func,
                    "result": value
                }, default=str)
            
            elif operation == "groupby":
                group_col = kwargs.get("group_column")
                agg_col = kwargs.get("agg_column")
                agg_func = kwargs.get("agg_function", "sum")
                
                result = df.groupby(group_col)[agg_col].agg(agg_func)
                
                return json.dumps({
                    "operation": "groupby",
                    "grouped_by": group_col,
                    "aggregated": agg_col,
                    "function": agg_func,
                    "results": result.to_dict()
                }, default=str)
            
            elif operation == "sort":
                column = kwargs.get("column")
                ascending = kwargs.get("value", True)
                
                result = df.sort_values(by=column, ascending=ascending)
                
                return json.dumps({
                    "operation": "sort",
                    "sorted_by": column,
                    "ascending": ascending,
                    "top_10": result.head(10).to_dict('records')
                }, default=str)
            
            elif operation == "top_n":
                column = kwargs.get("column")
                n = kwargs.get("n", 10)
                
                result = df.nlargest(n, column)
                
                return json.dumps({
                    "operation": "top_n",
                    "column": column,
                    "n": n,
                    "results": result.to_dict('records')
                }, default=str)
            
            else:
                return json.dumps({"error": f"Unknown operation: {operation}"})
        
        except KeyError as e:
            return json.dumps({"error": f"Column not found: {str(e)}"})
        except Exception as e:
            return json.dumps({"error": f"Query failed: {str(e)}"})
    
    def create_visualization(self, chart_type: str, **kwargs) -> str:
        """Create visualization"""
        if self.current_df is None:
            return json.dumps({"error": "No dataset loaded. Use load_dataset first."})
        
        df = self.current_df
        
        try:
            plt.figure(figsize=(10, 6))
            plt.style.use('seaborn-v0_8-darkgrid')
            
            if chart_type == "bar":
                x_col = kwargs.get("x_column")
                y_col = kwargs.get("y_column")
                
                # If x is categorical, aggregate first
                if df[x_col].dtype == 'object':
                    data = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
                    data.plot(kind='bar')
                else:
                    df.plot(x=x_col, y=y_col, kind='bar')
                
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.xticks(rotation=45, ha='right')
            
            elif chart_type == "line":
                x_col = kwargs.get("x_column")
                y_col = kwargs.get("y_column")
                
                df.plot(x=x_col, y=y_col, kind='line', marker='o')
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, alpha=0.3)
            
            elif chart_type == "scatter":
                x_col = kwargs.get("x_column")
                y_col = kwargs.get("y_column")
                
                plt.scatter(df[x_col], df[y_col], alpha=0.5)
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, alpha=0.3)
            
            elif chart_type == "histogram":
                col = kwargs.get("column")
                
                df[col].hist(bins=30, edgecolor='black')
                plt.xlabel(col)
                plt.ylabel("Frequency")
                plt.grid(True, alpha=0.3)
            
            elif chart_type == "pie":
                col = kwargs.get("column")
                
                # Aggregate if needed
                if df[col].dtype == 'object':
                    data = df[col].value_counts()
                else:
                    return json.dumps({"error": "Pie charts require categorical column"})
                
                data.plot(kind='pie', autopct='%1.1f%%')
                plt.ylabel('')
            
            else:
                return json.dumps({"error": f"Unknown chart type: {chart_type}"})
            
            # Title
            title = kwargs.get("title", f"{chart_type.title()} Chart")
            plt.title(title, fontsize=14, fontweight='bold')
            
            # Save
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"{output_dir}/{chart_type}_{int(time.time())}.png"
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            return json.dumps({
                "success": True,
                "filepath": filename,
                "chart_type": chart_type
            })
        
        except Exception as e:
            plt.close()
            return json.dumps({"error": f"Visualization failed: {str(e)}"})
    
    def generate_report(self, include_sections: Optional[List[str]] = None) -> str:
        """Generate analysis report"""
        if self.current_df is None:
            return json.dumps({"error": "No dataset loaded. Use load_dataset first."})
        
        if include_sections is None:
            include_sections = ["overview", "statistics", "missing_data", "insights"]
        
        df = self.current_df
        
        try:
            lines = []
            
            # Header
            lines.append("# Data Analysis Report")
            lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Dataset: {self.current_file}\n")
            lines.append("---\n")
            
            # Overview
            if "overview" in include_sections:
                lines.append("## Dataset Overview\n")
                lines.append(f"- **Total Rows:** {len(df):,}")
                lines.append(f"- **Total Columns:** {len(df.columns)}")
                lines.append(f"- **Columns:** {', '.join(df.columns)}")
                lines.append(f"- **Memory Usage:** {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n")
            
            # Statistics
            if "statistics" in include_sections:
                lines.append("## Summary Statistics\n")
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                
                for col in numeric_cols:
                    lines.append(f"### {col}\n")
                    lines.append(f"- **Mean:** {df[col].mean():.2f}")
                    lines.append(f"- **Median:** {df[col].median():.2f}")
                    lines.append(f"- **Std Dev:** {df[col].std():.2f}")
                    lines.append(f"- **Min:** {df[col].min():.2f}")
                    lines.append(f"- **Max:** {df[col].max():.2f}\n")
            
            # Missing data
            if "missing_data" in include_sections:
                missing = df.isnull().sum()
                if missing.sum() > 0:
                    lines.append("## Missing Data\n")
                    for col, count in missing[missing > 0].items():
                        pct = (count / len(df)) * 100
                        lines.append(f"- **{col}:** {count:,} ({pct:.1f}%)")
                    lines.append("")
                else:
                    lines.append("## Missing Data\n")
                    lines.append("✅ No missing values detected.\n")
            
            # Insights
            if "insights" in include_sections:
                lines.append("## Key Insights\n")
                lines.append(f"1. Dataset contains {len(df):,} records across {len(df.columns)} columns")
                
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    lines.append(f"2. {len(numeric_cols)} numeric columns available for analysis")
                
                categorical_cols = df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    lines.append(f"3. {len(categorical_cols)} categorical columns: {', '.join(categorical_cols)}")
                
                lines.append(f"4. Data quality: {(1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100:.1f}% complete")
            
            # Save
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"{output_dir}/report_{int(time.time())}.md"
            with open(filename, 'w') as f:
                f.write('\n'.join(lines))
            
            return json.dumps({
                "success": True,
                "filepath": filename,
                "sections": include_sections
            })
        
        except Exception as e:
            return json.dumps({"error": f"Report generation failed: {str(e)}"})
    
    def clear_data(self):
        """Clear loaded data"""
        self.current_df = None
        self.current_file = None



