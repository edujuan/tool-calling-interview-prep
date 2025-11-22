# Data Analyst Bot - Complete Tutorial

> **Build a production-ready AI data analyst from scratch**

---

## Overview

This is a **complete, end-to-end tutorial** for building an AI-powered data analyst bot that can:

- 📊 Load and analyze datasets (CSV, Excel, JSON)
- 🔍 Answer natural language questions about data
- 📈 Generate visualizations
- 📝 Create summary reports
- 💾 Save analysis results

### What You'll Learn

- ✅ Building a real-world AI agent
- ✅ Tool design and implementation
- ✅ Data analysis with pandas
- ✅ Visualization with matplotlib
- ✅ Error handling and validation
- ✅ Testing and debugging
- ✅ Security best practices

### Prerequisites

- Python 3.8+
- Basic understanding of:
  - Python programming
  - pandas DataFrame basics
  - AI agents (recommended: read [Fundamentals](../../docs/02-fundamentals.md) first)

---

## Architecture

```
┌─────────────────────────────────────────┐
│          Data Analyst Bot               │
│  (OpenAI GPT-4 with function calling)   │
└──────────────┬──────────────────────────┘
               │
               ├─► Tool: load_dataset
               │   • CSV, Excel, JSON support
               │   • Data validation
               │
               ├─► Tool: get_data_info
               │   • Summary statistics
               │   • Column types
               │   • Missing values
               │
               ├─► Tool: query_data
               │   • Filter rows
               │   • Aggregate data
               │   • Sort and group
               │
               ├─► Tool: create_visualization
               │   • Bar charts
               │   • Line plots
               │   • Scatter plots
               │   • Histograms
               │
               └─► Tool: generate_report
                   • Markdown reports
                   • Summary insights
                   • Export results
```

---

## Installation

### Step 1: Set Up Environment

```bash
# Navigate to project directory
cd projects/data-analyst-bot

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# Get your key at: https://platform.openai.com/api-keys
```

### Step 3: Prepare Sample Data

The project includes sample datasets in the `data/` directory:
- `sales_data.csv` - Sample sales transactions
- `customers.json` - Customer information
- `products.xlsx` - Product catalog

---

## Quick Start

### Run the Bot

```bash
python analyst_bot.py
```

### Example Session

```
Data Analyst Bot - Ready!
Available commands:
  - Ask questions about your data
  - Type 'load <file>' to load a dataset
  - Type 'quit' to exit

> load data/sales_data.csv

✓ Loaded sales_data.csv (1,000 rows, 8 columns)

> What are the total sales by product category?

[Analyzing data...]

Here's the breakdown of total sales by product category:

1. Electronics: $245,832
2. Clothing: $198,456
3. Home & Garden: $156,789
4. Sports: $134,567
5. Books: $98,234

Would you like me to create a visualization of this?

> Yes, create a bar chart

[Creating visualization...]

✓ Saved chart to: output/sales_by_category.png

The bar chart shows Electronics as the top-selling category,
followed by Clothing and Home & Garden.

> Generate a summary report

[Generating report...]

✓ Report saved to: output/analysis_report.md

The report includes:
- Dataset overview
- Key findings
- Sales trends
- Recommendations
```

---

## Tutorial: Building the Bot

### Part 1: Core Data Tools

#### Tool 1: Load Dataset

