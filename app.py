import streamlit as st
import pandas as pd
import random
import json
import io

st.set_page_config(page_title="Pro Group Mixer", layout="wide")

# --- 1. CSS: Targeted Label Styling ---
# This targets the container based on the emoji in the label
st.markdown("""
    <style>
    /* Target Favorites by the Star Emoji */
    div[data-testid="stWidgetLabel"]:contains("⭐") + div [data-baseweb="tag"] {
        background-color: #28a745 !important;
    }
    /* Target Keep-Aparts by the Prohibit Emoji */
    div[data-testid="stWidgetLabel"]:contains("🚫") + div [data-baseweb="tag"] {
        background-color: #dc3545 !important;
    }
    /* Global Tag Fixes */
    [data-baseweb="tag"] span { color: white !important; font-weight: 600 !important; }
    [data-baseweb="tag"] svg { fill: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'students' not in st.session_state:
    st.session_state.students = []

# --- 2. Header ---
st.title("👥 Pro Group Mixer by David Naughton")

instructions_url = "https://github.com/Sadsfan/Pro-Group-Maker/blob/main/instructions.md"
st.markdown(f'<a href="{instructions_url}" target="_blank"><button style="background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 20px;">📖 View Instructions</button></a>', unsafe_allow_html=True)

# --- 3. Sidebar ---
with st.sidebar:
    st.header("⚙️ Mixing Settings")
    num_groups = st.number_input("Number of Groups", min_value=2, value=3)
    max_favs_per_group = st.slider("Max Favorites per group (per child)", 1, 5, 2)
    st.write("---")
    if st.session_state.students:
        js = json.dumps(st.session_state.students)
        st.download_button("💾 Save Config (.json)", js, "mixer_config.json")
    if st.button("🗑️ Clear All Names"):
        st.session_state.students = []
        st.rerun()

# --- 4. Limits & Input ---
st.subheader("🛠️ Entry Limits")
cl1, cl2 = st.columns(2)
with cl1:
    limit_select_fav = st.number_input("Max Favorites per person", 1, 10, 5)
with cl2:
    limit_select_ka = st.number_input("Max Keep-Aparts per person", 1, 10, 5)

with st.expander("📥 Step 1: Add Students", expanded=False):
    template_df = pd.DataFrame(columns=["Name", "Gender", "Favorites", "Keep_Apart"])
    st.download_button("📄 CSV Template", template_df.to_csv(index=False).encode('utf-8'), "template.csv", "text/csv")
    
    c1, c2 = st.columns(2)
    with c1:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up and st.button("Process CSV"):
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
    with c2:
        with st.form("manual_add", clear_on_submit=True):
            n = st.text_input("Name")
            g = st.selectbox("Gender", ["M", "F", "Other"])
            if st.form_submit_button("Add Student") and n:
                st.session_state.students.append({"Name": n.strip(), "Gender": g[:1], "Favorites": [], "Keep_Apart": []})
                st.rerun()

# --- 5. Relationship Editor ---
if st.session_state.students:
    st.write("---")
    st.info("ℹ️ Note: Due to system settings, 'Likes' and 'Avoids' may both appear in red, but rest assured the app knows the difference!")
    st.subheader("🔗 Relationship Dashboard")
    all_names = sorted([s['Name'] for s in st.session_state.students])
    edit_cols = st.columns(3)
    
    for i, student in enumerate(st.session_state.students):
        with edit_cols[i % 3]:
            with st.container(border=True):
                st.write(f"#### {student['Name']} ({student['Gender']})")
                
                # IMPORTANT: Use the exact emojis in the labels for the CSS to pick up
                st.session_state.students[i]['Favorites'] = st.multiselect(
                    f"⭐ Likes: {student['Name']}", 
                    all_names, 
                    default=[f for f in student['Favorites'] if f in all_names], 
                    key=f"fav_{i}",
                    max_selections=limit_select_fav
                )
                
                st.session_state.students[i]['Keep_Apart'] = st.multiselect(
                    f"🚫 Avoids: {student['Name']}", 
                    all_names, 
                    default=[k for k in student['Keep_Apart'] if k in all_names], 
                    key=f"ka_{i}",
                    max_selections=limit_select_ka
                )

# --- 6. Generator ---
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