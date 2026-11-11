import streamlit as st
import datetime
import pandas as pd

st.set_page_config(page_title="Gider ve Fatura Takipçisi", page_icon="💰", layout="wide")

# Oturum verilerini başlat
if "expenses" not in st.session_state:
    st.session_state.expenses = [
        {"id": "1", "date": "2026-11-01", "bank": "Garanti", "type": "Kredi Kartı", "amount": 4500.0, "paid": False, "note": "Kasım ekstresi"},
        {"id": "2", "date": "2026-11-05", "bank": "Ziraat", "type": "Elektrik", "amount": 650.0, "paid": True, "note": "Otomatik ödeme"},
        {"id": "3", "date": "2026-11-10", "bank": "İş Bankası", "type": "Su", "amount": 320.0, "paid": False, "note": "Fatura"}
    ]

# Varsayılan banka ve kategori listeleri
default_banks = ["Garanti", "Ziraat", "İş Bankası", "Yapı Kredi", "Akbank", "Enpara", "Nakit", "Diğer"]
default_types = ["Kredi Kartı", "Elektrik", "Su", "Doğalgaz", "İnternet", "Kira", "Telefon", "Market", "Diğer"]

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
    
    # --- ÜST BAŞLIK VE ÇIKTI / İNDİRME BUTONLARI ---
    col_h1, col_h2 = st.columns([0.7, 0.3])
    with col_h1:
        st.subheader("📋 Ödeme Listesi")
    with col_h2:
        if st.session_state.expenses:
            # Excel / CSV olarak indirme hazırlığı
            df_export = pd.DataFrame(st.session_state.expenses)
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Excel / CSV İndir",
                data=csv_data,
                file_name=f"giderler_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # --- FİLTRELER ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        selected_bank_filter = st.selectbox("🏦 Banka Filtresi", ["Tümü"] + all_banks)
    with col_f2:
        selected_type_filter = st.selectbox("📂 Kategori Filtresi", ["Tümü"] + all_types)
    with col_f3:
        search_query = st.text_input("🔍 Notlarda ara...").lower()
    
    # Filtrelenmiş liste
    filtered_items = []
    for item in st.session_state.expenses:
        if selected_bank_filter != "Tümü" and item["bank"] != selected_bank_filter:
            continue
        if selected_type_filter != "Tümü" and item["type"] != selected_type_filter:
            continue
        if search_query and not search_query in item.get("note", "").lower():
            continue
        filtered_items.append(item)
        
    if not filtered_items:
        st.info("Seçilen kriterlere uygun ödeme bulunamadı.")
    else:
        # Tablo Görünümü ve Yönetimi için Kompakt Satırlar
        for item in filtered_items:
            # Tarihi GG/AA/YYYY formatına çevir
            try:
                date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = item["date"]
                
            status_text = "Ödendi ✅" if item["paid"] else "Bekliyor ⏳"
            
            # Her satırı şık bir container içinde tablo sütunları gibi hizalayalım
            with st.container(border=True):
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([0.1, 0.25, 0.2, 0.15, 0.15, 0.15])
                
                # Ödendi Checkbox'ı
                new_paid = r_col1.checkbox("Ödendi", value=item["paid"], key=f"paid_{item['id']}", label_visibility="collapsed")
                if new_paid != item["paid"]:
                    item["paid"] = new_paid
                    st.rerun()
                    
                r_col2.markdown(f"**{item['type']}**\n\n`{item['bank']}`")
                r_col3.markdown(f"📅 **{formatted_date}**")
                r_col4.markdown(f"💰 **{item['amount']:,.2f} TL**")
                r_col5.markdown(f"*{status_text}*")
                
                if r_col6.button("🗑️ Sil", key=f"del_{item['id']}", use_container_width=True):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e["id"] != item["id"]]
                    st.rerun()
                
                if item.get("note"):
                    st.caption(f"📝 Not: {item['note']}")

elif menu == "Yeni Ödeme Ekle":
    st.title("➕ Yeni Ödeme Kaydı")
    
    with st.form("add_form"):
        date_val = st.date_input("Ödeme Tarihi", datetime.date.today())
        
        col_b, col_t = st.columns(2)
        with col_b:
            bank_input_type = st.radio("Banka Giriş Yöntemi", ["Listeden Seç", "Yeni Yaz"], horizontal=True)
            if bank_input_type == "Listeden Seç":
                bank_val = st.selectbox("Banka Seçin", all_banks)
            else:
                bank_val = st.text_input("Yeni Banka Adını Yazın")
                
        with col_t:
            type_input_type = st.radio("Kategori Giriş Yöntemi", ["Listeden Seç", "Yeni Yaz"], horizontal=True, key="type_radio")
            if type_input_type == "Listeden Seç":
                type_val = st.selectbox("Kategori Seçin", all_types)
            else:
                type_val = st.text_input("Yeni Kategori Adını Yazın")
                
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