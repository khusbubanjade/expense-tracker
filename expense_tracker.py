import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import os

# ---------- SETTINGS ----------
CSV_FILE = "expenses.csv"
categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Health", "Others"]
accounts = ["Cash", "Bank", "Credit"]
THRESHOLD = 20000  # minimum total before alerts trigger
budgets = {"Cash": 2000, "Bank": 20000, "Credit": 2000}  # Example budgets per account

# Load existing data or create new DataFrame
if os.path.exists(CSV_FILE):
    data = pd.read_csv(CSV_FILE, parse_dates=["Date"])

# ---- Fix missing columns from older CSV versions ----
    if "Account" not in data.columns:
        data["Account"] = "Cash"

    if "Category" not in data.columns:
        data["Category"] = "Others"

    if "Amount" not in data.columns:
        data["Amount"] = 0.0

    if "Description" not in data.columns:
        data["Description"] = ""
else:
    data = pd.DataFrame(columns=["Date", "Account", "Category", "Amount", "Description"])
    editing_index = None

# ---------- FUNCTIONS ----------

def save_data():
    data.to_csv(CSV_FILE, index=False)

def add_expense():
    global data
    category = category_combo.get()
    account = account_combo.get()
    amount = amount_entry.get()
    desc = desc_entry.get()
    if not category or not amount or not account:
        messagebox.showerror("Error", "Fill all fields")
        return
    try:
        amount = float(amount)
    except:
        messagebox.showerror("Error", "Amount must be a number")
        return

    new_row = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Account": account,
        "Category": category,
        "Amount": amount,
        "Description": desc
    }
    data.loc[len(data)] = new_row
    save_data()
    update_dashboard()
    category_combo.set("")
    account_combo.set("")
    amount_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)

def update_dashboard():
    filtered = get_filtered_data()

    # Update table
    for i in tree.get_children():
        tree.delete(i)

    for idx, row in filtered.iterrows():
        tree.insert("", "end", iid=idx,
            values=(row["Date"], row["Account"], row["Category"],
                    f"${row['Amount']:.2f}", row["Description"]))

    # Update summary
    total = filtered["Amount"].sum()
    avg = filtered["Amount"].mean() if len(filtered)>0 else 0
    summary_label.config(text=f"Total Spending: ${total:.2f}    Avg Expense: ${avg:.2f}")

    # Check alerts
    alerts_text.delete("1.0", tk.END)

    for acc in accounts:
        spent = filtered[filtered["Account"]==acc]["Amount"].sum()
        budget = budgets.get(acc, 0)

        if spent > THRESHOLD:
            if spent > budget:
                alerts_text.insert(tk.END,
                    f"⚠️ Overspending on {acc}: ${spent:.2f} / ${budget}\n")

                # popup alert (NEW)
                messagebox.showwarning(
                    "Overspending Alert",
                    f"You exceeded budget in {acc}\nSpent: ${spent:.2f}\nBudget: ${budget}"
                )
            else:
                alerts_text.insert(tk.END,
                    f"{acc}: ${spent:.2f} / ${budget}\n")

    update_chart(filtered)

    # Update chart
    update_chart()

def edit_row():
    global editing_index
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a row to edit")
        return

    editing_index = int(selected[0])
    row = data.loc[editing_index]

    # Load values into form
    category_combo.set(row["Category"])
    account_combo.set(row["Account"])
    amount_entry.delete(0, tk.END)
    amount_entry.insert(0, row["Amount"])
    desc_entry.delete(0, tk.END)
    desc_entry.insert(0, row.get("Description", ""))

    add_btn.config(text="Update Expense", command=update_expense)

def delete_row():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a row to delete")
        return
    idx = int(selected[0])
    data.drop(idx, inplace=True)
    data.reset_index(drop=True, inplace=True)
    save_data()
    update_dashboard()

def reset_all():
    global data
    confirm = messagebox.askyesno("Reset All", "Delete ALL expenses permanently?")
    if confirm:
        data = pd.DataFrame(columns=["Date","Account","Category","Amount","Description"])
        save_data()
        update_dashboard()

def update_chart(df=None):
    if df is None:
        df = data

    fig.clear()
    if df.empty:
        canvas.draw()
        return

    ax1 = fig.add_subplot(121)
    df.groupby("Category")["Amount"].sum().plot(kind="bar", ax=ax1, color='tomato')
    ax1.set_title("Spending by Category")
    ax1.set_ylabel("Amount ($)")

    ax2 = fig.add_subplot(122)
    df.groupby("Account")["Amount"].sum().plot(kind="bar", ax=ax2, color='skyblue')
    ax2.set_title("Spending by Account")
    ax2.set_ylabel("Amount ($)")

    fig.tight_layout()
    canvas.draw()

