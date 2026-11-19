import io
import os
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fralda & Lenço — Planilha de Controle",
    page_icon="🧷",
    layout="wide",
)

DATA_FILE = "controle_fraldas_lencos.csv"
MOVEMENTS = ["Entrada", "Saída", "Ajuste"]
CATEGORIES = ["Fralda", "Lenço Umedecido"]

SEED_DATA = [
    {"Data": date(2026, 10, 18), "Movimento": "Entrada", "Categoria": "Fralda", "Marca": "Pampers Confort Sec", "Tamanho/Tipo": "M", "Pacotes": 2.0, "Un./Pacote": 70, "Valor (R$)": 169.80, "Observações": "Promoção pacote mega na farmácia"},
    {"Data": date(2026, 10, 20), "Movimento": "Entrada", "Categoria": "Lenço Umedecido", "Marca": "Huggies Pureza", "Tamanho/Tipo": "96 un.", "Pacotes": 4.0, "Un./Pacote": 96, "Valor (R$)": 47.60, "Observações": "Kit com 4 pacotes sem fragrância"},
    {"Data": date(2026, 10, 26), "Movimento": "Saída", "Categoria": "Fralda", "Marca": "Pampers Confort Sec", "Tamanho/Tipo": "M", "Pacotes": 1.0, "Un./Pacote": 70, "Valor (R$)": 0.0, "Observações": "Pacote aberto e finalizado"},
    {"Data": date(2026, 11, 2), "Movimento": "Entrada", "Categoria": "Fralda", "Marca": "Huggies Supreme Care", "Tamanho/Tipo": "M", "Pacotes": 1.0, "Un./Pacote": 64, "Valor (R$)": 82.90, "Observações": "Uso noturno"},
    {"Data": date(2026, 11, 5), "Movimento": "Saída", "Categoria": "Lenço Umedecido", "Marca": "Huggies Pureza", "Tamanho/Tipo": "96 un.", "Pacotes": 2.0, "Un./Pacote": 96, "Valor (R$)": 0.0, "Observações": "Uso trocador + bolsa passeio"},
    {"Data": date(2026, 11, 9), "Movimento": "Entrada", "Categoria": "Fralda", "Marca": "MamyPoko Calça", "Tamanho/Tipo": "G", "Pacotes": 2.0, "Un./Pacote": 52, "Valor (R$)": 135.80, "Observações": "Reserva para próxima fase"},
    {"Data": date(2026, 11, 12), "Movimento": "Saída", "Categoria": "Fralda", "Marca": "Pampers Confort Sec", "Tamanho/Tipo": "M", "Pacotes": 1.0, "Un./Pacote": 42, "Valor (R$)": 0.0, "Observações": "Consumo da semana"},
    {"Data": date(2026, 11, 15), "Movimento": "Entrada", "Categoria": "Lenço Umedecido", "Marca": "Johnson's Recém-Nascido", "Tamanho/Tipo": "48 un.", "Pacotes": 3.0, "Un./Pacote": 48, "Valor (R$)": 38.70, "Observações": "Pacotes compactos para bolsa"},
    {"Data": date(2026, 11, 17), "Movimento": "Saída", "Categoria": "Lenço Umedecido", "Marca": "Huggies Pureza", "Tamanho/Tipo": "96 un.", "Pacotes": 1.0, "Un./Pacote": 96, "Valor (R$)": 0.0, "Observações": "Pacote finalizado no quarto"},
]

BASE_COLS = ["Data", "Movimento", "Categoria", "Marca", "Tamanho/Tipo", "Pacotes", "Un./Pacote", "Valor (R$)", "Observações"]


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in BASE_COLS:
        if c not in out.columns:
            out[c] = "" if c in ["Marca", "Tamanho/Tipo", "Observações"] else 0
    out = out[BASE_COLS].copy()
    out["Data"] = pd.to_datetime(out["Data"], errors="coerce").dt.date.fillna(date.today())
    out["Movimento"] = out["Movimento"].where(out["Movimento"].isin(MOVEMENTS), "Entrada")
    out["Categoria"] = out["Categoria"].where(out["Categoria"].isin(CATEGORIES), "Fralda")
    out["Marca"] = out["Marca"].fillna("").astype(str)
    out["Tamanho/Tipo"] = out["Tamanho/Tipo"].fillna("M").astype(str)
    out["Pacotes"] = pd.to_numeric(out["Pacotes"], errors="coerce").fillna(1.0).astype(float)
    out["Un./Pacote"] = pd.to_numeric(out["Un./Pacote"], errors="coerce").fillna(60).clip(lower=1).astype(int)
    out["Valor (R$)"] = pd.to_numeric(out["Valor (R$)"], errors="coerce").fillna(0.0).clip(lower=0.0).astype(float)
    out["Observações"] = out["Observações"].fillna("").astype(str)
    return out.reset_index(drop=True)


