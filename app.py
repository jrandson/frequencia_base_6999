import streamlit as st
import pandas as pd
import  numpy as np
import time
import stripe
from utils import get_info_log, get_update_report



st.title("Xeque Mate Global - Stripe :chess_pawn:")
st.markdown(
    """ 
    """
)

allow_price_update = False
SECRET_KEY = ""

SECRET_KEY = st.text_input("Stripe Secret Key", placeholder="sk_...")
st.session_state.SECRET_KEY = SECRET_KEY

if 'SECRET_KEY' in st.session_state and st.session_state.SECRET_KEY != "":
    st.success("STRIPE Key registered successfully")
else:
    st.error("STRIPE Key not registered")

stripe.api_key = st.session_state.SECRET_KEY

price_id = st.text_input("Price ID", placeholder="price_...")

if price_id:
    try:
        st.write(f"__Price id__: {price_id}")
        st.session_state.price_id = price_id
        price = stripe.Price.retrieve(price_id)
        st.write(f"__Price value__: R$ {price['unit_amount'] / 100:.2f}")
        allow_price_update = True
    except Exception as error:
        st.error(error)

if 'SECRET_KEY' in st.session_state:
    st.write("Obtendo inscrições...")
    subscriptions = stripe.Subscription.list(
        status="active"  # (active, past_due, canceled, etc.)
    )

    total_subscription = len(subscriptions)
    st.success(f"{total_subscription} inscrições encontradas.")
    
    total_executions = total_subscription

    limit_exec = st.toggle("Atualizar apenas 5 inscrições")
    if limit_exec:    
        total_executions = 5
        st.caption("Esta ação irá alterar 5 inscrições ativas para fins de teste.")
    else:
        st.caption("Esta ação irá alterar todas as incrições ativas para o novo valor definido acima.")
    
if allow_price_update:
    if st.button("Atualizar preço"):

        progress_increment = int(100/total_subscription)
        latest_iteration = st.empty()
        progress_text = "Price update in progress. Please wait."
        progress_value = 0
        progress_bar = st.progress(0, text=progress_text)

        data_log = []

        count = 0
        for subscription in subscriptions:
            sub_id = subscription.id
            si_id = dict(subscription.items())['items']['data'][0].id

            subscription = stripe.Subscription.modify(
                sub_id,
                items=[{
                    'id': si_id,  # The subscription item ID
                    'price': price_id,  # The new price ID
                }],
                proration_behavior="none",  # Options: "create_prorations", "none", "always_invoice"
            )

            progress_value += int(progress_increment)
            progress_bar.progress(progress_value)
            count += 1
            latest_iteration.text(f"Total atualizado: {count}")

            log = get_info_log(stripe, subscription)
            data_log.append(log)

            if count >= total_executions:
                break

        progress_bar.empty()

        if total_subscription == count:
            st.badge("Todas as incrições foram atualizadas", icon=":material/check:", color="green")
        else:
            st.badge(f"Inscrições atualizadas: {count}/{total_subscription}", color="gray")

        df = get_update_report(data_log)
        st.session_state.df = df
        
        if count > 100:
            st.balloons()

if 'df' in st.session_state:

    st.write("Confira no relatório abaixo as incrições atualizadas com o novo valor.")

    st.write(st.session_state.df)

    st.download_button(
        label="Download CSV",
        data=st.session_state.df.to_csv().encode("utf-8"),
        file_name="price-update-report.csv",
        mime="text/csv",
        icon=":material/download:",
    )



