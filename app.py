import streamlit as st
import pandas as pd
import random
import json
import io

st.set_page_config(page_title="Pro Group Mixer", layout="wide")

# --- 1. CSS for Visual Colors (Matches your Screenshots) ---
st.markdown("""
    <style>
    .fav-box div[data-baseweb="tag"] { background-color: #ff4b4b !important; color: white !important; }
    .ka-box div[data-baseweb="tag"] { background-color: #ff4b4b !important; color: white !important; }
    /* Note: Streamlit uses the same red for tags by default; 
       we keep them consistent with your 'Emma/Sophia' red tags */
    </style>
    """, unsafe_allow_html=True)

if 'students' not in st.session_state:
    st.session_state.students = []

st.title("👥 Pro Group Mixer by David Naughton")

# --- 2. Sidebar: Global Mixing Rules ---
with st.sidebar:
    st.header("⚙️ Mixing Settings")
    num_groups = st.number_input("Number of Groups", min_value=2, value=3)
    
    st.subheader("Group Limits")
    max_favs_per_group = st.slider("Max Favorites allowed per group", 1, 5, 2)
    allow_ka_per_group = st.slider("Max Keep-Aparts allowed per group", 0, 3, 0)
    
    st.write("---")
    st.subheader("Data Management")
    if st.session_state.students:
        js = json.dumps(st.session_state.students)
        st.download_button("💾 Save Config (.json)", js, "mixer_config.json")
    
    if st.button("🗑️ Clear All Names"):
        st.session_state.students = []
        st.rerun()

# --- 3. Entry Limits (Controls the 'Max 1' message you saw) ---
st.subheader("🛠️ Entry Limits")
col_lim1, col_lim2 = st.columns(2)
with col_lim1:
    limit_select_fav = st.number_input("Max Favorites a person can have", 1, 10, 1)
with col_lim2:
    limit_select_ka = st.number_input("Max Keep-Aparts a person can have", 1, 10, 2)

# --- 4. Data Input ---
with st.expander("📥 Step 1: Add Students", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up and st.button("Process CSV"):
            df = pd.read_csv(up)
            df.columns = df.columns.str.strip()
            def parse_csv_list(val):
                if pd.isna(val) or str(val).strip() == "": return []
                return [x.strip() for x in str(val).split(',') if x.strip()]
            for _, row in df.iterrows():
                if not any(s['Name'] == str(row['Name']).strip() for s in st.session_state.students):
                    st.session_state.students.append({
                        "Name": str(row['Name']).strip(), 
                        "Gender": str(row.get('Gender', 'M')).upper()[:1],
                        "Favorites": parse_csv_list(row.get('Favorites', ''))[:limit_select_fav],
                        "Keep_Apart": parse_csv_list(row.get('Keep_Apart', ''))[:limit_select_ka]
                    })
            st.rerun()
    with c2:
        with st.form("manual", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.selectbox("Gender", ["M", "F", "Other"])
            if st.form_submit_button("Add") and n:
                st.session_state.students.append({"Name": n, "Gender": g[:1], "Favorites": [], "Keep_Apart": []})
                st.rerun()

# --- 5. The Rules-First Sorting Engine ---
if st.button("🎲 Generate Groups (Strict Separation)"):
    if len(st.session_state.students) < num_groups:
        st.error("Not enough students!")
    else:
        students = list(st.session_state.students)
        random.shuffle(students)
        groups = [[] for _ in range(num_groups)]
        
        # Calculate hard ceiling for size balance
        max_cap = (len(students) // num_groups) + (1 if len(students) % num_groups != 0 else 0)

        # CRITICAL CHANGE: Sort by Keep_Apart count FIRST. 
        # We must place the "difficult" students while groups are empty.
        students.sort(key=lambda s: len(s['Keep_Apart']), reverse=True)

        for child in students:
            best_idx, best_score = -1, -float('inf')
            
            for idx, group in enumerate(groups):
                if len(group) >= max_cap: continue
                
                names = [p['Name'] for p in group]
                score = 0
                
                # 1. 🚫 STRICT KEEP APART PENALTY (Highest Weight)
                # We use a massive penalty (-5000) so it overrides everything else.
                ka_violations = sum(1 for ka in child['Keep_Apart'] if ka in names)
                for m in group:
                    if child['Name'] in m['Keep_Apart']: 
                        ka_violations += 1
                
                score -= (ka_violations * 5000) 
                
                # 2. ⭐ FAVORITES BONUS
                fav_in = sum(1 for f in child['Favorites'] if f in names)
                for m in group:
                    if child['Name'] in m['Favorites']: 
                        fav_in += 1
                score += (fav_in * 50)
                
                # 3. ⚖️ SIZE BALANCE (Secondary Priority)
                score -= (len(group) * 10)
                
                # 4. 👦/👧 GENDER BALANCE (Lowest Priority)
                # Reduced from 10 to 2 to make it less influential than rules.
                g_match = sum(1 for p in group if p['Gender'] == child['Gender'])
                score -= (g_match * 2) 

                if score > best_score:
                    best_score, best_idx = score, idx
            
            # If no group is "good," it will still pick the one with the least-bad score
            groups[best_idx].append(child)

        # --- 6. Results Display & Conflict Audit ---
        st.write("---")
        st.subheader("🏁 Final Groups & Audit")
        
        final_list = []
        conflicts = []
        
        res_cols = st.columns(num_groups)
        for idx, g in enumerate(groups):
            group_id = idx + 1
            group_names = [p['Name'] for p in g]
            
            with res_cols[idx]:
                st.success(f"Group {group_id}")
                m_c = sum(1 for p in g if p['Gender'] == 'M')
                f_c = sum(1 for p in g if p['Gender'] == 'F')
                st.caption(f"👦 {m_c} | 👧 {f_c} | Total: {len(g)}")
                
                for p in g:
                    st.write(f"• **{p['Name']}**")
                    
                    # Audit Keep Aparts
                    for ka in p['Keep_Apart']:
                        if ka in group_names:
                            conflicts.append(f"⚠️ **Keep Apart Violation**: {p['Name']} and {ka} are both in Group {group_id}")
                    
                    # Audit Favorites (Optional: Flag if a friend was lost)
                    has_fav = False
                    for fav in p['Favorites']:
                        if fav in group_names:
                            has_fav = True
                    if p['Favorites'] and not has_fav:
                        # We don't call this a 'violation', just a 'note'
                        pass 

                    # Prep for Excel
                    p_out = p.copy()
                    p_out['Assigned_Group'] = group_id
                    # Clean up list formatting for Excel readability
                    p_out['Favorites'] = ", ".join(p['Favorites'])
                    p_out['Keep_Apart'] = ", ".join(p['Keep_Apart'])
                    final_list.append(p_out)

        # --- Display Audit Results ---
        if conflicts:
            st.warning("### 🔍 Conflict Audit")
            for c in conflicts:
                st.write(c)
        else:
            st.balloons()
            st.success("✅ **Perfect Separation!** All 'Keep Apart' rules were respected.")

        # --- 7. Excel Export ---
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