```python
import pandas as pd
import json

def load_dataset(filepath: str, file_type: str = "csv") -> str:
    """
    Load a dataset from file.
    
    Args:
        filepath: Path to data file
        file_type: Type of file (csv, json, excel)
    
    Returns:
        JSON string with load status and data summary
    """
    try:
        if file_type == "csv":
            df = pd.read_csv(filepath)
        elif file_type == "json":
            df = pd.read_json(filepath)
        elif file_type == "excel":
            df = pd.read_excel(filepath)
        else:
            return json.dumps({"error": f"Unsupported file type: {file_type}"})
        
        # Store in global state (or pass around)
        global current_dataframe
        current_dataframe = df
        
        return json.dumps({
            "success": True,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "preview": df.head(3).to_dict('records')
        })
    
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**What it does:**
- Loads CSV, JSON, or Excel files
- Returns summary information
- Provides preview of first 3 rows
- Handles errors gracefully

#### Tool 2: Get Data Info

```python
def get_data_info() -> str:
    """
    Get detailed information about the current dataset.
    
    Returns:
        JSON string with dataset statistics
    """
    if current_dataframe is None:
        return json.dumps({"error": "No dataset loaded"})
    
    df = current_dataframe
    
    info = {
        "shape": {
            "rows": len(df),
            "columns": len(df.columns)
        },
        "columns": {},
        "missing_values": df.isnull().sum().to_dict(),
        "summary_stats": df.describe().to_dict()
    }
    
    # Column type information
    for col in df.columns:
        info["columns"][col] = {
            "type": str(df[col].dtype),
            "unique_values": int(df[col].nunique()),
            "sample_values": df[col].dropna().head(3).tolist()
        }
    
    return json.dumps(info, default=str)
```

**What it does:**
- Provides comprehensive dataset overview
- Shows data types and unique values
- Identifies missing data
- Includes summary statistics

#### Tool 3: Query Data

```python
def query_data(operation: str, **kwargs) -> str:
    """
    Perform data operations.
    
    Args:
        operation: Operation type (filter, aggregate, groupby, sort)
        **kwargs: Operation-specific parameters
    
    Returns:
        JSON string with query results
    """
    if current_dataframe is None:
        return json.dumps({"error": "No dataset loaded"})
    
    df = current_dataframe
    
    try:
        if operation == "filter":
            # Filter rows based on condition
            column = kwargs.get("column")
            operator = kwargs.get("operator")  # ==, >, <, >=, <=, !=
            value = kwargs.get("value")
            
            if operator == "==":
                result = df[df[column] == value]
            elif operator == ">":
                result = df[df[column] > value]
            # ... other operators
            
            return json.dumps({
                "rows": len(result),
                "data": result.head(10).to_dict('records')
            })
        
        elif operation == "aggregate":
            # Aggregate data
            column = kwargs.get("column")
            func = kwargs.get("function")  # sum, mean, count, min, max
            
            if func == "sum":
                value = df[column].sum()
            elif func == "mean":
                value = df[column].mean()
            # ... other functions
            
            return json.dumps({
                "column": column,
                "function": func,
                "result": value
            })
        
        elif operation == "groupby":
            # Group and aggregate
            group_col = kwargs.get("group_column")
            agg_col = kwargs.get("agg_column")
            agg_func = kwargs.get("agg_function", "sum")
            
            result = df.groupby(group_col)[agg_col].agg(agg_func)
            
            return json.dumps({
                "groups": result.to_dict()
            })
        
        else:
            return json.dumps({"error": f"Unknown operation: {operation}"})
    
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**What it does:**
- Filters data based on conditions
- Aggregates data (sum, mean, count, etc.)
- Groups data and applies aggregations
- Handles various data operations

### Part 2: Visualization Tools

#### Tool 4: Create Visualization

