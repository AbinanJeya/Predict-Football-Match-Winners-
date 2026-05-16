import sys
import os
import pandas as pd
import joblib
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ingestion.db_utils import read_from_db

class PredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Predictor - Mission Control")
        self.root.geometry("1100x800")
        
        # Data State
        self.full_test_df = None
        
        # Main Container
        self.main_frame = tk.Frame(self.root, bg="#f0f2f5")
        self.main_frame.pack(expand=True, fill="both")

        # --- Sidebar (Controls) ---
        self.sidebar = tk.Frame(self.main_frame, width=250, bg="#2c3e50", padx=20, pady=20)
        self.sidebar.pack(side="left", fill="y")
        
        tk.Label(self.sidebar, text="COMMANDS", fg="white", bg="#2c3e50", font=("Helvetica", 12, "bold")).pack(pady=(0, 20))
        
        self.btn_full = self.create_sidebar_button("🚀 Run Full Pipeline", self.run_full_pipeline)
        self.btn_ingest = self.create_sidebar_button("📥 Ingest New Data", lambda: self.run_script("pipelines/orchestrator.py"))
        self.btn_train = self.create_sidebar_button("🧠 Retrain Model", lambda: self.run_script("models/train.py"))
        self.btn_refresh = self.create_sidebar_button("📊 Load/Refresh Data", self.reload_all_data)
        
        tk.Label(self.sidebar, text="SYSTEM STATUS", fg="#bdc3c7", bg="#2c3e50", font=("Helvetica", 10)).pack(side="bottom", pady=5)
        self.status_circle = tk.Label(self.sidebar, text="● Ready", fg="#2ecc71", bg="#2c3e50", font=("Helvetica", 10, "bold"))
        self.status_circle.pack(side="bottom")

        # --- Right Content Area ---
        self.content = tk.Frame(self.main_frame, bg="white")
        self.content.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # Header
        self.header_label = tk.Label(self.content, text="Prediction Dashboard", font=("Helvetica", 18, "bold"), bg="white")
        self.header_label.pack(anchor="w")
        
        self.acc_label = tk.Label(self.content, text="Waiting for pipeline run...", font=("Helvetica", 11, "italic"), bg="white", fg="#e67e22")
        self.acc_label.pack(anchor="w", pady=(0, 10))

        # --- Filter Bar ---
        self.filter_frame = tk.LabelFrame(self.content, text="FILTERS", bg="white", font=("Helvetica", 9, "bold"), padx=10, pady=10)
        self.filter_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(self.filter_frame, text="Select Team:", bg="white").grid(row=0, column=0, padx=5)
        self.team_filter = ttk.Combobox(self.filter_frame, state="readonly", width=30)
        self.team_filter.grid(row=0, column=1, padx=5)
        self.team_filter.bind("<<ComboboxSelected>>", self.apply_filters)
        
        tk.Label(self.filter_frame, text="Season:", bg="white").grid(row=0, column=2, padx=(20, 5))
        self.season_filter = ttk.Combobox(self.filter_frame, state="readonly", width=15)
        self.season_filter.grid(row=0, column=3, padx=5)
        self.season_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        self.btn_reset = tk.Button(self.filter_frame, text="Reset Filters", command=self.reset_filters, bg="#ecf0f1")
        self.btn_reset.grid(row=0, column=4, padx=20)

        # --- Results Table ---
        self.table_frame = tk.Frame(self.content, bg="white")
        self.table_frame.pack(expand=True, fill="both")
        
        columns = ("Date", "Team", "Opponent", "Actual", "Predicted", "Probability", "Season")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center")
            
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.pack(side="left", expand=True, fill="both")
        self.scrollbar.pack(side="right", fill="y")
        
        self.tree.tag_configure("correct", background="#e6ffed")
        self.tree.tag_configure("incorrect", background="#ffeef0")

        # --- Console Output ---
        tk.Label(self.content, text="System Logs", font=("Helvetica", 10, "bold"), bg="white").pack(anchor="w", pady=(20, 5))
        self.console = tk.Text(self.content, height=8, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9), padx=10, pady=10)
        self.console.pack(fill="x")
        
        # NOTE: self.reload_all_data() removed from __init__ to "start wiped"
        self.log("System initialized. Click a command to start.")

    def create_sidebar_button(self, text, command):
        btn = tk.Button(self.sidebar, text=text, command=command, 
                        bg="#34495e", fg="white", relief="flat", 
                        font=("Helvetica", 10), pady=10, cursor="hand2",
                        activebackground="#1abc9c")
        btn.pack(fill="x", pady=5)
        return btn

    def log(self, message):
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")

    def run_script(self, script_path):
        self.log(f"Starting execution: {script_path}")
        self.status_circle.config(text="● Busy", fg="#f1c40f")
        
        def task():
            try:
                process = subprocess.Popen([sys.executable, script_path], 
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    self.root.after(0, lambda l=line: self.log(l.strip()))
                process.wait()
                self.root.after(0, self.on_task_complete)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        threading.Thread(target=task, daemon=True).start()

    def run_full_pipeline(self):
        self.run_script("pipelines/orchestrator.py")

    def on_task_complete(self):
        self.status_circle.config(text="● Ready", fg="#2ecc71")
        self.log("Task completed. Updating dashboard...")
        self.reload_all_data()

    def reload_all_data(self):
        self.log("Requesting data from database...")
        df, error = self.load_data_and_predict()
        if error:
            self.log(f"Error: {error}")
            return

        self.full_test_df = df
        
        # Update Filter Options
        teams = sorted(df["team"].unique().tolist())
        self.team_filter["values"] = ["All Teams"] + teams
        self.team_filter.set("All Teams")
        
        seasons = sorted(df["season"].unique().astype(str).tolist())
        self.season_filter["values"] = ["All Seasons"] + seasons
        self.season_filter.set("All Seasons")
        
        self.log("Data loaded successfully.")
        self.apply_filters()

    def reset_filters(self):
        if self.full_test_df is None: return
        self.team_filter.set("All Teams")
        self.season_filter.set("All Seasons")
        self.apply_filters()

    def apply_filters(self, event=None):
        if self.full_test_df is None: return
        
        filtered = self.full_test_df.copy()
        
        team = self.team_filter.get()
        if team != "All Teams":
            filtered = filtered[filtered["team"] == team]
            
        season = self.season_filter.get()
        if season != "All Seasons":
            filtered = filtered[filtered["season"].astype(str) == season]
            
        self.update_tree_view(filtered)

    def update_tree_view(self, df):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new
        for i, row in df.head(100).iterrows():
            actual = "WIN" if row['result'] == 'W' else "NOT WIN"
            pred = "WIN" if row['predicted_win'] == 1 else "NOT WIN"
            prob = f"{row['win_prob']:.1%}"
            tag = "correct" if (actual == pred) else "incorrect"
            self.tree.insert("", "end", values=(
                row['date'].strftime('%Y-%m-%d'), 
                row['team'], 
                row['opponent'], 
                actual, 
                pred, 
                prob,
                row['season']
            ), tags=(tag,))

        # Update Accuracy
        if not df.empty:
            correct = (df["result"] == "W") == (df["predicted_win"] == 1)
            accuracy = correct.mean()
            self.acc_label.config(text=f"Model Accuracy: {accuracy:.2%}", font=("Helvetica", 11, "bold"), fg="#2c3e50")
        else:
            self.acc_label.config(text="No data matching filters.", font=("Helvetica", 11), fg="#7f8c8d")

    def load_data_and_predict(self):
        try:
            df = read_from_db("SELECT * FROM gold_features")
            if df.empty: return None, "Database table 'gold_features' is empty."
            
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date", ascending=False)
            
            # Test split (20%)
            split_idx = int(len(df) * 0.2)
            test_df = df.iloc[:split_idx].copy()
            
            model_path = "api/model_checkpoint/latest_model.pkl"
            if not os.path.exists(model_path): return None, "Model file missing in api/model_checkpoint/"
            
            model = joblib.load(model_path)
            predictors = ["venue_code", "opp_code", "hour", "day_code", 
                          "gf_rolling", "ga_rolling", "sh_rolling", 
                          "sot_rolling", "dist_rolling", "fk_rolling", 
                          "pk_rolling", "pkatt_rolling"]
            
            test_df["predicted_win"] = model.predict(test_df[predictors])
            test_df["win_prob"] = model.predict_proba(test_df[predictors])[:, 1]
            return test_df, None
        except Exception as e:
            return None, str(e)

if __name__ == "__main__":
    root = tk.Tk()
    app = PredictorApp(root)
    root.mainloop()
