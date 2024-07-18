# Standard library imports
import os
from datetime import datetime, timedelta, date

# Third-party library imports
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import polib
import extra_streamlit_components as stx
import uuid
from PIL import Image
import io


# Custom module imports
from etl_process import FetchDatasetList, FetchData, FetchChineseName, CleanData, ExtractMarketCloseDate
from random_stock_select import MonkeySelectStock
from regular_investment_plan import FilterMonths, FilterQuarters, CalculateInvestmentReturns, FormatChange, FormatRatio, FormatNumber
from user_behavior_tracker import save_user_session, save_tab_click_counter


st.set_page_config(layout="wide")
pio.templates.default = "plotly_dark"

KEY_PATH = {
    "type": st.secrets["firebase"]["type"],
    "project_id": st.secrets["firebase"]["project_id"],
    "private_key_id": st.secrets["firebase"]["private_key_id"],
    "private_key": st.secrets["firebase"]["private_key"],
    "client_email": st.secrets["firebase"]["client_email"],
    "client_id": st.secrets["firebase"]["client_id"],
    "auth_uri": st.secrets["firebase"]["auth_uri"],
    "token_uri": st.secrets["firebase"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
    "universe_domain": st.secrets["firebase"]["universe_domain"]
}

# initialize the structure
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

# Initialize the click counts in session state
if 'tab1' not in st.session_state:
    st.session_state['tab1'] = 0
if 'tab2' not in st.session_state:
    st.session_state['tab2'] = 0
if 'tab3' not in st.session_state:
    st.session_state['tab3'] = 0

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 1

# Save the current user session
save_user_session(st.session_state['user_id'], KEY_PATH)



# Used for the data frame in random stock selection experiment
CSS = """
<style>
    table {
        width: 100%;
        table-layout: fixed;
        word-wrap: break-word;
    }
    th, td {
        padding: 10px;
        text-align: left;
    }
</style>
"""


def create_excel(df):
    dfc = df.copy()
    dfc.columns = ["date", "min", "max", "open", "close"]
    dfc = dfc[["date", "open", "close", "min", "max"]]
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        dfc.to_excel(writer, sheet_name='Sheet1', index=False)
    buffer.seek(0)
    return buffer

def filter_date(data, code):
    """
    Filter stock data based within specific date range
    
    Args:
        data (dataframe): The data frame of stock data.
        code (int): The code indicating the date range of data to filter.
    
    Returns:
        dataframe: The filtered stock data or the original data if the the date range indicates
        all available dates
    """
    code_day_map = {
        0: 30,
        1: 90,
        2: 150,
        3: 365,
        4: 1825
    }
    if code in code_day_map:
        return data[-code_day_map[code]:]
    
    return data


def get_valid_end_year():
    """
    Get the valid end year for date range available.
    
    Returns:
        tuple: A tuple containing the valid year.
    """
    year = date.today().year
    year -= 1
    return year

def progress_callback(step, total_steps):
    progress_percentage = int(step / total_steps * 100)
    progress_bar.progress(progress_percentage)


def modify_detail_df(stocks_group, profit_ratios_group, dates, _t=None):
    """
    Format detailed stock data for display.
    
    Args:
        stock_groups (list): List of lists containing stock symbols.
        profit_ratio_groups (list): List of lists containing profit ratios for each stock.
        dates (list): List of dates for the date intervals.
    
    Returns:
        pd.DataFrame: DataFrame containing formatted stock details with execution periods.
    """

    # Create date intervals for the data frame
    date_intervals = [
        f"{dates[i][:4]}~{dates[i+1][:4]}" 
        for i in range(len(dates)-1)
        ]

    # Create formatted information for each stock
    formatted_infos = []
    for stocks, profits in zip(stocks_group, profit_ratios_group):
        info_list = [
            f"{stock.split('-')[0]} (+{profit}%)" if profit > 0 else f"{stock.split('-')[0]} (-{str(profit)[1:]}%)"
            for stock, profit in zip(stocks, profits)
        ]
        formatted_infos.append(info_list)

    info_df = pd.DataFrame(formatted_infos)

    # Set column names for stocks
    info_df.columns = [_t("Stock-")+str(i+1) for i in range(len(stocks_group[0]))]

    # Add date intervals as a new column
    info_df[_t("Portfolio Holding Period")] = date_intervals

    # Reorder columns to place "執行期間" at the front
    columns = [_t("Portfolio Holding Period")] + [_t("Stock-")+str(i+1) for i in range(len(stocks_group[0]))]
    info_df = info_df[columns]

    return info_df

# Define a function to determine the color based on the value
def get_color(value):
    return "red" if value > 0 else "green"

# Define a function to format the value with a "+" sign if positive
def format_value(value):
    return f"+{value}%" if value > 0 else str(value)+"%"


def get_translation(language):
    localedir = os.path.join(os.path.dirname(__file__), 'translations')
    po_file = os.path.join(localedir, language, 'messages.po')
    po = polib.pofile(po_file)
    translations = {entry.msgid: entry.msgstr for entry in po}
    return translations


st.sidebar.markdown(f"<p style='font-size: 24px'>Stockaroo</p>", unsafe_allow_html=True)


image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logo.png")
image = Image.open(image_path)
st.sidebar.image(image, width=150)

st.sidebar.markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)
# Define the available languages
languages = { '繁體中文': 'zh_TW', 'English': 'en'}

