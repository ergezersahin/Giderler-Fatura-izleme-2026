import streamlit as st
import datetime
import pandas as pd
import io
import json
import os

# PDF Raporlama için ReportLab kütüphaneleri
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gider ve Fatura Takipçisi", page_icon="💰", layout="wide")

# --- CSS İLE KOMPAKT / SIKILAŞTIRILMIŞ GÖRÜNÜM VE RENKLİ ROZETLER ---
st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] {
            align-items: center;
        }
        div.st-key-container, div[data-testid="stVerticalBlock"] > div.element-container {
            margin-bottom: -10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- DOSYA TABANLI KALICI VERİ YÖNETİMİ ---
DATA_FILE = "expenses.json"

def load_expenses():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_expenses(expenses):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False, indent=4)

if "expenses" not in st.session_state:
    st.session_state.expenses = load_expenses()

if "deleted_banks" not in st.session_state:
    st.session_state.deleted_banks = []
if "deleted_types" not in st.session_state:
    st.session_state.deleted_types = []

default_banks = ["Garanti", "Ziraat", "İş Bankası", "Yapı Kredi", "Akbank", "TEB", "Nakit", "Diğer"]
default_types = ["Kredi Kartı Ödemesi", "Bina / Site Aidatı", "Elektrik Bedeli", "Su Bedeli", "Doğalgaz Bedeli", "İnternet/TV Bedeli", "Kira Gelir Vergisi", "Motorlu Taşıt Vergisi","Emlak Vergisi", "Apt. Temizlik Bedeli", "Diğer"]

existing_banks = list(set(item["bank"] for item in st.session_state.expenses))
all_banks = sorted(list(set([b for b in (default_banks + existing_banks) if b not in st.session_state.deleted_banks])))

existing_types = list(set(item["type"] for item in st.session_state.expenses))
all_types = sorted(list(set([t for t in (default_types + existing_types) if t not in st.session_state.deleted_types])))

