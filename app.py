import streamlit as st
import pandas as pd
import random
import json
import io

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Pro Group Mixer", layout="wide")

# --- 2. CSS: TARGETING EMOJIS FOR COLORS ---
# This attempts to force green for Likes and red for Avoids by targeting the labels
st.markdown("""
    <style>
    div[data-testid="stWidgetLabel"]:contains("⭐") + div [data-baseweb="tag"] { background-color: #28a745 !important; }
    div[data-testid="stWidgetLabel"]:contains("🚫") + div [data-baseweb="tag"] { background-color: #dc3545 !important; }
    [data-baseweb="tag"] span { color: white !important; font-weight: 600 !important; }
    [data-baseweb="tag"] svg { fill: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session States
if 'students' not in st.session_state: st.session_state.students = []
if 'num_groups' not in st.session_state: st.session_state.num_groups = 3
if 'max_favs' not in st.session_state: st.session_state.max_favs = 2

st.title("👥 Pro Group Mixer by David Naughton")

# Instructions Link
instructions_url = "https://github.com/Sadsfan/Pro-Group-Maker/blob/main/instructions.md"
st.markdown(f'<a href="{instructions_url}" target="_blank"><button style="background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 20px;">📖 View Instructions</button></a>', unsafe_allow_html=True)

# --- 3. SIDEBAR: SETTINGS & RESET ---
with st.sidebar:
    st.header("⚙️ Mixing Settings")
    
    # Sidebar Summary
    if st.session_state.students:
        boys = sum(1 for s in st.session_state.students if s['Gender'] == 'M')
        girls = sum(1 for s in st.session_state.students if s['Gender'] == 'F')
        st.write(f"**Total Pupils:** {len(st.session_state.students)}")
        st.write(f"👦 Boys: {boys} | 👧 Girls: {girls}")
        st.write("---")
    
    if st.button("🔄 Reset to Defaults"):
        st.session_state.num_groups = 3
        st.session_state.max_favs = 2
        st.rerun()

    # Manage Data
    st.write("---")
    st.subheader("💾 Organise Data")
    if st.session_state.students:
        df_save = pd.DataFrame(st.session_state.students)
        csv_data = df_save.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Data to CSV", csv_data, "pupil_data.csv", "text/csv")
        
        js = json.dumps(st.session_state.students)
        st.download_button("💾 Save Configuration (.json)", js, "mixer_config.json")

    st.write("---")
    num_groups = st.number_input("Number of Groups", min_value=2, value=st.session_state.num_groups)
    
    # Ensuring max_size_limit doesn't error when empty
    limit_val = max(1, len(st.session_state.students)) if st.session_state.students else 50
    max_size_limit = st.slider("📏 Strict Group Size Limit", 1, limit_val, min(50, limit_val))
    
    max_favs_per_group = st.slider("🤝 Clique Control (Max friends per group)", 1, 5, st.session_state.max_favs)

    # Dynamic Explanation
    if max_favs_per_group == 1:
        st.info("**Mode: Spread Out.** Every pupil gets at most **one** friend. Best for behaviour management.")
    elif max_favs_per_group == 2:
        st.info("**Mode: Balanced.** Allows pairs of friends to stay together.")
    else:
        st.warning(f"**Mode: Social Clusters.** Up to **{max_favs_per_group}** friends can stay together.")

    st.write("---")
    if st.button("🗑️ Clear All Pupils", type="primary"):
        st.session_state.students = []
        if 'final_groups' in st.session_state: del st.session_state.final_groups
        st.rerun()

# --- 4. DATA ENTRY & LIMITS ---
st.subheader("🛠️ Entry Limits")
cl1, cl2 = st.columns(2)
with cl1:
    limit_select_fav = st.number_input("Max Favourites per person", 1, 10, 5)
with cl2:
    limit_select_ka = st.number_input("Max Keep-Aparts per person", 1, 10, 5)

with st.expander("📥 Step 1: Add Students", expanded=not bool(st.session_state.students)):
    template_df = pd.DataFrame(columns=[
        "Name", "Gender (M/F)", "SEND (Y/N)", "Favourites (Comma Separated)", "Keep_Apart (Comma Separated)"
    ])
    st.download_button("📄 Download CSV Template", template_df.to_csv(index=False).encode('utf-8'), "student_template.csv", "text/csv")
    
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Import CSV")
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up and st.button("Process CSV"):
            try:
                df = pd.read_csv(up).fillna("")
                df.columns = [c.split('(')[0].strip() for c in df.columns]
                for _, row in df.iterrows():
                    name = str(row.get('Name', '')).strip()
                    if name and not any(s['Name'] == name for s in st.session_state.students):
                        def pl(v): return [x.strip() for x in str(v).replace("[","").replace("]","").replace("'","").replace('"',"").split(',') if x.strip()]
                        is_send = str(row.get('SEND', '')).strip().upper() in ['Y', 'YES', 'TRUE', '1']
                        st.session_state.students.append({
                            "Name": name, 
                            "Gender": str(row.get('Gender', 'M')).strip().upper()[:1],
                            "SEND": is_send,
                            "Favourites": pl(row.get('Favourites', ''))[:limit_select_fav],
                            "Keep_Apart": pl(row.get('Keep_Apart', ''))[:limit_select_ka]
                        })
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    with c2:
        st.subheader("Manual Add")
        with st.form("manual_add", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.selectbox("Gender", ["M", "F", "Other"])
            s_en = st.checkbox("SEND Student?")
            if st.form_submit_button("Add Student") and n:
                st.session_state.students.append({"Name": n.strip(), "Gender": g[:1], "SEND": s_en, "Favourites": [], "Keep_Apart": []})
                st.rerun()

# --- 5. SEARCH & RELATIONSHIP DASHBOARD ---
if st.session_state.students:
    st.write("---")
    st.subheader("🔗 Relationship Dashboard")
    search_query = st.text_input("🔍 Search for a student...", "").lower()
    all_names = sorted([s['Name'] for s in st.session_state.students])
    
    filtered_indices = [i for i, s in enumerate(st.session_state.students) if search_query in s['Name'].lower()]
    
    if not filtered_indices:
        st.info("No matching students found.")
    else:
        edit_cols = st.columns(3)
        for count, idx in enumerate(filtered_indices):
            student = st.session_state.students[idx]
            with edit_cols[count % 3]:
                with st.container(border=True):
                    st.write(f"#### {student['Name']} {'(SEND)' if student['SEND'] else ''}")
                    st.session_state.students[idx]['SEND'] = st.toggle("SEND Status", value=student['SEND'], key=f"s_{idx}")
                    st.session_state.students[idx]['Favourites'] = st.multiselect(f"⭐ Likes: {student['Name']}", all_names, default=[f for f in student['Favourites'] if f in all_names], key=f"fav_{idx}")
                    st.session_state.students[idx]['Keep_Apart'] = st.multiselect(f"🚫 Avoids: {student['Name']}", all_names, default=[k for k in student['Keep_Apart'] if k in all_names], key=f"ka_{idx}")

# --- 6. GENERATOR LOGIC ---
if st.button("🎲 Generate Groups", type="primary"):
    import math
    if len(st.session_state.students) < num_groups:
        st.error("Not enough pupils for that many groups!")
    elif len(st.session_state.students) > (max_size_limit * num_groups):
        st.error(f"⚠️ {len(st.session_state.students)} pupils cannot fit into {num_groups} groups with a limit of {max_size_limit}.")
    else:
        students = list(st.session_state.students)
        random.shuffle(students)
        groups = [[] for _ in range(num_groups)]
        students.sort(key=lambda s: (len(s['Keep_Apart']), s['SEND']), reverse=True)

        for child in students:
            best_idx = -1
            best_score = -float('inf')
            for idx, group in enumerate(groups):
                if len(group) >= max_size_limit: continue
                names = [p['Name'] for p in group]
                score = 0
                ka_v = sum(1 for ka in child['Keep_Apart'] if ka in names) + sum(1 for m in group if child['Name'] in m['Keep_Apart'])
                score -= (ka_v * 10000)
                if child['SEND']: score -= (sum(1 for p in group if p['SEND']) * 500)
                score -= (len(group) * 100) # Stronger balance penalty
                if score > best_score: best_score, best_idx = score, idx
            
            if best_idx != -1: groups[best_idx].append(child)
            else: groups[min(range(num_groups), key=lambda i: len(groups[i]))].append(child)

        st.session_state.final_groups = groups
        st.session_state.group_names = {i: f"Group {i+1}" for i in range(num_groups)}

# --- 7. DISPLAY & EXPORT ---
if 'final_groups' in st.session_state:
    st.write("---")
    
    # 1. Edit Names
    with st.expander("🏷️ Edit Group Names"):
        for i in range(len(st.session_state.final_groups)):
            st.session_state.group_names[i] = st.text_input(
                f"Name for Group {i+1}", 
                value=st.session_state.group_names[i], key=f"gn_{i}"
            )

    # 2. Display Groups + Summary Line
    res_cols = st.columns(len(st.session_state.final_groups))
    for idx, g in enumerate(st.session_state.final_groups):
        with res_cols[idx]:
            gn = st.session_state.group_names.get(idx, f"Group {idx+1}")
            st.success(f"### {gn}")
            
            boys = sum(1 for p in g if p['Gender'] == 'M')
            girls = sum(1 for p in g if p['Gender'] == 'F')
            send_count = sum(1 for p in g if p['SEND'])
            st.caption(f"👦 {boys} | 👧 {girls} | 🧩 SEND: {send_count}")
            
            for p in g:
                gender_icon = "👦" if p['Gender'] == 'M' else "👧"
                send_marker = " 🧩" if p['SEND'] else ""
                st.write(f"• {p['Name']} {gender_icon}{send_marker}")

    # 3. Export Section
    st.write("---")
    st.subheader("📥 Export Your Groups")
    d1, d2 = st.columns(2)
    
    with d1:
        clean_data = []
        for idx, g in enumerate(st.session_state.final_groups):
            gn = st.session_state.group_names.get(idx, f"Group {idx+1}")
            for p in g:
                clean_data.append({"Group Name": gn, "Student Name": p['Name'], "Gender": p['Gender'], "SEND": "Yes" if p['SEND'] else "No"})
        excel_buffer = io.BytesIO()
        pd.DataFrame(clean_data).to_excel(excel_buffer, index=False)
        st.download_button("📊 Download Excel", excel_buffer.getvalue(), "groups.xlsx")

    with d2:
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.pagesizes import letter
        
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Classroom Group Assignments", styles['Title']), Spacer(1, 12)]
        
        num_groups = len(st.session_state.final_groups)
        max_rows = max([len(g) for g in st.session_state.final_groups], default=0)
        
       # Build Table Data
        table_data = [[st.session_state.group_names.get(i, f"Group {i+1}") for i in range(num_groups)]]
        for r in range(max_rows):
            row = []
            for g in st.session_state.final_groups:
                # Add the safety check: 'if r < len(g)'
                if r < len(g):
                    p = g[r]
                    row.append(f"{p['Name']} ({p['Gender']}{'/' + 'S' if p['SEND'] else ''})")
                else:
                    row.append("") # Add an empty cell if the group has no pupil at this row
            table_data.append(row)
        
        # Add Totals Row
        totals = ["Boys: " + str(sum(1 for p in g if p['Gender']=='M')) + " | Girls: " + str(sum(1 for p in g if p['Gender']=='F')) + " | SEND: " + str(sum(1 for p in g if p['SEND'])) for g in st.session_state.final_groups]
        table_data.append(totals)
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey), # Highlight totals row
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')
        ]))
        elements.append(t)
        doc.build(elements)
        st.download_button("📥 Download PDF Table", pdf_buffer.getvalue(), "groups.pdf")