# Create a selectbox for language selection
selected_language = st.sidebar.selectbox('Select Language', options=list(languages.keys()))
st.sidebar.markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)
# Load the translation function based on the selected language
translations = get_translation(languages[selected_language])
_t = lambda s: translations.get(s, s)

linked_text = _t("Tutorial")
st.sidebar.markdown(f'<a href="https://hackmd.io/@wavelolz005/By3CCPZvC" style="font-size:20px;">{linked_text}</a>', unsafe_allow_html=True)



# tab_graph, tab_dollar_cost_averaging, tab_random_strategy = st.tabs([_t("Stock Trend"), _t("Regular Investment Plan"), _t("Random Stock Selection Plan")])

# Define the tab bar
chosen_id = stx.tab_bar(data=[
    stx.TabBarItemData(id=1, title=_t("Stock Trend"), description=_t("Stock Market Journal")),
    stx.TabBarItemData(id=2, title=_t("Regular Investment Plan"), description=_t("Patience is the Key")),
    stx.TabBarItemData(id=3, title=_t("Random Stock Selection Plan"), description=_t("Surprise from Randomness")),
], default=1)

# Update the click count based on the chosen tab
if st.session_state['active_tab'] != int(chosen_id):
    chosen_id_int = int(chosen_id)
    st.session_state['active_tab'] = chosen_id_int
    if chosen_id_int == 1:
        st.session_state['tab1'] += 1
        save_tab_click_counter(st.session_state['user_id'], "tab1_click_count", st.session_state['tab1'], KEY_PATH)
    elif chosen_id_int == 2:
        st.session_state['tab2'] += 1
        save_tab_click_counter(st.session_state['user_id'], "tab2_click_count", st.session_state['tab2'], KEY_PATH)
    elif chosen_id_int == 3:
        st.session_state['tab3'] += 1
        save_tab_click_counter(st.session_state['user_id'], "tab3_click_count", st.session_state['tab3'], KEY_PATH)

        