def tr_to_en(text):
    if not isinstance(text, str):
        return str(text)
    tr_chars = {'ş': 's', 'Ş': 'S', 'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
    for k, v in tr_chars.items():
        text = text.replace(k, v)
    return text

def generate_pdf(items):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=15,
        alignment=1
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#374151')
    )
    
    elements.append(Paragraph(tr_to_en("Gider ve Fatura Takip Raporu"), title_style))
    elements.append(Paragraph(tr_to_en(f"Olusturulma Tarihi: {datetime.date.today().strftime('%d/%m/%Y')}"), normal_style))
    elements.append(Spacer(1, 15))
    
    table_data = [[tr_to_en("Tür / Kategori"), tr_to_en("Ödeme Şekli"), tr_to_en("Tarih"), tr_to_en("Tutar (TL)"), tr_to_en("Durum")]]
    
    sorted_items_for_pdf = sorted(items, key=lambda x: x.get("date", ""))
    
    for item in sorted_items_for_pdf:
        try:
            date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except:
            formatted_date = item["date"]
            
        status = "Odendi" if item["paid"] else "Bekliyor"
        table_data.append([
            tr_to_en(item["type"]),
            tr_to_en(item["bank"]),
            formatted_date,
            f"{item['amount']:,.2f} TL",
            tr_to_en(status)
        ])
        
    t = Table(table_data, colWidths=[120, 100, 80, 100, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


st.sidebar.title("📌 Menü")
menu = st.sidebar.selectbox("Sayfa Seçin", ["Ana Panel", "Yeni Ödeme Ekle", "Tanımları Yönet", "Çıkış Yap"])

st.sidebar.divider()
st.sidebar.markdown(
    "<div style='font-size: 11px; color: #6b7280; text-align: center;'>Bu program Şahin ERGEZER tarafından hazırlanmıştır (2026).</div>", 
    unsafe_allow_html=True
)

if menu == "Ana Panel":
    st.title("💰 Gider ve Fatura Takipçisi")
    
    total_pending = sum(item["amount"] for item in st.session_state.expenses if not item["paid"])
    total_paid = sum(item["amount"] for item in st.session_state.expenses if item["paid"])
    
    col1, col2 = st.columns(2)
    col1.metric("Ödenecek Toplam", f"{total_pending:,.2f} TL")
    col2.metric("Ödenen Toplam", f"{total_paid:,.2f} TL")
    
    st.divider()
    
    col_h1, col_h2 = st.columns([0.6, 0.4])
    with col_h1:
        st.subheader("📋 Ödeme Listesi")
    with col_h2:
        if st.session_state.expenses:
            pdf_bytes = generate_pdf(st.session_state.expenses)
            st.download_button(
                label="📄 PDF Raporu İndir",
                data=pdf_bytes,
                file_name=f"gider_raporu_{datetime.date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        selected_bank_filter = st.selectbox("🏦 Banka Filtresi", ["Tümü"] + all_banks)
    with col_f2:
        selected_type_filter = st.selectbox("📂 Kategori Filtresi", ["Tümü"] + all_types)
    with col_f3:
        search_query = st.text_input("🔍 Notlarda ara...").lower()
    
    sorted_expenses = sorted(st.session_state.expenses, key=lambda x: x.get("date", ""))
    today_date = datetime.date.today()
    
    filtered_items = []
    for item in sorted_expenses:
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
        for item in filtered_items:
            try:
                date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d").date()
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                date_obj = today_date
                formatted_date = item["date"]
                
            # --- RENKLİ HTML ROZETLER ---
            is_paid = item["paid"]
            if not is_paid:
                if date_obj < today_date:
                    status_badge = "<span style='color: white; background-color: #dc2626; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;'>🔴 VADESİ GEÇTİ</span>"
                elif date_obj == today_date:
                    status_badge = "<span style='color: white; background-color: #ea580c; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;'>🟠 BUGÜN ÖDENECEK</span>"
                else:
                    status_badge = "<span style='color: #4b5563; background-color: #f3f4f6; padding: 3px 8px; border-radius: 4px; font-size: 12px;'>⏳ Bekliyor</span>"
            else:
                status_badge = "<span style='color: white; background-color: #16a34a; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;'>Ödendi ✅</span>"
            
            with st.container(border=True):
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7 = st.columns([0.06, 0.24, 0.18, 0.15, 0.15, 0.11, 0.11])
                
                new_paid = r_col1.checkbox("Ödendi", value=item["paid"], key=f"paid_{item['id']}", label_visibility="collapsed")
                if new_paid != item["paid"]:
                    item["paid"] = new_paid
                    save_expenses(st.session_state.expenses)
                    st.rerun()
                    
                r_col2.markdown(f"**{item['type']}** <span style='color:gray; font-size:12px;'>({item['bank']})</span>", unsafe_allow_html=True)
                r_col3.markdown(f"📅 {formatted_date}")
                r_col4.markdown(f"💰 **{item['amount']:,.2f} TL**")
                r_col5.markdown(status_badge, unsafe_allow_html=True)
                
                edit_key = f"edit_mode_{item['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                if r_col6.button("✏️ Düzenle", key=f"btn_edit_{item['id']}", use_container_width=True):
                    st.session_state[edit_key] = not st.session_state[edit_key]
                    st.rerun()
                
                if r_col7.button("🗑️ Sil", key=f"del_{item['id']}", use_container_width=True):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e["id"] != item["id"]]
                    save_expenses(st.session_state.expenses)
                    st.rerun()
                
                if item.get("note"):
                    st.caption(f"📝 Not: {item['note']}")
                
                if st.session_state[edit_key]:
                    st.markdown("---")
                    st.markdown(f"##### ✍️ Kaydı Düzenle: {item['type']}")
                    with st.form(key=f"form_edit_{item['id']}"):
                        e_date = st.date_input("Tarih", date_obj, key=f"ed_date_{item['id']}")
                        
                        e_bank = st.selectbox("Banka / Ödeme Şekli", all_banks, index=all_banks.index(item["bank"]) if item["bank"] in all_banks else 0, key=f"ed_bank_{item['id']}")
                        e_type = st.selectbox("Kategori / Tür", all_types, index=all_types.index(item["type"]) if item["type"] in all_types else 0, key=f"ed_type_{item['id']}")
                        
                        e_amount = st.number_input("Tutar (TL)", min_value=0.0, value=float(item["amount"]), step=10.0, key=f"ed_amount_{item['id']}")
                        e_note = st.text_area("Not", value=item.get("note", ""), key=f"ed_note_{item['id']}")
                        
                        col_sub1, col_sub2 = st.columns(2)
                        with col_sub1:
                            submit_update = st.form_submit_button("Değişiklikleri Kaydet", use_container_width=True)
                        with col_sub2:
                            cancel_update = st.form_submit_button("İptal", use_container_width=True)
                        
                        if submit_update:
                            item["date"] = str(e_date)
                            item["bank"] = e_bank
                            item["type"] = e_type
                            item["amount"] = e_amount
                            item["note"] = e_note.strip()
                            save_expenses(st.session_state.expenses)
                            st.session_state[edit_key] = False
                            st.success("Kayıt başarıyla güncellendi!")
                            st.rerun()
                        
                        if cancel_update:
                            st.session_state[edit_key] = False
                            st.rerun()

elif menu == "Yeni Ödeme Ekle":
    st.title("➕ Yeni Ödeme Kaydı")
    
    with st.form("add_expense_form", clear_on_submit=True):
        date_val = st.date_input("Ödeme Tarihi", datetime.date.today())
        
        col_b, col_t = st.columns(2)
        
        with col_b:
            st.markdown("##### Banka Seçimi")
            bank_choice = st.selectbox("Listeden Seçin", all_banks, key="bank_select")
            custom_bank = st.text_input("Veya Yeni Banka Yazın (İsteğe bağlı)", placeholder="Örn: QNB, Fibabanka", key="custom_bank_input")
            
        with col_t:
            st.markdown("##### Kategori Seçimi")
            type_choice = st.selectbox("Listeden Seçin", all_types, key="type_select")
            custom_type = st.text_input("Veya Yeni Kategori Yazın (İsteğe bağlı)", placeholder="Örn: Vergi, Aidat", key="custom_type_input")
            
        amount_str = st.text_input("Tutar (TL)", value="", placeholder="Örn: 1250.50", key="amount_input")
        
        paid_val = st.checkbox("Ödendi olarak işaretle", key="paid_input")
        note_val = st.text_area("Not (Opsiyonel)", key="note_input")
        
        submitted = st.form_submit_button("Ödemeyi Kaydet", type="primary", use_container_width=True)
        
        if submitted:
            final_bank = custom_bank.strip() if custom_bank.strip() else bank_choice
            final_type = custom_type.strip() if custom_type.strip() else type_choice
            
            try:
                clean_amount = float(amount_str.replace(" ", "").replace("TL", "").replace(".", "").replace(",", ".")) if amount_str else 0.0
            except:
                clean_amount = 0.0
            
            if final_bank and final_type and clean_amount > 0:
                new_item = {
                    "id": str(datetime.datetime.now().timestamp()),
                    "date": str(date_val),
                    "bank": final_bank,
                    "type": final_type,
                    "amount": clean_amount,
                    "paid": paid_val,
                    "note": note_val.strip()
                }
                st.session_state.expenses.append(new_item)
                save_expenses(st.session_state.expenses)
                st.success(f"Ödeme başarıyla eklendi! ({final_bank} - {final_type})")
            else:
                st.error("Lütfen geçerli bir banka, kategori ve tutar girin.")

elif menu == "Tanımları Yönet":
    st.title("⚙️ Banka ve Kategori Yönetimi")
    st.write("Listelerde görünmesini istemediğiniz banka veya kategorileri buradan silebilirsiniz.")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.subheader("🏦 Bankalar")
        for b in all_banks:
            rc1, rc2 = st.columns([0.7, 0.3])
            rc1.markdown(f"- {b}")
            if rc2.button("Kaldır", key=f"del_bank_{b}", use_container_width=True):
                if b not in st.session_state.deleted_banks:
                    st.session_state.deleted_banks.append(b)
                    st.success(f"'{b}' bankası listeden kaldırıldı.")
                    st.rerun()
                    
    with col_m2:
        st.subheader("📂 Kategoriler")
        for t in all_types:
            tc1, tc2 = st.columns([0.7, 0.3])
            tc1.markdown(f"- {t}")
            if tc2.button("Kaldır", key=f"del_type_{t}", use_container_width=True):
                if t not in st.session_state.deleted_types:
                    st.session_state.deleted_types.append(t)
                    st.success(f"'{t}' kategorisi listeden kaldırıldı.")
                    st.rerun()

elif menu == "Çıkış Yap":
    save_expenses(st.session_state.expenses)
    st.title("🔒 Oturum Kapatıldı")
    st.success("Tüm verileriniz başarıyla kaydedildi (`expenses.json`). Güvenle çıkış yapabilirsiniz.")
    st.info("Uygulamaya tekrar dönmek için sol menüden başka bir sayfa seçebilirsiniz.")
