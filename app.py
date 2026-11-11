import streamlit as st
import datetime

st.set_page_config(page_title="Gider ve Fatura Takipçisi", page_icon="💰", layout="wide")

# Oturum verilerini başlat
if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"id": "1", "date": "2026-11-01", "bank": "Garanti", "type": "Kredi Kartı", "amount": 4500.0, "paid": False, "note": "Kasım ekstresi"},
        {"id": "2", "date": "2026-11-05", "bank": "Ziraat", "type": "Elektrik", "amount": 650.0, "paid": True, "note": "Otomatik ödeme"},
        {"id": "3", "date": "2026-11-10", "bank": "İş Bankası", "type": "Su", "amount": 320.0, "paid": False, "note": "Fatura"}
    ]

# Varsayılan veya kayıtlı verilerden dinamik liste oluşturma
default_banks = ["Garanti", "Ziraat", "İş Bankası", "Yapı Kredi", "Akbank", "Enpara", "Nakit", "Diğer"]
default_types = ["Kredi Kartı", "Elektrik", "Su", "Doğalgaz", "İnternet", "Kira", "Telefon", "Market", "Diğer"]

# Mevcut kayıtlı özel banka/türleri de listeye dahil et
existing_banks = list(set(item["bank"] for item in st.session_state.expenses))
all_banks = sorted(list(set(default_banks + existing_banks)))

existing_types = list(set(item["type"] for item in st.session_state.expenses))
all_types = sorted(list(set(default_types + existing_types)))

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
    
    # --- FİLTRELER ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        selected_bank_filter = st.selectbox("🏦 Banka Filtresi", ["Tümü"] + all_banks)
    with col_f2:
        selected_type_filter = st.selectbox("📂 Kategori Filtresi", ["Tümü"] + all_types)
    with col_f3:
        search_query = st.text_input("🔍 Notlarda ara...").lower()
    
    updated = False
    filtered_count = 0
    
    for item in st.session_state.expenses:
        # Filtreleme mantığı
        if selected_bank_filter != "Tümü" and item["bank"] != selected_bank_filter:
            continue
        if selected_type_filter != "Tümü" and item["type"] != selected_type_filter:
            continue
        if search_query and not search_query in item.get("note", "").lower():
            continue
            
        filtered_count += 1
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
            
    if filtered_count == 0:
        st.info("Seçilen kriterlere uygun ödeme bulunamadı.")
            
    if updated:
        st.rerun()

elif menu == "Yeni Ödeme Ekle":
    st.title("➕ Yeni Ödeme Kaydı")
    
    with st.form("add_form"):
        date_val = st.date_input("Ödeme Tarihi", datetime.date.today())
        
        # Seçmeli veya yeni eklenebilir yapı için text_input + selectbox kombinasyonu
        col_b, col_t = st.columns(2)
        with col_b:
            bank_choice = st.selectbox("Banka / Kurum Seç", all_banks + ["+ Diğer (Yeni Yaz)"])
            if bank_choice == "+ Diğer (Yeni Yaz)":
                bank_val = st.text_input("Yeni Banka / Kurum Adını Girin")
            else:
                bank_val = bank_choice
                
        with col_t:
            type_choice = st.selectbox("Ödeme Türü / Kategori Seç", all_types + ["+ Diğer (Yeni Yaz)"])
            if type_choice == "+ Diğer (Yeni Yaz)":
                type_val = st.text_input("Yeni Ödeme Türünü Girin")
            else:
                type_val = type_choice
                
        amount_val = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        paid_val = st.checkbox("Ödendi olarak işaretle")
        note_val = st.text_area("Not (Opsiyonel)")
        
        if st.form_submit_button("Ödemeyi Kaydet"):
            final_bank = bank_val.strip() if bank_val else ""
            final_type = type_val.strip() if type_val else ""
            
            if final_bank and final_type and amount_val > 0:
                new_item = {
                    "id": str(datetime.datetime.now().timestamp()),
                    "date": str(date_val),
                    "bank": final_bank,
                    "type": final_type,
                    "amount": amount_val,
                    "paid": paid_val,
                    "note": note_val.strip()
                }
                st.session_state.expenses.append(new_item)
                st.success("Ödeme başarıyla eklendi! Sol menüden 'Ana Panel'e dönebilirsiniz.")
            else:
                st.error("Lütfen banka, tür ve tutar alanlarını eksiksiz doldurun.")
