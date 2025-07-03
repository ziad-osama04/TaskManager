
# 📌 Task Manager Project

A Python-based Task Manager CLI application developed for our **Data Structures** course. This project demonstrates the practical application of various data structures, searching, and sorting algorithms, as well as email integration to automatically fetch and manage tasks.

---

## 📚 Features

- 🧠 **Data Structures Used:**
  - Hash Table (`dict`) – for storing tasks by ID
  - Priority Queue (`heapq`) – for managing task priorities
  - Stack (`list`) – for undo operations
  - Lists – for sorting and searching tasks

- 🔍 **Searching:**
  - Linear search (by task title)
  - Binary search (by task priority)

- 🔢 **Sorting:**
  - Bubble sort (by priority)
  - Selection sort (by creation date)

- 📩 **Email Integration:**
  - Fetch tasks automatically from Gmail inbox using `imaplib`
  - Extract task title, priority, and deadline from email body

- ↩️ **Undo Feature:**
  - Revert the last 10 actions (add, remove, complete)

- 📊 **Statistics:**
  - View total, completed, and pending task counts

---

## ⚙️ How to Run

1. Make sure you have Python 3 installed.
2. Install required libraries (optional, mostly standard libraries used):
3. Clone the repository:
   ```bash
   git clone https://github.com/your-username/task-manager.git
   cd task-manager
   ```
4. Run the app:
   ```bash
   python main.py
   ```

---

## 📂 Config File

On first use, the program will ask for your Gmail address and App Password (used to scan your inbox for tasks) and will create a `config.json` file.

---

## 🛠️ Example Email Format

To add a task via email, use this format:
```
Subject: Task Reminder

Body:
Task: Finish data structures assignment
Deadline: 2025-06-20
Priority: High
```

---

## 👨‍💻 Authors

- Badawy:
    - Core functionality
    - undo stack
    - Hash Table logic  
- Ahmed:
    - Priority queue logic
    - Task Management & Reporting Functions
- Karim:
    - Search algorithms(linear and binary search by priority)  
- Ziad:
    - Sorting algorithms
    - Testing & bug detection
- Yosef:
    - Email integration  
---


## 📌 Notes

- This is a CLI-based educational project meant to showcase core data structure knowledge.
- Bubble and selection sorts are used intentionally for demonstration, despite being inefficient.

---

## ✅ Future Improvements

- Add GUI using Tkinter or PyQt
- Persistent storage (save tasks to file)
- Unit testing for main functionalities

---
