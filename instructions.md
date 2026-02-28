# 🚀 Pro Group Mixer: User Guide & How It Works

Welcome to the Pro Group Mixer! This tool is designed to take the headache out of classroom sorting by balancing gender and respecting social dynamics.

---

## 🛠 Part 1: How to Use the App (Step-by-Step)

### 1. Add Your Students
* **The CSV Way (Fastest):** Click **"Download CSV Template"** at the top of the app. Open it in Excel, fill in your names and genders (M/F), and save it. Upload that file into the **"Upload CSV"** box and click **"Process CSV."**
* **The Manual Way:** Use the **"Manual Add"** form to type names and select genders one by one.

### 2. Define Relationships
Once your students appear in the **Relationship Dashboard**:
* **⭐ Likes:** Select the students this person *wants* to be with. The app treats these as "bonuses" to aim for.
* **🚫 Avoids:** Select the students this person *must not* be with. The app treats these as "deal-breakers."

### 3. Configure Your Mix
On the left sidebar, set your **Number of Groups**.
* **Max Favourites per group:** Use this slider to prevent "super-cliques." If set to 1, the app tries to give everyone *one* friend but spreads the rest of the friend group out to other tables.

### 4. Generate & Export
Click **"Generate Groups."**
* **Conflict Audit:** If the app displays a warning at the bottom, it means a "Keep Apart" rule was mathematically impossible to follow.
* **Download:** If you are happy with the results, click **"Download Excel"** to save your final list.

---

## 🧠 Part 2: How the "Brain" Works (The Logic)

The mixer doesn't just "shuffle" names; it uses a **Weighted Priority Algorithm** to find the best possible fit for every student.

### The Scoring System
Every time you click generate, the "Brain" looks at every available group and calculates a score for a student based on these rules:

| Rule | Impact on Score | Purpose |
| :--- | :--- | :--- |
| **Keep Apart Violation** | **-10,000 points** | Avoids these pairings at almost any cost. |
| **Favorite Found** | **+100 points** | Tries to keep friends together where possible. |
| **Group Size** | **-20 points** | Ensures groups stay even (e.g., no groups of 2 vs groups of 6). |
| **Gender Balance** | **-5 points** | Subtracts points for every same-gender student already in the group to encourage a mix. |



### The Placement Process
1.  **Constraint First:** The app identifies students with the most "Avoid" rules and places them first, as they are the hardest to fit.
2.  **Best Fit:** For every other student, the app calculates the scores for all groups and places the student in the group with the **highest total score**.