def compute_metrics_df(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_df(df)
    raw_units = (out["Pacotes"] * out["Un./Pacote"]).round().astype(int)
    out["Total Unid."] = raw_units
    out.loc[out["Movimento"] == "Entrada", "Total Unid."] = raw_units.abs()
    out.loc[out["Movimento"] == "Saída", "Total Unid."] = -raw_units.abs()

    out["Valor (R$)"] = out.apply(
        lambda r: float(r["Valor (R$)"]) if r["Movimento"] == "Entrada" else 0.0, axis=1
    )
    out["Custo / Un. (R$)"] = out.apply(
        lambda r: (r["Valor (R$)"] / abs(r["Total Unid."]))
        if r["Movimento"] == "Entrada" and r["Valor (R$)"] > 0 and abs(r["Total Unid."]) > 0
        else None,
        axis=1,
    )
    return out


def save_data(df: pd.DataFrame) -> None:
    normalize_df(df).to_csv(DATA_FILE, sep=";", index=False, encoding="utf-8-sig")


def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        try:
            loaded = pd.read_csv(DATA_FILE, sep=";", encoding="utf-8-sig")
            return normalize_df(loaded)
        except Exception:
            pass
    df = normalize_df(pd.DataFrame(SEED_DATA))
    save_data(df)
    return df


if "df" not in st.session_state:
    st.session_state.df = load_data()

if "last_upload_key" not in st.session_state:
    st.session_state.last_upload_key = None

# Barra lateral
with st.sidebar:
    st.title("Fralda & Lenço")
    st.caption("Controle de estoque e custos")

    st.subheader("Alertas de estoque mínimo")
    min_diapers = st.number_input("Fraldas (un.)", min_value=0, value=50, step=5)
    min_wipes = st.number_input("Lenços (un.)", min_value=0, value=100, step=10)

    st.divider()
    st.subheader("Importar / Exportar CSV")
    uploaded = st.file_uploader("Importar CSV (separador ; ou ,)", type=["csv"])
    if uploaded is not None:
        upload_key = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.last_upload_key != upload_key:
            raw_text = uploaded.read().decode("utf-8-sig", errors="replace")
            lines = raw_text.splitlines()
            sep = ";" if lines and ";" in lines[0] else ","
            imported_df = pd.read_csv(io.StringIO(raw_text), sep=sep)
            st.session_state.df = pd.concat([normalize_df(imported_df), st.session_state.df], ignore_index=True)
            st.session_state.last_upload_key = upload_key
            save_data(st.session_state.df)
            st.success(f"{len(imported_df)} linhas importadas!")

    csv_export = normalize_df(st.session_state.df).to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="Exportar planilha CSV",
        data=csv_export,
        file_name=f"controle-fraldas-lencos-{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("Restaurar exemplo", use_container_width=True):
            st.session_state.df = normalize_df(pd.DataFrame(SEED_DATA))
            save_data(st.session_state.df)
            st.rerun()
    with col_r2:
        if st.button("Limpar tudo", use_container_width=True):
            st.session_state.df = normalize_df(pd.DataFrame(columns=BASE_COLS))
            save_data(st.session_state.df)
            st.rerun()

# Cálculos principais
full_df = compute_metrics_df(st.session_state.df)
diaper_df = full_df[full_df["Categoria"] == "Fralda"]
wipe_df = full_df[full_df["Categoria"] == "Lenço Umedecido"]

diaper_stock = int(diaper_df["Total Unid."].sum())
wipe_stock = int(wipe_df["Total Unid."].sum())
total_spent = float(full_df.loc[full_df["Movimento"] == "Entrada", "Valor (R$)"].sum())

if not full_df.empty:
    latest_ym = pd.to_datetime(full_df["Data"]).dt.to_period("M").max()
    month_spent = float(
        full_df.loc[
            (full_df["Movimento"] == "Entrada")
            & (pd.to_datetime(full_df["Data"]).dt.to_period("M") == latest_ym),
            "Valor (R$)",
        ].sum()
    )
else:
    month_spent = 0.0

diaper_priced = diaper_df[(diaper_df["Movimento"] == "Entrada") & (diaper_df["Valor (R$)"] > 0)]
wipe_priced = wipe_df[(wipe_df["Movimento"] == "Entrada") & (wipe_df["Valor (R$)"] > 0)]
avg_diaper_cost = (diaper_priced["Valor (R$)"].sum() / diaper_priced["Total Unid."].sum()) if diaper_priced["Total Unid."].sum() > 0 else None
avg_wipe_cost = (wipe_priced["Valor (R$)"].sum() / wipe_priced["Total Unid."].sum()) if wipe_priced["Total Unid."].sum() > 0 else None


def stock_badge(val: int, threshold: int) -> str:
    if val <= 0:
        return "Sem estoque"
    if val < threshold:
        return "Estoque baixo"
    return "Estoque normal"


# Indicadores
st.header("Controle de Fraldas e Lenço Umedecido")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Fraldas em estoque", f"{diaper_stock} un.", stock_badge(diaper_stock, min_diapers))
k2.metric("Lenços umedecidos", f"{wipe_stock} un.", stock_badge(wipe_stock, min_wipes))
k3.metric("Gasto no último mês", format_brl(month_spent), f"Total: {format_brl(total_spent)}")
k4.metric(
    "Custo médio / unid.",
    f"Fralda {format_brl(avg_diaper_cost)}" if avg_diaper_cost else "Fralda —",
    f"Lenço {format_brl(avg_wipe_cost)}" if avg_wipe_cost else "Lenço —",
)

tab_sheet, tab_inventory, tab_costs = st.tabs(["Planilha Geral", "Estoque por Tamanho", "Resumo de Custos"])

with tab_sheet:
    with st.expander("Adicionar nova linha rapidamente", expanded=False):
        with st.form("add_row_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            f_date = c1.date_input("Data", value=date.today())
            f_mov = c2.selectbox("Movimento", MOVEMENTS)
            f_cat = c3.selectbox("Categoria", CATEGORIES)

            c4, c5 = st.columns([2, 1])
            f_brand = c4.text_input("Marca / Descrição", placeholder="Ex.: Pampers Confort Sec")
            f_variant = c5.text_input("Tamanho / Embalagem", placeholder="Ex.: M, G ou 96 un.")

            c6, c7, c8 = st.columns(3)
            f_packs = c6.number_input("Qtd. Pacotes", value=1.0, step=0.5)
            f_units = c7.number_input("Unid. por Pacote", min_value=1, value=60, step=1)
            f_price = c8.number_input("Valor Total (R$)", min_value=0.0, value=0.0, step=0.50)

            f_notes = st.text_input("Observações (opcional)")
            submitted = st.form_submit_button("Adicionar na planilha", type="primary")
            if submitted:
                if not f_brand.strip():
                    st.error("Informe a marca ou descrição do produto.")
                else:
                    default_var = "M" if f_cat == "Fralda" else "96 un."
                    new_row = pd.DataFrame([{
                        "Data": f_date,
                        "Movimento": f_mov,
                        "Categoria": f_cat,
                        "Marca": f_brand.strip(),
                        "Tamanho/Tipo": f_variant.strip() or default_var,
                        "Pacotes": f_packs,
                        "Un./Pacote": int(f_units),
                        "Valor (R$)": f_price if f_mov == "Entrada" else 0.0,
                        "Observações": f_notes.strip(),
                    }])
                    st.session_state.df = pd.concat([normalize_df(new_row), st.session_state.df], ignore_index=True)
                    save_data(st.session_state.df)
                    st.rerun()

    st.caption("Clique em qualquer célula para editar diretamente, use a última linha (+) para adicionar ou Delete para remover.")
    edited_df = st.data_editor(
        full_df,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "Movimento": st.column_config.SelectboxColumn("Movimento", options=MOVEMENTS, required=True),
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIES, required=True),
            "Marca": st.column_config.TextColumn("Marca / Descrição", required=True),
            "Tamanho/Tipo": st.column_config.TextColumn("Tam. / Tipo", required=True),
            "Pacotes": st.column_config.NumberColumn("Pacotes", step=0.5, format="%.1f"),
            "Un./Pacote": st.column_config.NumberColumn("Un./Pct", min_value=1, step=1, format="%d"),
            "Total Unid.": st.column_config.NumberColumn("Total Unid.", disabled=True, format="%d"),
            "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", min_value=0.0, step=0.01, format="R$ %.2f"),
            "Custo / Un. (R$)": st.column_config.NumberColumn("R$/Unid.", disabled=True, format="R$ %.2f"),
            "Observações": st.column_config.TextColumn("Observações"),
        },
        key="main_sheet_editor",
    )

    normalized_edited = normalize_df(edited_df[BASE_COLS])
    normalized_current = normalize_df(st.session_state.df)
    if not normalized_edited.equals(normalized_current):
        st.session_state.df = normalized_edited
        save_data(st.session_state.df)
        st.rerun()

