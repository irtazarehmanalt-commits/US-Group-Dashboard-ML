import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

MONTH_NAMES = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
               7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

def prepare_chart_data(df: pd.DataFrame):
    """Returns (category_labels, value_col_name, value_series, chart_type)"""

    cols_lower = [c.lower() for c in df.columns]
    has_year = 'year' in cols_lower
    has_month = 'month' in cols_lower

    # Case 1: Year + Month present -> build a proper chronological "Mon YYYY" label
    if has_year and has_month:
        year_col = df.columns[cols_lower.index('year')]
        month_col = df.columns[cols_lower.index('month')]

        df = df.sort_values([year_col, month_col]).reset_index(drop=True)
        labels = [f"{MONTH_NAMES.get(int(m), m)} {int(y)}" for y, m in zip(df[year_col], df[month_col])]

        remaining_numeric = [c for c in df.select_dtypes(include='number').columns 
                              if c not in (year_col, month_col)]
        if not remaining_numeric:
            return None
        value_col = remaining_numeric[0]

        return labels, value_col, df[value_col], 'line'

    # Case 2: a text/category column exists alongside a numeric value
    text_cols = df.select_dtypes(exclude='number').columns.tolist()
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    if text_cols and numeric_cols:
        category_col = text_cols[0]
        value_col = numeric_cols[0]
        return df[category_col].astype(str).tolist(), value_col, df[value_col], (
            'pie' if len(df) <= 6 else 'bar'
        )

    # Case 3: two numeric columns, no text -> assume first is category-like 
    # (e.g. Unit number), second is the value, only if first has more unique 
    # values than the row count suggests otherwise
    if len(numeric_cols) >= 2:
        category_col, value_col = numeric_cols[0], numeric_cols[1]
        return df[category_col].astype(str).tolist(), value_col, df[value_col], 'bar'

    return None


def generate_chart(rows: list) -> str:
    df = pd.DataFrame(rows)
    if df.empty:
        return None

    result = prepare_chart_data(df)
    if result is None:
        return None

    labels, value_col, values, chart_type = result

    plt.figure(figsize=(8, 5))

    if chart_type == 'line':
        plt.plot(labels, values, marker='o')
        plt.xticks(rotation=30, ha='right')
        plt.ylabel(value_col)
    elif chart_type == 'bar':
        plt.bar(labels, values)
        plt.xticks(rotation=30, ha='right')
        plt.ylabel(value_col)
    elif chart_type == 'pie':
        plt.pie(values, labels=labels, autopct='%1.1f%%')

    plt.title(f"{value_col} over time" if chart_type == 'line' else f"{value_col} by category")
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    plt.close()
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8')