if chosen_id == "1":
    # Fetch the list of stock IDs
    stock_df = FetchChineseName(KEY_PATH)
    stock_list = [stock_df.iloc[i]["id"]+"-"+stock_df.iloc[i]["n"] for i in range(len(stock_df))]

    # Select a stock from the list
    selected_stock = st.selectbox(_t("Stock List"), stock_list, key="G1")
    selected_stock = str("s" + selected_stock.split("-")[0])

    # Fetch and clean data for the selected stock
    raw_data = FetchData("stock", selected_stock, KEY_PATH)
    cleaned_data = CleanData(raw_data)
    market_close_dates = ExtractMarketCloseDate(cleaned_data)
    
    # Map the duration to filter codes
    duration_map = {
        _t("1M"): 0,
        _t("3M"): 1,
        _t("5M"): 2,
        _t("1Y"): 3,
        _t("5Y"): 4,
        _t("All"): 5
    }

    # Select the duration for plotting
    selected_duration = st.radio(
        _t("Please select the length of the date"),
        list(duration_map.keys()),
        horizontal=True
    )

    # Filter data based on the selected duration
    filter_code = duration_map[selected_duration]
    filtered_data = filter_date(cleaned_data, filter_code)

    excel_file = create_excel(filtered_data)

    st.markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)
    st.download_button(
        label=_t("Download Data"),
        data=excel_file,
        file_name=f"{selected_stock[1:]}_{selected_duration}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Create the line plot
    line_plot = go.Scatter(
        x=filtered_data["date"],
        y=filtered_data["c"],
        mode="lines"
    )
    fig = go.Figure()
    fig.add_trace(line_plot)

    # Update the x-axis to exclude market close dates
    fig.update_xaxes(rangebreaks=[dict(values=market_close_dates)])

    fig.update_layout(
        title = dict(
            text=_t('Stock Trend'),
            font=dict(
                size=20,
                family="Arial Black"
            ),
            x=0.5,
            xanchor="center"
        ),

        xaxis = dict(
            title=dict(
                text=_t("Date"),
                font=dict(
                    size=16,
                    family="Arial"
                )
            ),
            tickfont=dict(
                size=12,
                family="Arial Black"
            ),
        ),

        yaxis = dict(
            title=dict(
                text=_t("Price"),
                font=dict(
                    size=16,
                    family="Arial"
                )
            ),
            tickfont=dict(
                size=12,
                family="Arial Black"
            ),
        ),
    )


    # Display the plot
    st.plotly_chart(fig, use_container_width=True)

if chosen_id == "2":

    # Create three columns with a 1:1:2 ratio
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(_t("Please select investment frequency and amount"))

        # Fetch the list of stock IDs
        stock_df = FetchChineseName(KEY_PATH)
        stock_list = [stock_df.iloc[i]["id"]+"-"+stock_df.iloc[i]["n"] for i in range(len(stock_df))]

        # Select a stock from the list
        selected_stock_label = st.selectbox(_t("Please select stock to be invested"), stock_list, key="RIP1")
        selected_stock = str("s" + selected_stock_label.split("-")[0])

        # Select duration type: month, quarter, or year
        duration_type = st.selectbox(_t("Investment Frequency"), [_t("Month"), _t("Quarter"), _t("Year")])
        
        # Create a text input widget for monthly investment amount
        user_input = st.text_input(_t("Please input money invested each time"), value=1000)
        MIA = int(user_input)  # Default to 1000 if no input

        
    with col2:
        

        st.subheader(_t("Please select time range"))
        # Load the stock data file based on the selected stock code
        data = FetchData("stock", selected_stock, KEY_PATH)
        data = CleanData(data)
        data0050 = FetchData("stock", "s0050", KEY_PATH)
        data0050 = CleanData(data0050)
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

        if duration_type == "Month" or duration_type == "月":
            start_year = st.selectbox(_t("Start Year"), years, index=len(years) - 1)
            valid_start_months = FilterMonths(start_year, min_date, max_date)
            start_month = st.selectbox(_t("Start Month"), valid_start_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
            
            end_year = st.selectbox(_t("End Year"), years, index=len(years) - 1)
            valid_end_months = FilterMonths(end_year, min_date, max_date)
            end_month = st.selectbox(_t("End Month"), valid_end_months, format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
            
        elif duration_type == "Quarter" or duration_type == "季":
            start_year = st.selectbox(_t("Start Year"), years, index=len(years) - 1)
            valid_start_quarters = FilterQuarters(start_year, min_date, max_date)
            start_quarter = st.selectbox(_t("Start Quarter"), valid_start_quarters)
            
            end_year = st.selectbox(_t("End Year"), years, index=len(years) - 1)
            valid_end_quarters = FilterQuarters(end_year, min_date, max_date)
            end_quarter = st.selectbox(_t("End Quarter"), valid_end_quarters)
            
            start_month = quarter_month_map[start_quarter][0]
            end_month = quarter_month_map[end_quarter][1]

        elif duration_type == "Year" or duration_type == "年":
            start_year = st.selectbox(_t("Start Year"), years, index=len(years) - 1)
            end_year = st.selectbox(_t("End Year"), years, index=len(years) - 1)
            
            start_month = 1
            end_month = 12

        
        start_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 1) + pd.offsets.MonthEnd(1)

    with st.container():
        
        if st.button(_t("Start"), key="RIP2"):
            if not (end_date > start_date):
                st.header(_t("Invalid Input: End date needs to go after start date"))
            elif MIA <= 0:
                st.header(_t("Invalid Input: Amount needs to be greater than 0"))
            else:

                if end_date < max(data['date']):
                    end_date = end_date
                else:
                    end_date = max(data['date'])
                # Filter the data based on the selected date range
                filtered_data = data.loc[(data['date'] >= start_date) & (data['date'] <= end_date)].copy()
                filtered_data0050 = data0050.loc[(data0050['date'] >= start_date) & (data0050['date'] <= end_date)].copy()

                duration, start_balance, end_balance, ROI = CalculateInvestmentReturns(filtered_data, duration_type, MIA)
                _, start_balance_0050, end_balance_0050, ROI_0050 = CalculateInvestmentReturns(filtered_data0050, duration_type, MIA)
                
                if duration_type == "Month" or duration_type == "月":
                    duration_label = 'Month'
                elif duration_type == "Quarter" or duration_type == "季":
                    duration_label = 'Quarter'
                elif duration_type == "Year" or duration_type == "年":
                    duration_label = 'Year'

                result = pd.DataFrame({
                    duration_label: duration,
                    'Start Balance': start_balance,
                    'Change': [round(e - s, 2) for s, e in zip(start_balance, end_balance)],
                    'End Balance': end_balance,
                    'ROI (%)': ROI
                })

                st.subheader(_t("Backtesting Result"))
                st.markdown(f"<p style='font-size: 24px;'>{_t('Investment Period: ')}{start_date.strftime(r'%Y-%m-%d')}~{end_date.strftime(r'%Y-%m-%d')}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 24px'>{_t('Total Cost: ')}{start_balance[-1]}</p>", unsafe_allow_html=True)
                individual_change = end_balance[-1] - start_balance[-1]
                individual_ratio = ROI[-1]
                etf_change = end_balance_0050[-1] - start_balance_0050[-1]
                etf_ratio = ROI_0050[-1]
                stock_label = selected_stock_label
                text1 = f"{stock_label}"
                text2 = f"0050-元大台灣50"

                # Round the numbers to two decimal places
                individual_change = round(individual_change, 2)
                individual_ratio = round(individual_ratio, 2)
                etf_change = round(etf_change, 2)
                etf_ratio = round(etf_ratio, 2)

                # Formatted display strings
                display_individual_change = FormatChange(individual_change)
                display_etf_change = FormatChange(etf_change)
                display_individual_ratio = FormatRatio(individual_ratio)
                display_etf_ratio = FormatRatio(etf_ratio)
                # Create two columns
                col1, col2 = st.columns(2)

                # Display the descriptions in the first row with larger font size
                col1.metric(text1, display_individual_change, display_individual_ratio)
                col2.metric(text2, display_etf_change, display_etf_ratio)

                # Generate alternating colors for each row
                fill_colors = [['lightgray', 'white'] * (len(result) // 2 + 1)][0][:len(result)]

                fig = go.Figure(data=go.Table(
                    header=dict(values=[_t(name) for name in list(result[[duration_label, 'Start Balance', 'Change',  'End Balance', 'ROI (%)']].columns)],
                                fill_color='white',
                                align='center',
                                line_color='darkslategray',
                                line_width=2,
                                font=dict(size=14, color="black")
                            ),
                    cells=dict(values=[result[duration_label], result['Start Balance'], result['Change'], result['End Balance'], result['ROI (%)']],
                            fill_color=[fill_colors],
                            align='center',
                            line_color='darkslategray',
                            line_width=1,
                            font=dict(size=14, color="black")
                            )
                ))


                # Update layout
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )

                st.plotly_chart(fig, use_container_width=True)

            
if chosen_id == "3":
    col1, col2 = st.columns([1, 1])
    # Set list of year available    

    with col1:

        st.subheader(_t("Please select time range and number of stocks to be sampled"))
        valid_year = get_valid_end_year()
        years = list(np.arange(2018, valid_year+1))

        # Select start year
        start_year = st.selectbox(_t("Start Year"), years, key="RSS3")
        start_date = f"{start_year}-01"

        # Select end year
        end_year = st.selectbox(_t("End Year"), years, index=1, key="RSS4")
        end_date = f"{end_year+1}-01"

        # Select number of stocks 
        num_stock = st.selectbox(_t("Number of stocks"), [i+1 for i in range(5)])

    with col2:

        st.subheader(_t("Please select an industry"))
        # Select stock category
        options = [_t("All"), _t("ETF"), _t("Finance and Insurance"), 
                _t("Electrical Machinery"), _t("Electronics Industry"), 
                _t("Telecommunication and Network Industry"), _t("Semiconductor Industry"), 
                _t("Computer and Peripheral Equipment Industry"), _t("Automotive Industry"),
                _t("Electronic Components Industry"), _t("Glass and Ceramics"), _t("ETN"),
                _t("Digital Cloud"), _t("Biotechnology and Medical Care"), _t("Building Materials and Construction"),
                _t("Rubber Industry"), _t("Other Electronics"), _t("Beneficiary Securities"),
                _t("Steel Industry"), _t("Food Industry"), _t("Green Energy and Environmental Protection"),
                _t("Depositary Receipts"), _t("Innovative Board Stocks"), _t("Oil, Electricity, and Gas Industry"),
                _t("Cement Industry"), _t("Optoelectronics Industry"), _t("Agricultural Technology"), 
                _t("Cultural and Creative Industry"), _t("Tourism Industry"), _t("Others"), _t("Shipping Industry"),
                _t("Paper Industry"), _t("Tourism and Hospitality"), _t("Textile and Fiber"), _t("Electrical Appliances and Cables"),
                _t("Electrical Machinery"), _t("Home and Living"), _t("Trading and Department Stores"), _t("Electronic Distribution Industry"),
                _t("Information Service Industry"), _t("Chemical Industry"), _t("Plastics Industry")]
        choice = st.selectbox(_t("The program will sample stocks from selected industry only"), options)

    with st.container():
        progress_bar = st.progress(0)
        if st.button(_t("Start"), key="RSSP1"):
            if end_year <= start_year:
                st.header(_t("Invalid Input: End date needs to go after start date"))
            else:
                new_balances, new_balances_0050, dates, profit_ratios_group, stocks_group = MonkeySelectStock(
                    start_date, end_date, num_stock, choice, 1000, KEY_PATH, progress_callback, invest_interval=_t("Year"), 
                )


                difference = np.round((np.array(new_balances)-np.array(new_balances_0050))/np.array(new_balances_0050)*100)
                df_plot = pd.DataFrame({
                    "change_of_portfolio" : [np.round((new_balances[i+1]-new_balances[0])/new_balances[0]*100, 2) for i in range(len(new_balances)-1)],
                    "change_of_0050" : [np.round((new_balances_0050[i+1]-new_balances_0050[0])/new_balances_0050[0]*100, 2) for i in range(len(new_balances_0050)-1)],
                    "date" : dates[1:]
                })
                

                # Plot the balance over time
                fig = go.Figure(data=[
                    go.Bar(
                        x=df_plot['date'],
                        y=df_plot['change_of_portfolio'],
                        marker_color="#FFA117",
                        name=_t("Random Stock Selection Plan")
                    ),
                    go.Bar(
                        x=df_plot['date'],
                        y=df_plot['change_of_0050'],
                        marker_color="#6BC2FF",
                        name="0050"
                    )
                ])

                stack_y_value = list(df_plot["change_of_portfolio"])+list(df_plot["change_of_0050"])

                yaxis = np.linspace(min(stack_y_value), max(stack_y_value)+10, 8)
                yaxis = [int(np.round(i)) for i in yaxis]
                # Customize the layout
                fig.update_layout(
                    title = dict(
                        text=_t('ROI of Random Stock Selection Plan and 0050 (by year)'),
                        font=dict(
                            size=20,
                            family="Arial Black"
                        ),
                        x=0.5,
                        xanchor="center"
                    ),

                    legend = dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    ),

                    xaxis = dict(
                        title=dict(
                            text=_t("Date"),
                            font=dict(
                                size=16,
                                family="Arial"
                            )
                        ),
                        tickfont=dict(
                            size=12,
                            family="Arial Black"
                        ),
                        tickmode="array",
                        tickvals=df_plot["date"],
                        ticktext=[f"{dates[i][:4]}~{dates[i+1][:4]}" for i in range(len(dates)-1)]
                    ),

                    yaxis = dict(
                        title=dict(
                            text=_t("ROI"),
                            font=dict(
                                size=16,
                                family="Arial"
                            )
                        ),
                        tickfont=dict(
                            size=12,
                            family="Arial Black"
                        ),
                        tickmode="array",
                        tickvals=yaxis,
                        ticktext=[str(i)+"%" for i in yaxis]
                    ),
                    bargap=0.5
                )

                st.plotly_chart(fig, use_container_width=True)


                # Provide summary statistics
                profit_ratio_random = np.round((new_balances[-1]-1000)/1000*100, 2)
                profit_ratio_0050 = np.round((new_balances_0050[-1]-1000)/1000*100, 2)
                profit_ratio_difference = np.round(profit_ratio_random-profit_ratio_0050, 2)
                

                html_code = f"""
                <style>
                .container {{
                    display: flex;
                    justify-content: space-around;  /* Use space-around to center the metrics */
                    margin-bottom: 20px;
                }}

                .metric {{
                    text-align: center;
                    position: relative;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    min-width: 350px; /* Set a minimum width to ensure space between metrics */
                }}

                .metric::after {{
                    content: '';
                    position: absolute;
                    right: -10px; /* Adjust the position to be just outside the padding */
                    top: 10%; /* Adjust this value to center the line vertically */
                    height: 80%; /* Adjust this value to change the line height */
                    border-right: 1px solid #e0e0e0;
                }}

                .metric:last-child::after {{
                    content: none;
                }}

                .metric-title {{
                    font-size: 16px;
                    white-space: nowrap; /* Prevents breaking into multiple lines */
                }}

                .metric-value {{
                    font-size: 32px;
                    font-weight: bold;
                }}
                </style>

                <div class="container">
                    <div class="metric">
                        <div class="metric-title">{_t("Return Rate of Random Stock Selection Plan")}</div>
                        <div class="metric-value" style="color: {get_color(profit_ratio_random)};">{format_value(profit_ratio_random)}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-title">{_t("Return Rate of 0050")}</div>
                        <div class="metric-value" style="color: {get_color(profit_ratio_0050)};">{format_value(profit_ratio_0050)}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-title">{_t("Comparison with 0050")}</div>
                        <div class="metric-value" style="color: {get_color(profit_ratio_difference)};">{format_value(profit_ratio_difference)}</div>
                    </div>
                </div>
                """

                st.markdown(html_code, unsafe_allow_html=True)

                # Display stock portfolio
                stock_df = FetchChineseName(KEY_PATH)
                for i in range(len(stocks_group)):
                    for j in range(len(stocks_group[i])):
                        stocks_group[i][j] = stocks_group[i][j] + "-" + stock_df.loc[stock_df["id"]==stocks_group[i][j]]["n"].values[0]
                date_intervals = [
                    f"{dates[i][:4]}~{dates[i+1][:4]}" 
                    for i in range(len(dates)-1)
                ]


                st.markdown(
                    f"""
                    <h1 style='text-align: center; font-family: "Arial Black"; font-size: 20px;'>
                    {_t("The following shows the stocks selected")}
                    </h1>
                    """,
                    unsafe_allow_html=True
                )
                cols = st.columns(len(date_intervals))

                for i in range(len(date_intervals)):
                    cols[i].markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True) 
                    cols[i].markdown('<div class="custom-container">', unsafe_allow_html=True)
                    cols[i].markdown(f'<div class="custom-column"><h3 style="margin-top: -10px; margin-bottom: 0px;">⭐ {date_intervals[i]}</h3></div>', unsafe_allow_html=True)
                    for stock in stocks_group[i]:
                        cols[i].markdown(f'<div class="custom-column"><h6 style="margin-top: 0px; margin-bottom: 0px; padding-left: 5px">{stock}</h6></div>', unsafe_allow_html=True)
                    cols[i].markdown('</div>', unsafe_allow_html=True)
                    cols[i].markdown("<hr style='margin-top: 0px; margin-bottom: 0px;'>", unsafe_allow_html=True)  # Add a horizontal line with shorter spacing
                    i += 1
                
                # Displayed detailed information
                df_detail_info = modify_detail_df(stocks_group, profit_ratios_group, dates, _t)
                fill_colors = [['lightgray', 'white'] * (len(df_detail_info) // 2 + 1)][0][:len(df_detail_info)]
                fig = go.Figure(data=go.Table(
                    header=dict(
                        values=df_detail_info.columns,
                        fill_color='white',
                        align='center',
                        line_color='darkslategray',
                        line_width=2,
                        font=dict(size=14, color="black")
                    ),
                    cells=dict(
                        values=[df_detail_info.iloc[:, i] for i in range(len(df_detail_info.columns))],
                        fill_color=[fill_colors],
                        align='center',
                        line_color='darkslategray',
                        line_width=1,
                        font=dict(size=14, color="black")
                    )
                ))

                fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        title = dict(
                        text=_t("This table shows the ROI of each stock"),
                        font=dict(
                            size=20,
                            family="Arial Black"
                        ),
                        x=0.5,
                        xanchor="center")
                    )

                st.plotly_chart(fig, use_container_width=True)
                