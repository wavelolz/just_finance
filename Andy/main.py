# main.py

from fun import FilterMonths, FilterQuarters, CalculateInvestmentReturns
import pandas as pd
from datetime import datetime
from plotly import graph_objs as go
import streamlit as st

# Set the title of the app
st.title("Regular Investment Plan")
# Create three columns with a 1:1:2 ratio
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Design your plan")

    # Add a select box for the stock code at the top
    stock_code = st.selectbox("Select Stock Code:", ["2609", "0050", "0052", "0053", "0054"])
    
    # Select duration type: month, quarter, or year
    duration_type = st.selectbox("Select investment frequency:", ["Month", "Quarter", "Year"])
    
    # Create a text input widget for monthly investment amount
    user_input = st.text_input("Money you invest monthly", value=1000)
    MIA = int(user_input)  # Default to 1000 if no input

    
with col2:
    st.subheader("Select Starting and Ending Date")
    # Load the stock data file based on the selected stock code
    data = pd.read_csv('Andy\s2609.csv')
    data0050 = pd.read_csv('Andy\s0050.csv')
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
        valid_start_months = FilterMonths(start_year, min_date, max_date)
        start_month = st.selectbox("Start Month:", valid_start_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        
        end_year = st.selectbox("End Year:", years, index=len(years) - 1)
        valid_end_months = FilterMonths(end_year, min_date, max_date)
        end_month = st.selectbox("End Month:", valid_end_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        
    elif duration_type == "Quarter":
        start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
        valid_start_quarters = FilterQuarters(start_year, min_date, max_date)
        start_quarter = st.selectbox("Start Quarter:", valid_start_quarters)
        
        end_year = st.selectbox("End Year:", years, index=len(years) - 1)
        valid_end_quarters = FilterQuarters(end_year, min_date, max_date)
        end_quarter = st.selectbox("End Quarter:", valid_end_quarters)
        
        start_month = quarter_month_map[start_quarter][0]
        end_month = quarter_month_map[end_quarter][1]

    elif duration_type == "Year":
        start_year = st.selectbox("Start Year:", years, index=len(years) - 1)
        end_year = st.selectbox("End Year:", years, index=len(years) - 1)
        
        start_month = 1
        end_month = 12

    
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 1) + pd.offsets.MonthEnd(1)
    if start_date <= end_date:
        if end_date < max(data['date']):
            end_date = end_date
        else:
            end_date = max(data['date'])
        # Filter the data based on the selected date range
        filtered_data = data.loc[(data['date'] >= start_date) & (data['date'] <= end_date)].copy()
        filtered_data0050 = data0050.loc[(data0050['date'] >= start_date) & (data0050['date'] <= end_date)].copy()

        duration, start_balance, end_balance, ROI = CalculateInvestmentReturns(filtered_data, duration_type, MIA)
        _, start_balance_0050, end_balance_0050, ROI_0050 = CalculateInvestmentReturns(filtered_data0050, duration_type, MIA)
        
        if duration_type == "Month":
            duration_label = 'Month'
        elif duration_type == "Quarter":
            duration_label = 'Quarter'
        elif duration_type == "Year":
            duration_label = 'Year'

        result = pd.DataFrame({
            duration_label: duration,
            'Start Balance': start_balance,
            'Change': [round(e - s, 2) for s, e in zip(start_balance, end_balance)],
            'End Balance': end_balance,
            'ROI (%)': ROI
        })


with st.container():
    if start_year and start_month and end_year and end_month:
        st.subheader("See what you earn")

        st.write(f"When you have invested a total of {start_balance[-1]} NT dollars over {duration[-1]} months,")
        individual_change = end_balance[-1] - start_balance[-1]
        individual_ratio = ROI[-1]
        etf_change = end_balance_0050[-1] - start_balance_0050[-1]
        etf_ratio = ROI_0050[-1]
        text1 = "Your strategy"
        text2 = "Invest in ETF 0050"

        # Round the numbers to two decimal places
        individual_change = round(individual_change, 2)
        individual_ratio = round(individual_ratio, 2)
        etf_change = round(etf_change, 2)
        etf_ratio = round(etf_ratio, 2)

        # Add the currency symbol and signs for numbers
        display_individual_change = f"+ {individual_change:.2f} NT" if individual_change > 0 else f"- {-individual_change:.2f} NT"
        display_etf_change = f"+ {etf_change:.2f} NT" if etf_change > 0 else f"- {-etf_change:.2f} NT"

        # Add signs for percentages
        display_individual_ratio = f"+ {individual_ratio:.2f}%" if individual_ratio > 0 else f"- {-individual_ratio:.2f}%"
        display_etf_ratio = f"+ {etf_ratio:.2f}%" if etf_ratio > 0 else f"- {-etf_ratio:.2f}%"

        # Create two columns
        col1, col2 = st.columns(2)

        # Display the descriptions in the first row with larger font size
        col1.metric(text1, display_individual_change, display_individual_ratio)
        col2.metric(text2, display_etf_change, display_etf_ratio)

        
        st.write(f"Investment Duration: {start_date.strftime(r'%Y-%m-%d')} to {end_date.strftime(r'%Y-%m-%d')}")
        
        # Initialize the session state if not already done
        if 'show_options' not in st.session_state:
            st.session_state.show_options = False
        # Function to toggle the state
        def toggle_options():
            st.session_state.show_options = not st.session_state.show_options
        st.button("Detail", on_click=toggle_options)
        
        if st.session_state.show_options:
            st.markdown(f'<p style="color:gray; font-style:italic;">The ROI of Stock 0050 is {ROI_0050[-1]} in this duration</p>', unsafe_allow_html=True)

            # Generate alternating colors for each row
            fill_colors = [['lightgray', 'white'] * (len(result) // 2 + 1)][0][:len(result)]

            fig = go.Figure(data=go.Table(
                header=dict(values=list(result[[duration_label, 'Start Balance', 'Change',  'End Balance', 'ROI (%)']].columns),
                            fill_color='white',
                            align='center',
                            line_color='darkslategray',
                            line_width=2,
                            font=dict(size=14, color='black')
                        ),
                cells=dict(values=[result[duration_label], result['Start Balance'], result['Change'], result['End Balance'], result['ROI (%)']],
                        fill_color=[fill_colors],
                        align='center',
                        line_color='darkslategray',
                        line_width=1
                        )
            ))


            # Update layout
            fig.update_layout(
                margin=dict(l=5, r=5, b=10, t=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            

            st.write(fig)
    else:
        st.header("起始日必在終止日前")