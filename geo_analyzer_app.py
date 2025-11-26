# file: geo_analyzer_app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import base64

st.set_page_config(page_title="GEO Analyzer Pro", layout="centered", page_icon="rocket")

# Custom CSS - exactly like the iamdigital tool
st.markdown("""
<style>
    .big-font {font-size:50px !important; font-weight:bold; color:#1E88E5;}
    .score-box {font-size:72px; font-weight:bold; text-align:center; padding:20px;}
    .urgent {background:#D32F2F; color:white; padding:10px; border-radius:10px;}
    .high {background:#F57C00; color:white; padding:10px; border-radius:10px;}
    .medium {background:#FBC02D; color:black; padding:10px; border-radius:10px;}
    .low {background:#388E3C; color:white; padding:10px; border-radius:10px;}
    .issue {margin:10px 0; padding:15px; background:#f8f9fa; border-left:5px solid #1E88E5; border-radius:5px;}
</style>
""", unsafe_allow_html=True)

st.title("rocket GEO Analyzer Pro 2025")
st.markdown("**Make your content the #1 source for ChatGPT, Perplexity, Claude & Gemini**")

url = st.text_input("Enter URL to analyze", placeholder="https://your-site.com/product-page")

if st.button("Analyze Now", type="primary"):
    if not url.startswith("http"):
        url = "https://" + url

    with st.spinner("Crawling and analyzing page..."):
        headers = {'User-Agent': 'GEOAnalyzerBot/1.0 (+https://yourdomain.com)'}
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text()
        except:
            st.error("Failed to fetch the page. Check URL or try again later.")
            st.stop()

        # === Scoring Engine (same as before, compact) ===
        tech_score = 0
        structure_score = 0
        authority_score = 0
        issues = []

        # Technical (40%)
        if soup.find("script", type="application/ld+json"): tech_score += 35
        else: issues.append(("No JSON-LD structured data", "Quick"))
        if any(soup.find(t) for t in ['article','section','main']): tech_score += 20
        else: issues.append(("Limited semantic HTML", "Moderate"))
        if soup.find("h1") and len(soup.find_all(re.compile("^h[1-6]$"))) > 3: tech_score += 20
        else: issues.append(("Fix heading hierarchy", "Moderate"))
        if re.search(r'\d{4}-\d{2}-\d{2}|202[4-9]', text): tech_score += 15
        else: issues.append(("Add publish/update date", "Quick"))
        if len([p for p in soup.find_all("p") if len(p.text.split()) > 80]) < 3: tech_score += 10

        # Structure (35%)
        if soup.find_all(["table", "dl"]): structure_score += 40
        else: issues.append(("Add spec/comparison tables", "Moderate"))
        if soup.find_all(["ul","ol"]): structure_score += 25
        else: issues.append(("Use bullet/numbered lists", "Quick"))
        if "faq" in text.lower(): structure_score += 35
        else: issues.append(("Add FAQ section", "Moderate"))

        # Authority (25%)
        if any(x in text.lower() for x in ["by ", "author", "phd", "engineer"]): authority_score += 40
        else: issues.append(("Add author byline + credentials", "Quick"))
        external = len([a for a in soup.find_all("a", href=True) if urlparse(a["href"]).netloc != urlparse(url).netloc])
        if external > 8: authority_score += 35
        else: issues.append(("Link to reputable sources", "Moderate"))
        if soup.find(src=re.compile("badge|cert|trust", re.I)): authority_score += 25

        # Final score
        final_score = round(tech_score*0.4 + structure_score*0.35 + authority_score*0.25, 1)

        # Grade & Priority
        grades = {(94,"A+"), (87,"A"), (80,"A-"), (77,"B+"), (73,"B"), (70,"B-"), (67,"C+"), (63,"C"), (60,"C-")}
        grade = next((g for s,g in grades if final_score >= s), "F")
        priority = "URGENT" if final_score < 60 else "HIGH" if final_score < 75 else "MEDIUM" if final_score < 85 else "LOW"
        priority_class = priority.lower()

        # === Display Results ===
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f"<div class='score-box'>{final_score}<small>/100</small></div>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='text-align:center'>{grade}</h2>", unsafe_allow_html=True)
            st.markdown(f"<div class='{priority_class}' style='text-align:center; font-size:20px'>{priority} PRIORITY</div>", unsafe_allow_html=True)

        st.markdown("### Breakdown")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Technical Foundation", f"{tech_score}/100", "40% weight")
        with col2: st.metric("Content Structure", f"{structure_score}/100", "35% weight")
        with col3: st.metric("Authority Signals", f"{authority_score}/100", "25% weight")

        st.markdown("### Actionable Fixes")
        for issue, effort in issues[:10]:
            effort_icon = "Quick" if effort == "Quick" else "Moderate" if effort == "Moderate" else "Major"
            st.markdown(f"<div class='issue'>• {issue} <b>[{effort_icon}]</b></div>", unsafe_allow_html=True)

        # === PDF Export ===
        def create_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph("GEO Analyzer Report", styles['Title']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"URL: {url}", styles['Normal']))
            story.append(Paragraph(f"Score: {final_score}/100 ({grade}) – {priority}", styles['Normal']))
            story.append(Spacer(1, 20))
            for issue, effort in issues:
                story.append(Paragraph(f"• {issue} [{effort}]", styles['Normal']))
            doc.build(story)
            return buffer.getvalue()

        pdf_data = create_pdf()
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"GEO_Report_{urlparse(url).netloc}_{final_score}.pdf",
            mime="application/pdf"
        )

st.markdown("— Built with love by GEO addicts | Deployed free on Streamlit")
