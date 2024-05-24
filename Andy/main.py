# main.py

from fun import filter_months, filter_quarters, calculate_investment_returns
import streamlit as st
import pandas as pd
from datetime import datetime
from plotly import graph_objs as go

# Set the title of the app
st.title("Regular Investment Plan Simulation")
st.subheader("Select Monthly Investment Account")

# Create a text input widget for monthly investment amount
user_input = st.text_input("Money you invest monthly", value=1000)
MIA = int(user_input)  # Default to 1000 if no input

# Add a select box for the stock code at the top
stock_code = st.selectbox("Select Stock Code:", ["2609", "0050", "0052", "0053", "0054"])

# Select duration type: month, quarter, or year
duration_type = st.selectbox("Select Duration Type:", ["Month", "Quarter", "Year"])

st.subheader("Select Starting and Ending Date")
# Load the stock data file based on the selected stock code
data = pd.read_csv(f'just_finance/Andy/s{stock_code}.csv')
data0050 = pd.read_csv(f'just_finance/Andy/s0050.csv')
data['date'] = pd.to_datetime(data['date'])
data0050['date'] = pd.to_datetime(data0050['date'])

# Extract month, quarter, and year
data['month'] = data['date'].dt.month
data['year'] = data['date'].dt.year
data['quarter'] = data['date'].dt.to_period('Q')
data0050['month'] = data0050['date'].dt.month
data0050['year'] = data0050['date'].dt.year
data0050['quarter'] = data0050['date'].dt.to_period('Q')

# Quarter Dictionary
quarter_month_map = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12)
}

# Find the max and min dates in the file
min_date = data['date'].min()
max_date = data['date'].max()

# Get the years range based on the min and max dates
years = list(range(min_date.year, max_date.year + 1))

if duration_type == "Month":
    start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
    valid_start_months = filter_months(start_year, min_date, max_date)
    start_month = st.selectbox("Start Month:", valid_start_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
    
    end_year = st.selectbox("End Year:", years, index=len(years) - 1)
    valid_end_months = filter_months(end_year, min_date, max_date)
    end_month = st.selectbox("End Month:", valid_end_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
    
elif duration_type == "Quarter":
    start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
    valid_start_quarters = filter_quarters(start_year, min_date, max_date)
    start_quarter = st.selectbox("Start Quarter:", valid_start_quarters)
    
    end_year = st.selectbox("End Year:", years, index=len(years) - 1)
    valid_end_quarters = filter_quarters(end_year, min_date, max_date)
    end_quarter = st.selectbox("End Quarter:", valid_end_quarters)
    
    start_month = quarter_month_map[start_quarter][0]
    end_month = quarter_month_map[end_quarter][1]

elif duration_type == "Year":
    start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
    end_year = st.selectbox("End Year:", years, index=len(years) - 1)
    
    start_month = 1
    end_month = 12

if start_year and start_month and end_year and end_month:
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1) + pd.offsets.MonthEnd(1)
    if end_date in data['date'].values:
        end_date = end_date
    else:
        end_date = max(data['date'])
    # Filter the data based on the selected date range
    filtered_data = data.loc[(data['date'] >= start_date) & (data['date'] <= end_date)].copy()
    filtered_data0050 = data0050.loc[(data0050['date'] >= start_date) & (data0050['date'] <= end_date)].copy()

    duration, cost, revenue, ROI = calculate_investment_returns(filtered_data, duration_type, MIA)
    _, _, _, ROI0050 = calculate_investment_returns(filtered_data0050, duration_type, MIA)
    
    if duration_type == "Month":
        duration_label = 'Duration (Months)'
    elif duration_type == "Quarter":
        duration_label = 'Duration (Quarters)'
    elif duration_type == "Year":
        duration_label = 'Duration (Years)'

    result = pd.DataFrame({
        duration_label: duration,
        'Cost': cost,
        'Revenue': revenue,
        'Return on Investment (%)': ROI
    })
    
    st.subheader("Investment Summary Table")
    st.write(f"Investment Duration: {start_date.strftime(r'%Y-%m-%d')} to {end_date.strftime(r'%Y-%m-%d')}")
    st.markdown(f'<p style="color:gray; font-style:italic;">The ROI of Stock 0050 is {ROI0050[-1]} in this duration</p>', unsafe_allow_html=True)
    
    fig = go.Figure(data=go.Table(
        header=dict(values=list(result[[duration_label, 'Cost', 'Revenue', 'Return on Investment (%)']].columns),
                    fill_color='#FDBE72',
                    align='center'),
        cells=dict(values=[result[duration_label], result['Cost'], result['Revenue'], result['Return on Investment (%)']],
                   fill_color='#E5ECF6',
                   align='left'))
    )

    fig.update_layout(margin=dict(l=5, r=5, b=10, t=10),
                      paper_bgcolor='white')

    st.write(fig)
    
else:
    st.write("No data available for the selected date range.")
