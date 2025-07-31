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

def get_all_subscriptions(stripe, status="active", limit=100):
    """Função para buscar todas as inscrições com paginação"""
    all_subscriptions = []
    has_more = True
    starting_after = None
    params = {
        "limit": limit,
        "status": status
    }
    
    with st.status(f"Buscando páginas no servidor da Stripe, com {params['limit']} itens por página", expanded=True) as status_display:
        print(f"Buscando inscrições com status: {status}")
        st.spinner(text="In progress...",)
        total_paginas = 0

        while has_more:
            total_paginas += 1
            st.write("Buscando página:", total_paginas)

            if starting_after:
                params["starting_after"] = starting_after
                print(f"Paginação iniciada a partir de: {starting_after}")

            response = stripe.Subscription.list(**params)
            data = response['data']
            all_subscriptions.extend(data)

            if response.get("has_more"):
                starting_after = data[-1]["id"]
            else:
                has_more = False
        status_display.update(label="Completo", state="complete", expanded=False)
 
    st.write(f"Total de páginas consultadas: {total_paginas}")
    st.write(f"Total de inscrições encontradas<b>: {len(all_subscriptions)}</b>", unsafe_allow_html=True)
 
    return all_subscriptions