def update_expense():
    global data, editing_index

    if editing_index is None:
        return

    try:
        amount = float(amount_entry.get())
    except:
        messagebox.showerror("Error", "Amount must be a number")
        return

    data.loc[editing_index] = {
        "Date": data.loc[editing_index]["Date"],  # keep original date
        "Account": account_combo.get(),
        "Category": category_combo.get(),
        "Amount": amount,
        "Description": desc_entry.get()
    }

    save_data()
    update_dashboard()

    # Reset form
    category_combo.set("")
    account_combo.set("")
    amount_entry.delete(0, tk.END)
    desc_entry.delete(0, tk.END)

    editing_index = None
    add_btn.config(text="Add Expense", command=add_expense)

def export_csv():
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
    if file:
        data.to_csv(file, index=False)
        messagebox.showinfo("Export", f"CSV saved to {file}")

# ---------- GUI ----------
root = tk.Tk()
root.title("Professional Expense Tracker")
root.state("zoomed")
root.configure(bg="#121212")

# Title
tk.Label(root, text="💰 Expense Dashboard", font=("Segoe UI",24,"bold"), bg="#121212", fg="white").pack(pady=10)

# Input frame
frame = tk.Frame(root, bg="#121212")
frame.pack(pady=10)

tk.Label(frame,text="Category:",bg="#121212",fg="white").grid(row=0,column=0,padx=5)
category_combo = ttk.Combobox(frame, values=categories, state="readonly", width=18)
category_combo.grid(row=0,column=1,padx=5)

tk.Label(frame,text="Account:",bg="#121212",fg="white").grid(row=0,column=2,padx=5)
account_combo = ttk.Combobox(frame, values=accounts, state="readonly", width=12)
account_combo.grid(row=0,column=3,padx=5)

tk.Label(frame,text="Amount:",bg="#121212",fg="white").grid(row=1,column=0,padx=5)
amount_entry = tk.Entry(frame)
amount_entry.grid(row=1,column=1,padx=5)

tk.Label(frame,text="Description:",bg="#121212",fg="white").grid(row=1,column=2,padx=5)
desc_entry = tk.Entry(frame, width=25)
desc_entry.grid(row=1,column=3,padx=5)

add_btn = tk.Button(frame,text="Add Expense",command=add_expense,bg="#1f6feb",fg="white")
add_btn.grid(row=0,column=4,rowspan=2,padx=10)

# Summary
summary_label = tk.Label(root,text="Total Spending: $0.00", font=("Segoe UI",14), bg="#121212", fg="white")
summary_label.pack(pady=5)

# Month Filter
months = ["All","January","February","March","April","May","June",
          "July","August","September","October","November","December"]

month_combo = ttk.Combobox(root, values=months, state="readonly", width=15)
month_combo.set("All")
month_combo.pack(pady=5)
month_combo.bind("<<ComboboxSelected>>", lambda e: update_dashboard())

def get_filtered_data():
    if month_combo.get()=="All":
        return data
    return data[pd.to_datetime(data["Date"]).dt.strftime("%B")==month_combo.get()]

# Editable Table
tree_frame = tk.Frame(root)
tree_frame.pack(pady=10, fill="x")
cols = ("Date","Account","Category","Amount","Description")
tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
for col in cols:
    tree.heading(col,text=col)
tree.pack(fill="both",expand=True)

edit_del_frame = tk.Frame(root, bg="#121212")
edit_del_frame.pack(pady=5)
tk.Button(edit_del_frame,text="Edit Selected",command=edit_row,bg="#238636",fg="white").grid(row=0,column=0,padx=5)
tk.Button(edit_del_frame,text="Delete Selected",command=delete_row,bg="#c6538c",fg="white").grid(row=0,column=1,padx=5)
tk.Button(edit_del_frame,text="Reset All",command=reset_all,bg="#d73a49",fg="white").grid(row=0,column=2,padx=5)

# Embedded Chart
fig = plt.Figure(figsize=(10,4), dpi=100)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill="both", expand=True)

# Alerts
tk.Label(root,text="Alerts:",bg="#121212",fg="white", font=("Segoe UI",14,"bold")).pack(pady=5)
alerts_text = tk.Text(root,height=5,bg="#1f1f1f",fg="white")
alerts_text.pack(fill="x", padx=10, pady=5)

# Export buttons
export_frame = tk.Frame(root,bg="#121212")
export_frame.pack(pady=10)
tk.Button(export_frame,text="Export CSV",command=export_csv,bg="#238636",fg="white").grid(row=0,column=0,padx=10)

# ---------- Initialize ----------
update_dashboard()  
root.mainloop()