```python
import matplotlib.pyplot as plt
import os
import time
import json

def create_visualization(chart_type: str, **kwargs) -> str:
    """
    Create data visualizations.
    
    Args:
        chart_type: Type of chart (bar, line, scatter, histogram)
        **kwargs: Chart-specific parameters
    
    Returns:
        JSON string with file path to saved chart
    """
    if current_dataframe is None:
        return json.dumps({"error": "No dataset loaded"})
    
    df = current_dataframe
    
    try:
        plt.figure(figsize=(10, 6))
        
        if chart_type == "bar":
            x_col = kwargs.get("x_column")
            y_col = kwargs.get("y_column")
            
            # If x_col is categorical, group data
            if df[x_col].dtype == 'object':
                data = df.groupby(x_col)[y_col].sum()
                data.plot(kind='bar')
            else:
                df.plot(x=x_col, y=y_col, kind='bar')
            
            plt.title(kwargs.get("title", "Bar Chart"))
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        
        elif chart_type == "line":
            x_col = kwargs.get("x_column")
            y_col = kwargs.get("y_column")
            
            df.plot(x=x_col, y=y_col, kind='line')
            plt.title(kwargs.get("title", "Line Chart"))
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        
        elif chart_type == "scatter":
            x_col = kwargs.get("x_column")
            y_col = kwargs.get("y_column")
            
            plt.scatter(df[x_col], df[y_col])
            plt.title(kwargs.get("title", "Scatter Plot"))
            plt.xlabel(x_col)
            plt.ylabel(y_col)
        
        elif chart_type == "histogram":
            col = kwargs.get("column")
            bins = kwargs.get("bins", 20)
            
            df[col].hist(bins=bins)
            plt.title(kwargs.get("title", "Histogram"))
            plt.xlabel(col)
            plt.ylabel("Frequency")
        
        else:
            return json.dumps({"error": f"Unknown chart type: {chart_type}"})
        
        # Save chart
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/{chart_type}_{int(time.time())}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return json.dumps({
            "success": True,
            "filepath": filename,
            "chart_type": chart_type
        })
    
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**What it does:**
- Creates various chart types
- Handles categorical and numerical data
- Customizable titles and labels
- Saves charts to output directory

### Part 3: Reporting Tools

#### Tool 5: Generate Report

```python
import json
import os
from datetime import datetime
import numpy as np

def generate_report() -> str:
    """
    Generate a comprehensive analysis report.
    
    Returns:
        JSON string with report filepath
    """
    if current_dataframe is None:
        return json.dumps({"error": "No dataset loaded"})
    
    df = current_dataframe
    
    try:
        report_lines = []
        
        # Header
        report_lines.append("# Data Analysis Report")
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Dataset Overview
        report_lines.append("## Dataset Overview\n")
        report_lines.append(f"- **Rows:** {len(df)}")
        report_lines.append(f"- **Columns:** {len(df.columns)}")
        report_lines.append(f"- **Columns:** {', '.join(df.columns)}\n")
        
        # Summary Statistics
        report_lines.append("## Summary Statistics\n")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            report_lines.append(f"### {col}\n")
            report_lines.append(f"- Mean: {df[col].mean():.2f}")
            report_lines.append(f"- Median: {df[col].median():.2f}")
            report_lines.append(f"- Std Dev: {df[col].std():.2f}")
            report_lines.append(f"- Min: {df[col].min():.2f}")
            report_lines.append(f"- Max: {df[col].max():.2f}\n")
        
        # Missing Data
        missing = df.isnull().sum()
        if missing.sum() > 0:
            report_lines.append("## Missing Data\n")
            for col, count in missing[missing > 0].items():
                pct = (count / len(df)) * 100
                report_lines.append(f"- **{col}:** {count} ({pct:.1f}%)")
            report_lines.append("")
        
        # Key Findings (customize based on your data)
        report_lines.append("## Key Findings\n")
        report_lines.append("1. Dataset loaded successfully")
        report_lines.append(f"2. Total records: {len(df):,}")
        report_lines.append(f"3. Numeric columns: {len(numeric_cols)}")
        
        # Save report
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{output_dir}/report_{int(time.time())}.md"
        with open(filename, 'w') as f:
            f.write('\n'.join(report_lines))
        
        return json.dumps({
            "success": True,
            "filepath": filename,
            "sections": ["Overview", "Statistics", "Findings"]
        })
    
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**What it does:**
- Generates markdown reports
- Includes summary statistics
- Identifies missing data
- Provides key findings
- Saves to output directory

---

## Complete Implementation

See the full implementation in:
- [`analyst_bot.py`](./analyst_bot.py) - Main bot code
- [`tools.py`](./tools.py) - Tool implementations
- [`utils.py`](./utils.py) - Helper functions

---

## Testing Your Bot

### Test 1: Load and Explore

```bash
> load data/sales_data.csv
> Show me the column names and types
> What's the date range of this data?
```

