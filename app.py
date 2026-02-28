import streamlit as st
import pandas as pd
import random
import json
import io

st.set_page_config(page_title="Pro Group Mixer", layout="wide")

# --- 1. CSS: The Nuclear Option for Colors ---
st.markdown("""
    <style>
    /* 1. Target the Favorites box specifically */
    div.fav-box div[data-baseweb="tag"] {
        background-color: #28a745 !important;
        color: white !important;
    }
    
    /* 2. Target the Keep-Apart box specifically */
    div.ka-box div[data-baseweb="tag"] {
        background-color: #dc3545 !important;
        color: white !important;
    }

    /* 3. Ensure the text inside both stays white */
    div.fav-box span, div.ka-box span {
        color: white !important;
    }

    /* 4. Ensure the 'X' delete icons are white */
    div.fav-box svg, div.ka-box svg {
        fill: white !important;
    }

    /* 5. Highlight the border of the input boxes for extra clarity */
    div.fav-box div[data-baseweb="input"] {
        border: 1px solid #28a745 !important;
    }
    div.ka-box div[data-baseweb="input"] {
        border: 1px solid #dc3545 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'students' not in st.session_state:
    st.session_state.students = []

# --- 2. Title & Instructions ---
st.title("👥 Pro Group Mixer by David Naughton")

instructions_url = "https://github.com/Sadsfan/Pro-Group-Maker/blob/main/instructions.md"
st.markdown(
    f"""
    <a href="{instructions_url}" target="_blank">
        <button style="
            background-color: #007bff; color: white; padding: 10px 20px;
            border: none; border-radius: 5px; cursor: pointer;
            font-weight: bold; text-decoration: none; display: inline-block;
            margin-bottom: 20px;">
            📖 View Instructions
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- 3. Sidebar: Global Settings ---
with st.sidebar:
    st.header("⚙️ Mixing Settings")
    num_groups = st.number_input("Number of Groups", min_value=2, value=3)
    max_favs_per_group = st.slider(
        "Max Favorites allowed per group", 1, 5, 2, 
        help="This limit is per child. It ensures no group gets 'too many' successful friendship pairings."
    )
    st.write("---")
    if st.session_state.students:
        js = json.dumps(st.session_state.students)
        st.download_button("💾 Save Config (.json)", js, "mixer_config.json")
    if st.button("🗑️ Clear All Names"):
        st.session_state.students = []
        st.rerun()

# --- 4. Entry Limits ---
st.subheader("🛠️ Entry Limits")
cl1, cl2 = st.columns(2)
with cl1:
    limit_select_fav = st.number_input("Max Favorites per person", 1, 10, 5)
with cl2:
    limit_select_ka = st.number_input("Max Keep-Aparts per person", 1, 10, 5)

# --- 5. Data Input ---
with st.expander("📥 Step 1: Add Students", expanded=True):
    template_df = pd.DataFrame(columns=["Name", "Gender", "Favorites", "Keep_Apart"])
    st.download_button("📄 Download CSV Template", template_df.to_csv(index=False).encode('utf-8'), "template.csv", "text/csv")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Import CSV")
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up and st.button("Process CSV"):
            try:
                df = pd.read_csv(up).fillna("")
                for _, row in df.iterrows():
                    name = str(row['Name']).strip()
                    if not any(s['Name'] == name for s in st.session_state.students):
                        def pl(v): return [x.strip() for x in str(v).replace("[","").replace("]","").replace("'","").replace('"',"").split(',') if x.strip()]
                        st.session_state.students.append({
                            "Name": name, "Gender": str(row['Gender']).upper()[:1],
                            "Favorites": pl(row.get('Favorites', ''))[:limit_select_fav],
                            "Keep_Apart": pl(row.get('Keep_Apart', ''))[:limit_select_ka]
                        })
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    with c2:
        st.subheader("Manual Add")
        with st.form("manual_add", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.selectbox("Gender", ["M", "F", "Other"])
            if st.form_submit_button("Add Student") and n:
                st.session_state.students.append({"Name": n.strip(), "Gender": g[:1], "Favorites": [], "Keep_Apart": []})
                st.rerun()

# --- 6. Relationship Editor (The Final Color Fix) ---
if st.session_state.students:
    st.write("---")
    st.subheader("🔗 Relationship Dashboard")
    all_names = sorted([s['Name'] for s in st.session_state.students])
    edit_cols = st.columns(3)
    
    for i, student in enumerate(st.session_state.students):
        with edit_cols[i % 3]:
            with st.container(border=True):
                st.write(f"#### {student['Name']} ({student['Gender']})")
                
                # --- FAVORITES (FORCED GREEN) ---
                st.markdown(f"""
                    <style>
                    /* Target the specific unique key for this student's favorites */
                    div[data-testid="stMarkdownContainer"] + div:has(div[key="f_{i}"]) [data-baseweb="tag"] {{
                        background-color: #28a745 !important;
                    }}
                    /* Fallback for the wrapper */
                    .fav-{i} [data-baseweb="tag"] {{
                        background-color: #28a745 !important;
                        color: white !important;
                    }}
                    </style>
                    <div class="fav-{i}">
                """, unsafe_allow_html=True)
                
                st.session_state.students[i]['Favorites'] = st.multiselect(
                    f"⭐ Likes: {student['Name']}", 
                    all_names, 
                    default=[f for f in student['Favorites'] if f in all_names], 
                    key=f"f_{i}", 
                    max_selections=limit_select_fav
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- KEEP APARTS (FORCED RED) ---
                st.markdown(f"""
                    <style>
                    .ka-{i} [data-baseweb="tag"] {{
                        background-color: #dc3545 !important;
                        color: white !important;
                    }}
                    </style>
                    <div class="ka-{i}">
                """, unsafe_allow_html=True)
                
                st.session_state.students[i]['Keep_Apart'] = st.multiselect(
                    f"🚫 Avoids: {student['Name']}", 
                    all_names, 
                    default=[k for k in student['Keep_Apart'] if k in all_names], 
                    key=f"k_{i}", 
                    max_selections=limit_select_ka
                )
                st.markdown('</div>', unsafe_allow_html=True)

# --- 7. Sorting Engine ---
if st.button("🎲 Generate Groups"):
    if len(st.session_state.students) < num_groups:
        st.error("Not enough students!")
    else:
        students = list(st.session_state.students)
        random.shuffle(students)
        groups = [[] for _ in range(num_groups)]
        max_cap = (len(students) // num_groups) + (1 if len(students) % num_groups != 0 else 0)
        students.sort(key=lambda s: len(s['Keep_Apart']), reverse=True)

        for child in students:
            best_idx, best_score = -1, -float('inf')
            for idx, group in enumerate(groups):
                if len(group) >= max_cap: continue
                names = [p['Name'] for p in group]
                score = 0
                ka_v = sum(1 for ka in child['Keep_Apart'] if ka in names) + sum(1 for m in group if child['Name'] in m['Keep_Apart'])
                score -= (ka_v * 10000)
                fav_v = sum(1 for f in child['Favorites'] if f in names) + sum(1 for m in group if child['Name'] in m['Favorites'])
                score += (fav_v * 100) if fav_v <= max_favs_per_group else -500
                score -= (len(group) * 20) + (sum(1 for p in group if p['Gender'] == child['Gender']) * 5)
                if score > best_score: best_score, best_idx = score, idx
            groups[best_idx].append(child)

        # --- 8. Results ---
        st.write("---")
        final_list, conflicts, res_cols = [], [], st.columns(num_groups)
        for idx, g in enumerate(groups):
            with res_cols[idx]:
                st.success(f"Group {idx+1}")
                st.caption(f"👦 {sum(1 for p in g if p['Gender']=='M')} | 👧 {sum(1 for p in g if p['Gender']=='F')}")
                for p in g:
                    st.write(f"• {p['Name']}")
                    for ka in p['Keep_Apart']:
                        if ka in [m['Name'] for m in g]: conflicts.append(f"⚠️ {p['Name']} & {ka} (G{idx+1})")
                    p_out = p.copy(); p_out['Group'] = idx+1
                    final_list.append(p_out)
        if conflicts:
            st.warning("### 🔍 Conflicts")
            for c in set(conflicts): st.write(c)
        else: st.balloons()
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(final_list).to_excel(writer, index=False)
        st.download_button("📊 Download Excel", buffer.getvalue(), "groups.xlsx")