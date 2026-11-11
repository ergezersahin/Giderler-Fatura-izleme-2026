import streamlit as st
import datetime
import pandas as pd
import io

# PDF Raporlama için ReportLab kütüphaneleri
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

# --- TÜRKÇE KARAKTER DÖNÜŞTÜRÜCÜ (PDF için %100 Garanti Çözüm) ---
def tr_to_en(text):
    if not isinstance(text, str):
        return str(text)
    tr_chars = {'ş': 's', 'Ş': 'S', 'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U'}
    for k, v in tr_chars.items():
        text = text.replace(k, v)
    return text

# --- PDF OLUŞTURMA FONKSİYONU ---
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
    
    table_data = [[tr_to_en("Tür / Kategori"), tr_to_en("Banka"), tr_to_en("Tarih"), tr_to_en("Tutar (TL)"), tr_to_en("Durum")]]
    
    for item in items:
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
menu = st.sidebar.selectbox("Sayfa Seçin", ["Ana Panel", "Yeni Ödeme Ekle"])

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
        for item in filtered_items:
            try:
                date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except:
                formatted_date = item["date"]
                
            status_text = "Ödendi ✅" if item["paid"] else "Bekliyor ⏳"
            
            with st.container(border=True):
                r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([0.1, 0.25, 0.2, 0.15, 0.15, 0.15])
                
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
            bank_selection = st.selectbox("Banka / Kurum Seçin", all_banks + ["+ Yeni Banka Ekle..."])
            if bank_selection == "+ Yeni Banka Ekle...":
                bank_val = st.text_input("Yeni Banka Adını Yazın")
            else:
                bank_val = bank_selection
                
        with col_t:
            type_selection = st.selectbox("Ödeme Türü / Kategori Seçin", all_types + ["+ Yeni Kategori Ekle..."])
            if type_selection == "+ Yeni Kategori Ekle...":
                type_val = st.text_input("Yeni Kategori Adını Yazın")
            else:
                type_val = type_selection
                
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
