import streamlit as st
import pandas as pd
import numpy as np
import time
import stripe
from utils import get_info_log, get_update_report, get_all_subscriptions

st.title("Xeque Mate Global - Stripe :chess_pawn:")
st.markdown(""" """)

allow_price_update = False
SECRET_KEY = ""

SECRET_KEY = st.text_input("Stripe Secret Key", placeholder="sk_...")
st.session_state.SECRET_KEY = SECRET_KEY

if 'SECRET_KEY' in st.session_state and st.session_state.SECRET_KEY != "":
    st.success("STRIPE Key registered successfully")
else:
    st.error("STRIPE Key not registered")

stripe.api_key = st.session_state.SECRET_KEY

if not 'subscriptions' in st.session_state:
    st.session_state.subscriptions = []

if st.button("Carregar isncrições ativas"):
    try:
        st.session_state.subscriptions = get_all_subscriptions(stripe)

    except Exception as e:
        st.error(f"Erro ao buscar inscrições: {e}")

total_subscription = len(st.session_state.subscriptions)
total_executions = total_subscription
if total_subscription > 0:
    st.success(f"{total_subscription} inscrições encontradas.")

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

limit_exec = st.toggle("Atualizar apenas 3 inscrições")
if limit_exec:
    total_executions = 3
    st.caption(f"Esta ação irá alterar {total_executions} inscrições ativas para fins de TESTE.")
else:
    st.caption("Esta ação irá alterar todas as incrições ATIVAS para o novo valor.")

if allow_price_update:
    if st.button("Atualizar preço"):

        progress_increment = int(100 / total_subscription) if total_subscription > 0 else 100
        latest_iteration = st.empty()
        progress_text = "Atualizando preços... Por favor, aguarde."
        progress_value = 0
        progress_bar = st.progress(0, text=progress_text)

        data_log = []
        count = 0

        for subscription in st.session_state.subscriptions:
            sub_id = subscription.id
            si_id = dict(subscription.items())['items']['data'][0].id

            try:
                subscription = stripe.Subscription.modify(
                    sub_id,
                    items=[{
                        'id': si_id,
                        'price': price_id,
                    }],
                    proration_behavior="none",
                )

                log = get_info_log(stripe, subscription)
                data_log.append(log)

                count += 1
                progress_value += int(progress_increment)
                progress_bar.progress(min(progress_value, 100))
                # latest_iteration.text(f"Total atualizado: {count}")

            except Exception as e:
                st.warning(f"Erro ao atualizar inscrição {sub_id}: {e}")

            if count >= total_executions:
                break

        progress_bar.empty()

        if total_subscription == count:
            st.success("Todas as inscrições foram atualizadas com sucesso.")
        else:
            st.info(f"Inscrições atualizadas: {count}/{total_subscription}")

        df = get_update_report(data_log)
        st.session_state.df = df

        if count == total_subscription:
            st.balloons()

if 'df' in st.session_state:
    st.write("Confira no relatório abaixo as incrições atualizadas com o novo valor.")
    st.write(st.session_state.df)

    st.download_button(
        label="Download CSV",
        data=st.session_state.df.to_csv(index=False).encode("utf-8"),
        file_name="price-update-report.csv",
        mime="text/csv",
        icon=":material/download:",
    )
