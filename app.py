import streamlit as st
import pandas as pd
import numpy as np
import time
import stripe
from utils import get_info_log, get_update_report

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


def get_all_subscriptions(status="active", limit=100):
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

if stripe.api_key:
    try:
 
        subscriptions = get_all_subscriptions(limit=2)
        st.write(subscriptions)
        
        total_subscription = len(subscriptions)
        st.success(f"{total_subscription} inscrições encontradas.")

        total_executions = total_subscription

        limit_exec = st.toggle("Atualizar apenas 3 inscrições")
        if limit_exec:
            total_executions = 3
            st.caption(f"Esta ação irá alterar {total_executions} inscrições ativas para fins de TESTE.")
        else:
            st.caption("Esta ação irá alterar todas as incrições ATIVAS para o novo valor.")
    except Exception as e:
        st.error(f"Erro ao buscar inscrições: {e}")

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

if allow_price_update:
    if st.button("Atualizar preço"):

        progress_increment = int(100 / total_subscription) if total_subscription > 0 else 100
        latest_iteration = st.empty()
        progress_text = "Atualizando preços... Por favor, aguarde."
        progress_value = 0
        progress_bar = st.progress(0, text=progress_text)

        data_log = []
        count = 0

        for subscription in subscriptions:
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
                latest_iteration.text(f"Total atualizado: {count}")

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

        if count > 100:
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