with tab_inventory:
    st.subheader("Fraldas por tamanho")
    if diaper_df.empty:
        st.info("Nenhuma fralda registrada ainda.")
    else:
        size_summary = (
            diaper_df.groupby("Tamanho/Tipo", as_index=False)
            .agg(
                Saldo=("Total Unid.", "sum"),
                Compradas=("Total Unid.", lambda s: s[s > 0].sum()),
                Usadas=("Total Unid.", lambda s: abs(s[s < 0].sum())),
            )
        )
        st.dataframe(size_summary, use_container_width=True, hide_index=True)

        st.markdown("**Baixa rápida por tamanho**")
        cols = st.columns(min(len(size_summary), 6))
        for idx, row in size_summary.iterrows():
            sz = row["Tamanho/Tipo"]
            with cols[idx % len(cols)]:
                if st.button(f"-10 un. ({sz})", key=f"minus10_{sz}", use_container_width=True):
                    quick = pd.DataFrame([{
                        "Data": date.today(),
                        "Movimento": "Saída",
                        "Categoria": "Fralda",
                        "Marca": f"Baixa rápida ({sz})",
                        "Tamanho/Tipo": sz,
                        "Pacotes": 1.0,
                        "Un./Pacote": 10,
                        "Valor (R$)": 0.0,
                        "Observações": "Baixa rápida na aba de estoque",
                    }])
                    st.session_state.df = pd.concat([normalize_df(quick), st.session_state.df], ignore_index=True)
                    save_data(st.session_state.df)
                    st.rerun()

    st.subheader("Lenços umedecidos por marca")
    if wipe_df.empty:
        st.info("Nenhum lenço registrado ainda.")
    else:
        wipe_summary = (
            wipe_df.groupby(["Marca", "Tamanho/Tipo"], as_index=False)
            .agg(
                Saldo=("Total Unid.", "sum"),
                Comprados=("Total Unid.", lambda s: s[s > 0].sum()),
                Usados=("Total Unid.", lambda s: abs(s[s < 0].sum())),
                Gasto=("Valor (R$)", "sum"),
            )
        )
        st.dataframe(wipe_summary, use_container_width=True, hide_index=True)