### Test 2: Data Analysis

```bash
> What's the average sale price?
> Which product has the highest sales?
> Show me sales by month
```

### Test 3: Visualization

```bash
> Create a bar chart of sales by category
> Plot sales over time as a line chart
> Show me a histogram of sale amounts
```

### Test 4: Reporting

```bash
> Generate a summary report
> What are the top 5 customers by revenue?
> Create a comprehensive analysis
```

---

## Advanced Features

### 1. Multiple Datasets

Handle multiple datasets simultaneously:

```python
datasets = {}  # Store multiple dataframes

def load_dataset(filepath: str, name: str = "main"):
    """Load dataset with a name"""
    # ... load logic
    datasets[name] = df
```

### 2. Custom Aggregations

Add more complex queries:

```python
def advanced_query(query_type: str, **params):
    """
    Handle complex queries:
    - Correlation analysis
    - Trend detection
    - Outlier identification
    """
```

### 3. Export Options

Add more export formats:

```python
def export_data(format: str, filepath: str):
    """
    Export results in various formats:
    - CSV, Excel, JSON
    - PDF reports
    - Interactive HTML
    """
```

### 4. Caching

Cache expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_aggregation(operation_hash):
    """Cache aggregation results"""
```

---

## Best Practices

### ✅ DO:

1. **Validate Input Data**
   ```python
   if df.empty:
       return {"error": "Dataset is empty"}
   ```

2. **Handle Missing Values**
   ```python
   df = df.fillna(0)  # or dropna()
   ```

3. **Limit Result Sizes**
   ```python
   return result.head(100)  # Don't return millions of rows
   ```

4. **Use Clear Error Messages**
   ```python
   return {"error": f"Column '{col}' not found in dataset"}
   ```

5. **Clean Up Resources**
   ```python
   plt.close()  # Close matplotlib figures
   ```

### ❌ DON'T:

1. **Don't trust user input blindly**
2. **Don't load huge files without limits**
3. **Don't forget to close file handles**
4. **Don't expose sensitive data**
5. **Don't skip error handling**

---

## Troubleshooting

### Issue: "Memory error with large datasets"

**Solution:** Load data in chunks:

```python
chunks = pd.read_csv(filepath, chunksize=10000)
df = pd.concat([chunk for chunk in chunks])
```

### Issue: "Visualization doesn't show data"

**Solution:** Check data types:

```python
df[col] = pd.to_numeric(df[col], errors='coerce')
```

### Issue: "Agent makes wrong tool calls"

**Solution:** Improve tool descriptions:

```python
description = """
Query data using filters.

EXAMPLES:
- Filter sales > 1000: {"operation": "filter", "column": "sales", "operator": ">", "value": 1000}
- Sum revenue: {"operation": "aggregate", "column": "revenue", "function": "sum"}
"""
```

---

## Performance Tips

### 1. Use Appropriate Data Types

```python
# Optimize memory usage
df['category'] = df['category'].astype('category')
df['date'] = pd.to_datetime(df['date'])
```

### 2. Vectorize Operations

```python
# Fast (vectorized)
df['total'] = df['price'] * df['quantity']

# Slow (looping)
df['total'] = df.apply(lambda row: row['price'] * row['quantity'], axis=1)
```

### 3. Use Efficient File Formats

```python
# Parquet is faster than CSV for large datasets
df.to_parquet('data.parquet')
df = pd.read_parquet('data.parquet')
```

---

## Next Steps

### Extend the Bot

1. **Add database support** (SQLite, PostgreSQL)
2. **Implement data cleaning tools**
3. **Add ML predictions** (scikit-learn)
4. **Create interactive dashboards** (Plotly, Streamlit)
5. **Add collaboration features** (share reports)

### Learn More

- [Agent Architectures](../../docs/03-agent-architectures.md)
- [Security Best Practices](../../docs/04-security.md)
- [Multi-Agent Systems](../../docs/05-multi-agent.md)

---

## License

MIT License - See [LICENSE](../../LICENSE) for details.


