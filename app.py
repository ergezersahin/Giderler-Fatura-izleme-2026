import streamlit as st
import datetime

st.set_page_config(page_title="Gider ve Fatura Takipçisi", page_icon="💰", layout="wide")

# Oturum verilerini başlat
if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"id": "1", "date": "2026-11-01", "bank": "Garanti", "type": "Kredi Kartı", "amount": 4500.0, "paid": False, "note": "Kasım ekstresi"},
        {"id": "2", "date": "2026-11-05", "bank": "Ziraat", "type": "Elektrik", "amount": 650.0, "paid": True, "note": "Otomatik ödeme"}
    ]

st.sidebar.title("📌 Menü")
menu = st.sidebar.selectbox("Sayfa Seçin", ["Ana Panel", "Yeni Ödeme Ekle"])

if menu == "Ana Panel":
    st.title("💰 Gider ve Fatura Takipçisi")
    
    total_pending = sum(item["amount"] for item in st.session_state.expenses if not item["paid"])
    total_paid = sum(item["amount"] for item in st.session_state.expenses if item["paid"])
    
    col1, col2 = st.columns(2)
    col1.metric("Ödenecek Toplam", f"{total_pending:,.2f} TL")
    col2.metric("Ödenen Toplam", f"{total_paid:,.2f} TL")
    
    st.divider()
    st.subheader("📋 Ödeme Listesi")
    
    search_query = st.text_input("🔍 Banka veya tür ara...").lower()
    
    updated = False
    for item in st.session_state.expenses:
        if search_query and not (search_query in item["bank"].lower() or search_query in item["type"].lower()):
            continue
            
        cols = st.columns([0.1, 0.4, 0.2, 0.2, 0.1])
        new_paid = cols[0].checkbox("", value=item["paid"], key=f"paid_{item['id']}")
        if new_paid != item["paid"]:
            item["paid"] = new_paid
            updated = True
            
        cols[1].markdown(f"**{item['type']}**\n\n`{item['bank']}` • `{item['date']}`")
        cols[2].markdown(f"**{item['amount']:,.2f} TL**")
        
        if item["paid"]:
            cols[3].success("Ödendi")
        else:
            cols[3].warning("Bekliyor")
            
        if cols[4].button("🗑️", key=f"del_{item['id']}"):
            st.session_state.expenses = [e for e in st.session_state.expenses if e["id"] != item["id"]]
            st.rerun()
            
    if updated:
        st.rerun()

elif menu == "Yeni Ödeme Ekle":
    st.title("➕ Yeni Ödeme Kaydı")
    
    with st.form("add_form"):
        date_val = st.date_input("Ödeme Tarihi", datetime.date.today())
        bank_val = st.text_input("Banka / Kurum Adı", placeholder="Örn: Garanti, Ziraat")
        type_val = st.text_input("Ödeme Türü", placeholder="Örn: Elektrik, Su, Kredi Kartı")
        amount_val = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        paid_val = st.checkbox("Ödendi olarak işaretle")
        note_val = st.text_area("Not (Opsiyonel)")
        
        if st.form_submit_button("Ödemeyi Kaydet"):
            if bank_val and type_val and amount_val > 0:
                new_item = {
                    "id": str(datetime.datetime.now().timestamp()),
                    "date": str(date_val),
                    "bank": bank_val.strip(),
                    "type": type_val.strip(),
                    "amount": amount_val,
                    "paid": paid_val,
                    "note": note_val.strip()
                }
                st.session_state.expenses.append(new_item)
                st.success("Ödeme başarıyla eklendi! Sol menüden 'Ana Panel'e dönebilirsiniz.")
            else:
                st.error("Lütfen zorunlu alanları doldurun.")
