# 📖 Pro Group Mixer Instructions

Welcome to the Pro Group Mixer! This tool is designed to create balanced student groups while strictly respecting social dynamics.

## 🛠 Step 1: Data Input
You can add students in two ways:
* **CSV Import**: Use the "Download CSV Template" on the main page to see the required format. The headers must be `Name`, `Gender`, `Favorites`, and `Keep_Apart`.
* **Manual Add**: Use the form to add students one by one.

## 🔗 Step 2: Setting Relationships
Once students are added, you will see a card for each person:
* **⭐ Favorites (Green)**: These are students this person *wants* to be with.
* **🚫 Keep Apart (Red)**: These are students this person *should not* be with.

## ⚙️ Step 3: Mixing Settings
* **Number of Groups**: How many groups you want to create.
* **Max Favorites per Group**: Limits how many "friends" can clump together.
* **Entry Limits**: Controls how many names you can select per person in the dashboard.

## 🎲 Step 4: Generation & Audit
When you click **Generate Groups**, the engine prioritizes **Keep Aparts** above all else. 
* If a "Keep Apart" rule is broken due to mathematical impossibility, it will appear in the **Conflict Audit** at the bottom.
* You can download the final results as an **Excel** file for your records.