with tab_costs:
    st.subheader("Gastos mensais")
    compras = full_df[full_df["Movimento"] == "Entrada"].copy()
    if compras.empty:
        st.info("Nenhuma compra registrada.")
    else:
        compras["Mês"] = pd.to_datetime(compras["Data"]).dt.strftime("%Y-%m")
        monthly = (
            compras.groupby(["Mês", "Categoria"], as_index=False)["Valor (R$)"]
            .sum()
            .pivot(index="Mês", columns="Categoria", values="Valor (R$)")
            .fillna(0.0)
        )
        monthly["Total (R$)"] = monthly.sum(axis=1)
        st.dataframe(monthly.sort_index(ascending=False), use_container_width=True)

        st.subheader("Comparativo de custo por unidade entre marcas")
        brand_cmp = (
            compras[compras["Valor (R$)"] > 0]
            .groupby(["Marca", "Categoria"], as_index=False)
            .agg(Unidades=("Total Unid.", "sum"), Total_Gasto=("Valor (R$)", "sum"))
        )
        if not brand_cmp.empty:
            brand_cmp["Custo / Unid. (R$)"] = (brand_cmp["Total_Gasto"] / brand_cmp["Unidades"]).round(2)
            st.dataframe(brand_cmp.sort_values("Custo / Unid. (R$)"), use_container_width=True, hide_index=True)