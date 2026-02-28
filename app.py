import streamlit as st
import pandas as pd
import random
import json
import io

st.set_page_config(page_title="Pro Group Mixer", layout="wide")

# --- 1. CSS for Visual Colors ---
st.markdown("""
    <style>
    .fav-box div[data-baseweb="tag"] { background-color: #28a745 !important; color: white !important; }
    .ka-box div[data-baseweb="tag"] { background-color: #dc3545 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'students' not in st.session_state:
    st.session_state.students = []

st.title("👥 Pro Group Mixer")

# --- 2. Sidebar: Global Settings ---
with st.sidebar:
    st.header("⚙️ Mixing Settings")
    num_groups = st.number_input("Number of Groups", min_value=2, value=3)
    max_favs_per_group = st.slider("Max Favourites allowed per group", 1, 5, 2)
    
    st.write("---")
    if st.session_state.students:
        js = json.dumps(st.session_state.students)
        st.download_button("💾 Save Config (.json)", js, "mixer_config.json")
    
    if st.button("🗑️ Clear All Names"):
        st.session_state.students = []
        st.rerun()

# --- 3. Entry Limits ---
st.subheader("🛠️ Entry Limits")
col_lim1, col_lim2 = st.columns(2)
with col_lim1:
    limit_select_fav = st.number_input("Max Favourites a person can have", 1, 10, 5)
with col_lim2:
    limit_select_ka = st.number_input("Max Keep-Aparts a person can have", 1, 10, 5)

# --- 4. Data Input & Template ---
with st.expander("📥 Step 1: Add Students", expanded=True):
    st.info("💡 Download the template below to ensure your CSV matches the required format.")
    
    # Generate CSV Template
    template_df = pd.DataFrame(columns=["Name", "Gender", "Favourites", "Keep_Apart"])
    template_csv = template_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Download CSV Template",
        data=template_csv,
        file_name="student_template.csv",
        mime="text/csv",
    )
    
    st.write("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Import CSV")
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up and st.button("Process CSV"):
            try:
                df = pd.read_csv(up)
                df.columns = df.columns.str.strip()
                
                def parse_csv_list(val):
                    if pd.isna(val) or str(val).strip() == "": return []
                    raw = str(val).replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                    return [x.strip() for x in raw.split(',') if x.strip()]

                for _, row in df.iterrows():
                    name_val = str(row['Name']).strip()
                    if not any(s['Name'] == name_val for s in st.session_state.students):
                        st.session_state.students.append({
                            "Name": name_val, 
                            "Gender": str(row.get('Gender', 'M')).upper()[:1],
                            "Favourites": parse_csv_list(row.get('Favourites', ''))[:limit_select_fav],
                            "Keep_Apart": parse_csv_list(row.get('Keep_Apart', ''))[:limit_select_ka]
                        })
                st.success("CSV Processed!")
                st.rerun()
            except Exception as e:
                st.error(f"Processing Error: {e}")

    with c2:
        st.subheader("Manual Add")
        with st.form("manual_add_form", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.selectbox("Gender", ["M", "F", "Other"])
            if st.form_submit_button("Add Student"):
                if n and not any(s['Name'] == n.strip() for s in st.session_state.students):
                    st.session_state.students.append({
                        "Name": n.strip(), 
                        "Gender": g[:1], 
                        "Favourites": [], 
                        "Keep_Apart": []
                    })
                    st.rerun()

# --- 5. Relationship Editor ---
if st.session_state.students:
    st.write("---")
    st.subheader("🔗 Relationship Dashboard")
    all_names = sorted([s['Name'] for s in st.session_state.students])
    
    edit_cols = st.columns(3)
    for i, student in enumerate(st.session_state.students):
        with edit_cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{student['Name']}** ({student['Gender']})")
                
                # Favourites
                st.markdown("<div class='fav-box'>", unsafe_allow_html=True)
                st.session_state.students[i]['Favourites'] = st.multiselect(
                    f"⭐ Likes (Max {limit_select_fav})", all_names, 
                    default=[f for f in student['Favourites'] if f in all_names], 
                    key=f"f_{student['Name']}_{i}", max_selections=limit_select_fav
                )
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Keep Aparts
                st.markdown("<div class='ka-box'>", unsafe_allow_html=True)
                st.session_state.students[i]['Keep_Apart'] = st.multiselect(
                    f"🚫 Avoids (Max {limit_select_ka})", all_names, 
                    default=[k for k in student['Keep_Apart'] if k in all_names], 
                    key=f"k_{student['Name']}_{i}", max_selections=limit_select_ka
                )
                st.markdown("</div>", unsafe_allow_html=True)

# --- 6. Sorting Engine (Priority: Keep Aparts) ---
if st.button("🎲 Generate Groups (Strict Separation)"):
    if len(st.session_state.students) < num_groups:
        st.error("Not enough students!")
    else:
        students = list(st.session_state.students)
        random.shuffle(students)
        groups = [[] for _ in range(num_groups)]
        max_cap = (len(students) // num_groups) + (1 if len(students) % num_groups != 0 else 0)

        # Place students with most constraints first
        students.sort(key=lambda s: len(s['Keep_Apart']), reverse=True)

        for child in students:
            best_idx, best_score = -1, -float('inf')
            for idx, group in enumerate(groups):
                if len(group) >= max_cap: continue
                
                names_in_group = [p['Name'] for p in group]
                score = 0
                
                # Penalty: Keep Aparts (Strict)
                ka_violations = sum(1 for ka in child['Keep_Apart'] if ka in names_in_group)
                for m in group:
                    if child['Name'] in m['Keep_Apart']: ka_violations += 1
                score -= (ka_violations * 10000) 
                
                # Bonus: Favourites
                fav_in = sum(1 for f in child['Favourites'] if f in names_in_group)
                for m in group:
                    if child['Name'] in m['Favourites']: fav_in += 1
                
                if fav_in > max_favs_per_group:
                    score -= 500
                else:
                    score += (fav_in * 100)
                
                # Tie-breakers: Size and Gender
                score -= (len(group) * 20)
                score -= (sum(1 for p in group if p['Gender'] == child['Gender']) * 5)

                if score > best_score:
                    best_score, best_idx = score, idx
            groups[best_idx].append(child)

        # --- 7. Results & Audit ---
        st.write("---")
        final_list = []
        conflicts = []
        res_cols = st.columns(num_groups)
        
        for idx, g in enumerate(groups):
            group_id = idx + 1
            group_names = [p['Name'] for p in g]
            with res_cols[idx]:
                st.success(f"Group {group_id}")
                st.caption(f"👦 {sum(1 for p in g if p['Gender']=='M')} | 👧 {sum(1 for p in g if p['Gender']=='F')}")
                for p in g:
                    st.write(f"• **{p['Name']}**")
                    # Check for conflicts
                    for ka in p['Keep_Apart']:
                        if ka in group_names:
                            conflicts.append(f"⚠️ {p['Name']} & {ka} (Group {group_id})")
                    
                    # Prepare for Excel
                    p_out = p.copy()
                    p_out['Assigned_Group'] = group_id
                    p_out['Favourites'] = ", ".join(p['Favourites'])
                    p_out['Keep_Apart'] = ", ".join(p['Keep_Apart'])
                    final_list.append(p_out)

        if conflicts:
            st.warning("### 🔍 Keep Apart Conflicts")
            for c in set(conflicts):
                st.write(c)
        else:
            st.balloons()
            st.success("✅ Perfect separation achieved!")

        # --- 8. Excel Export ---
        df_results = pd.DataFrame(final_list)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_results.to_excel(writer, index=False, sheet_name='Groups')
        
        st.download_button(
            label="📊 Download Groups as Excel",
            data=buffer.getvalue(),
            file_name="mixed_groups.xlsx",
            mime="application/vnd.ms-excel"
        )