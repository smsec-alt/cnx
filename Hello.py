import streamlit as st
from gcs import GCS
from can_char import Canada_Processed


st.set_page_config(page_title="Grain Statistics Weekly", layout='wide',)

with st.sidebar:
    add_grain = st.selectbox("Select Commodity", ['Wheat', 'Barley', 'Corn', 'Oat', 'Rye','Canola', 'Soybeans','Amber Durum'])   
    add_item = st.selectbox("Select Variable", ['Domestic', 'Producer Deliveries', 'Exports', 'Producer Shipments'])   

def main():
    gcs = GCS('sm_data_bucket', streamlit=True)
    df = gcs.read_csv('canada/weekly_report.csv')
    can = Canada_Processed(df, add_grain, add_item)

    st.markdown("""### Summary""")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Week", "{:.2f}".format(can.current_week_value), "{:.2f}%".format(can.wow_value))
    col2.metric("To Date", "{:.2f}".format(can.to_date_value), "{:.2f}%".format(can.yoy_value))
    col3.metric("Week ago", "{:.2f}".format(can.last_week_value))
    col4.metric("Year ago", "{:.2f}".format(can.last_year_value))

    st.markdown("""### Charts""")
    st.plotly_chart(can.plot_grain_item())
    st.plotly_chart(can.plot_monthly_item())
    st.plotly_chart(can.plot_weekly_item())


if __name__ == '__main__':
    main()