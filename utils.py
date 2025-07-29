import pandas as pd
import streamlit as st

def get_info_log(stripe, subscription):
    def get_customer_info(cus_id):
        customer = stripe.Customer.retrieve(cus_id)

        cus_cols = ['name', 'email', 'phone']
        customer = {col: customer[col] for col in cus_cols}

        return customer

    customer = get_customer_info(subscription.customer)

    log = {'subscription_id': subscription.id,
           'amount': subscription['items']['data'][0]['plan']['amount'] / 100,
           'currency': subscription['items']['data'][0]['plan']['currency'],
           **customer}

    return pd.Series(log)

@st.cache_data
def get_update_report(data_log):
    df = pd.concat(data_log, axis=1).T

    return df


