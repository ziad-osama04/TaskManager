import heapq
import imaplib
import email
from datetime import datetime, timedelta
import re
from email.header import decode_header
import json

class Task:
    def __init__(self, task_id, title, priority=1):
        self.task_id = task_id
        self.title = title
        self.priority = priority
        self.completed = False
        self.created_at = datetime.now()

    def __lt__(self, other):
        return self.priority > other.priority


class TaskManager:
    def __init__(self):
        # Hash Table: store all tasks {task_id: Task}
        self.tasks = {}

        # Priority Queue: for getting the highest priority tasks
        self.priority_queue = []

        # Stack: for undo operations
        self.history = []
        
        self.load_credentials()


#--------------------------------------------------------------------------------------


#                                EMAIL PART(YOSEF)

        
    def load_credentials(self):
        try:
            with open('config.json','r') as file:
                config = json.load(file)
                self.email_address = config['email']
                self.app_password  = config['app_password']
        except FileNotFoundError:
            print("Config file not found. Creating new one...")
            self.create_config_file()

    def create_config_file(self):
            print("\nPlease enter your Gmail credentials")
            self.email_address = input("Gmail address: ")
            self.app_password = input("App Password: ")

            config ={
                    'email' : self.email_address,
                    'app_password' : self.app_password
                }
            with open('config.json', 'w') as file:
                json.dump(config, file)
                print("Config file created successfully!")
        
    def connect_to_email(self):
        try:
            imap_connection = imaplib.IMAP4_SSL("imap.gmail.com")
            imap_connection.login(self.email_address, self.app_password)
            return imap_connection,True
        except Exception as Error:
            print(f"Connection error: {str(Error)}")
            return None, False
        
    def scan_emails_for_tasks(self, days_back=7):
        print("\nScanning emails for tasks...")
        imap_connection, success = self.connect_to_email()
        
        if not success:
            return []

        tasks_found = []
        try:
            imap_connection.select('INBOX')
            
            date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            _, messages = imap_connection.search(None, f'(SINCE "{date}")')

            for msg_id in messages[0].split():
                try:
                    _, msg_data = imap_connection.fetch(msg_id, '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    subject = self.decode_email_subject(email_message['subject'])
                    content = self.get_email_content(email_message)
                    task = self.extract_task_info(content, subject)
                    if task:
                        tasks_found.append(task)
                        print(f"Found task: {task['description'][:50]}...")
                
                except Exception as e:
                    print(f"Error processing email: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error scanning emails: {str(e)}")
        finally:
            try:
                imap_connection.close()
                imap_connection.logout()
            except:
                pass
            
        return tasks_found

    def get_email_content(self, email_message):
            content = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        except:
                            continue
            else:
                try:
                    content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            return content
    
    def decode_email_subject(self, subject):
        if not subject:
            return ""
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_subject += part.decode(encoding if encoding else 'utf-8', errors='ignore')
            else:
                decoded_subject += str(part)
        return decoded_subject
    
    def extract_task_info(self, content, subject):
        # Task patterns
        task_patterns = [
            r"Task:\s*(.*?)(?=\n|$)",
            r"TODO:\s*(.*?)(?=\n|$)",
            r"Action item:\s*(.*?)(?=\n|$)"
        ]
        
        # Try to find task description
        task_desc = None
        for pattern in task_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                task_desc = match.group(1).strip()
                break
        
        # If no task pattern found, use subject
        if not task_desc:
            task_desc = subject

        if task_desc:
            # Look for deadline
            deadline_match = re.search(r"Deadline:\s*(.*?)(?=\n|$)", content, re.IGNORECASE)
            deadline = deadline_match.group(1).strip() if deadline_match else None

            # Look for priority
            priority_match = re.search(r"Priority:\s*(.*?)(?=\n|$)", content, re.IGNORECASE)
            priority = priority_match.group(1).strip() if priority_match else "Normal"
            priority_map = {
           'HIGH': 5,
           'MEDIUM': 3,
           'NORMAL': 2,
           'LOW': 1
       }
            

            return {
                'description': task_desc,
                'deadline': deadline,
                'priority': priority_map.get(str(priority).upper(), 2),
                'created_date': datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        
        return None



        
    # --------------------------------------------------------------------------

    #          HASH INCLUDED HERE
    def add_task(self, task_id, title, priority=1):  # Time Complexity O(1), Space Complexity O(1)
        """
        **BADAWY (ME)
        - Create new Task object
        - Store in tasks dictionary
        - Add to priority_queue using heapq.heappush()
        - Save operation to history stack: ("add", task_id)
        """
        if task_id in self.tasks.keys():
            return print("task-id is already in use, task was not added")
        task = Task(task_id, title, priority)
        self.tasks[task_id] = task
        heapq.heappush(self.priority_queue, (-task.priority, task_id))  # Using min-heap format
        self._save_to_history("add", task_id)

    def get_task(self, task_id):  # O(1) for both space and time
        """
         **BADAWY (ME)
        - Return task from tasks dictionary
        - Return None if task doesn't exist
        """
        return self.tasks.get(task_id, None)

    def remove_task(self, task_id):  # O(1) for both space and time
        """
         **BADAWY (ME)
        - Remove task from tasks dictionary
        - Save operation to history: ("remove", task_id, task_copy)
        - Return True if removed, False if not found
        """
        if task_id in self.tasks:
            task_copy = self.tasks[task_id]
            del self.tasks[task_id]
            self._save_to_history("remove", (task_id, task_copy))
            return True
        return False

    # -------------------------------------------------------------------------------------

    #                        PRIORITY QUEUE INCLUDED HERE

    def get_next_task(self):  # Time complexity O(n log n) and space complexity O(n)
        """
        AHMED
        - Use heapq.heappop() to get highest priority task
        - Skip tasks that were deleted (check if task_id still in self.tasks)
        - Skip completed tasks
        - Return the task object or None if no tasks available
        """
        temp_heap = self.priority_queue.copy()
        heapq.heapify(temp_heap)
        for i in range(len(temp_heap)):
            priority, next_task_id = heapq.heappop(temp_heap)
            if next_task_id in self.tasks:
                next_task = self.tasks[next_task_id]
                if not next_task.completed:
                    return next_task
            else:
                continue
        return None

    def get_top_3_tasks(self):  # Time complexity O(n log n) and space complexity O(n)
        """
        AHMED
        - Return list of top 3 highest priority incomplete tasks
        - Don't remove them from queue, just peek
        - Use temporary list and heapq operations
        """
        temp_heap = self.priority_queue.copy()
        heapq.heapify(temp_heap)
        top3 = []
        k = 0
        for i in range(len(temp_heap)):
            if k == 3:
                break
            priority, top_task_id = heapq.heappop(temp_heap)
            if top_task_id in self.tasks:
                top_task = self.tasks[top_task_id]
                if not top_task.completed:
                    top3.append(top_task)
                    k += 1
            else:
                continue
        if k < 3:
            print(f"Only found {k} incomplete Tasks")
        return top3

    # -------------------------------------------------------------------------------------

    #                           STACK INCLUDED HERE

    def undo(self):  # O(1) for both space and time
        """
            BADAWY: Implement this
            - Pop last operation from history stack
            - If operation was "add": remove the task
            - If operation was "remove": add the task back
            - If operation was "complete": mark as incomplete
            - Return True if undo successful, False if no history
            """
        if not self.history:
            return False
        last_operation = self.history.pop()
        if last_operation[0] == "add":
            task_id = last_operation[1]
            self.tasks.pop(task_id, None)
            # Also remove it from priority_queue
            self.priority_queue = [
                item for item in self.priority_queue if item[1] != task_id
            ]
            heapq.heapify(self.priority_queue)
            return True
        elif last_operation[0] == "remove":
            task_id, task = last_operation[1]
            self.tasks[task_id] = task
            heapq.heappush(self.priority_queue, (-task.priority, task_id))
            return True
        elif last_operation[0] == "complete":
            task_id = last_operation[1]
            if task_id in self.tasks:
                self.tasks[task_id].completed = False
                return True
        return False

    def _save_to_history(self, operation, data):  # O(1) for both space and time
        """
            BADAWY: Implement this helper
            - Push (operation, data) to history stack
            - Keep only last 10 operations (remove old ones)
            """
        self.history.append((operation, data))
        if len(self.history) > 10:
            self.history.pop(0)

    # --------------------------------------------------------------------------------

    #                     SEARCHING METHODS

    def linear_search(self, title):  # space complexity O(n) Worst case all match the search term           # time complexity O(n)  , n = number of tasks
        """
       KARIM
        - Search through all tasks in tasks
        - Return list of tasks where title contains the search term
        - Use simple string matching (case insensitive)<-----######
        """
        resultsOfSearch = []  # List of tasks where title contains the search term
        searchTerm = title.lower()  # convert the title of the search term to lower case for (case insensitive)
        for task in self.tasks.values():
            if searchTerm in task.title.lower():  # check if the search term equals the task's title
                resultsOfSearch.append(task)

        return resultsOfSearch

    def binary_search_by_priority(self, target_priority):  # time complexity O(n log n)     # space complexity  O(n)
        """
        KARIM
        - Get all tasks as a list
        - Sort by priority using sorted()
        - Use binary search to find tasks with target_priority
        - Return list of matching tasks
        """
        tasks_sorted = sorted(self.tasks.values(), key=lambda task: task.priority)

        low = 0
        high = len(tasks_sorted) - 1
        result_index = -1

        while low <= high:
            mid = (low + high) // 2
            mid_Priority = tasks_sorted[mid].priority
            if mid_Priority == target_priority:
                result_index = mid
                break
            elif mid_Priority < target_priority:
                low = mid + 1
            else:
                high = mid - 1

        if result_index == -1:
            return []

        results = [tasks_sorted[result_index]]

        i = result_index - 1
        while i >= 0 and tasks_sorted[i].priority == target_priority:
            results.insert(0, tasks_sorted[i])
            i -= 1

        i = result_index + 1
        while i < len(tasks_sorted) and tasks_sorted[i].priority == target_priority:
            results.append(tasks_sorted[i])
            i += 1

        return results

    # -----------------------------------------------------------------------------

    #                          SORTING

    def sort_by_priority(self):
        """
            ZIAD
            - Get all tasks from tasks
            - Sort using bubble sort algorithm
            - Return sorted list (highest priority first)
            - compare between each two adj element until the lowest priority get at the end of list
            """
        task_list = list(self.tasks.values())
        n = len(task_list)
        # Bubble sort: Time Complexity O(n^2)
        for i in range(n):
            for j in range(0, n - i - 1):
                if task_list[j].priority < task_list[j + 1].priority:
                    task_list[j], task_list[j + 1] = task_list[j + 1], task_list[j]
        return task_list

    def sort_by_date(self):
        """
        ZIAD
        - Get all tasks from tasks
        - Sort by created_at using selection sort
        - Return sorted list (newest first)
        - newest then newer then older then oldest
        - day 9-->4-->3-->2
        """
        task_list = list(self.tasks.values())
        n = len(task_list)
        # selection sort: Time Complexity O(n^2)
        for i in range(n):
            max_idx = i
            for j in range(i + 1, n):
                if task_list[j].created_at > task_list[max_idx].created_at:
                    max_idx = j
            task_list[i], task_list[max_idx] = task_list[max_idx], task_list[i]

        return task_list

    # ----------------------------------------------------------------------------

    #                         OPTIONAL METHODS

    def complete_task(self,task_id):  # Time complexity O(1) space complexity O(1)
        """
            - Mark task as completed
            - Save to history: ("complete", task_id)
            - Return True if successful, False if task not found
            """
        if task_id in self.tasks:
            current_task = self.tasks[task_id]
            current_task.completed = True
            self._save_to_history("complete", task_id)
            return True
        else:
            return False

    def get_all_tasks(self):  # Time complexity O(n) space complexity O(n)
        """
            - Return list of all tasks from self.tasks
        """
        tasks = list(self.tasks.values())
        formatted_tasks = tasks.copy()

        for i in range(len(tasks)):
            formatted_tasks[i] = f"{tasks[i].task_id}: {tasks[i].title}, Priority: {tasks[i].priority}, Completed: {tasks[i].completed}"
        return formatted_tasks

    def get_stats(self):  # Time complexity O(n) space complexity O(1)
        """
            - Return dictionary with:
            - "total": total number of tasks
            - "completed": number of completed tasks
            - "pending": number of pending tasks
         """
        output = {"total": 0, "completed": 0, "pending": 0}
        list_of_statuses = [0, 0, 0]
        # The first index is for the total and the second is for the completed and the third is for the pending

        for task in self.tasks.values():
            if task.completed:
                list_of_statuses[1] += 1
            else:
                list_of_statuses[2] += 1

            list_of_statuses[0] += 1
        i = 0
        for key, _ in output.items():
            if i < 3:
                output[key] = list_of_statuses[i]
                i += 1
        return output

    # -------------------------------------------------------------------

if __name__ == "__main__":
    tm = TaskManager()

    while True:
        print("\n--- Task Manager Menu ---")
        print("1. Add Task")
        print("2. Remove Task")
        print("3. Complete Task")
        print("4. View All Tasks")
        print("5. View Next Task (by priority)")
        print("6. View Top 3 Tasks (by priority)")
        print("7. Search Task by Title")
        print("8. Search Task by Priority")
        print("9. Sort Tasks by Priority")
        print("10. Sort Tasks by Date")
        print("11. Undo Last Action")
        print("12. View Stats")
        print("13. Import Tasks from Email")
        print("14. Update Email config")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()
        
        try:
            if choice == "1":
                try:
                    task_id = input("Enter Task ID: ")
                    int(task_id)  # Validate task_id is numeric
                    title = input("Enter Task Title: ")
                    while True:
                        try:
                            priority = int(input("Enter Priority (1-5): "))
                            if 1 <= priority <= 5:
                                break
                            print("Please enter a priority between 1 and 5 inclusive")
                        except ValueError:
                            print("Priority must be a number between 1 and 5")
                    tm.add_task(task_id, title, priority)
                    print("Task added successfully!")
                except ValueError:
                    print("Task ID must be a number")
                    continue

            elif choice == "2":
                try:
                    task_id = input("Enter Task ID to remove: ")
                    int(task_id)  
                    if tm.remove_task(task_id):
                        print("Task removed.")
                    else:
                        print("Task not found.")
                except ValueError:
                    print("Task ID must be a number")

            elif choice == "3":
                try:
                    task_id = input("Enter Task ID to mark as complete: ")
                    int(task_id)  
                    if tm.complete_task(task_id):
                        print("Task marked as completed.")
                    else:
                        print("Task not found.")
                except ValueError:
                    print("Task ID must be a number")

            elif choice == "4":
                print("\n--- All Tasks ---")
                tasks = tm.get_all_tasks()
                if tasks:
                    for t in tasks:
                        print(t)
                else:
                    print("No tasks found.")

            elif choice == "5":
                next_task = tm.get_next_task()
                if next_task:
                    print(f"Next task: {next_task.title}")
                else:
                    print("No available tasks.")

            elif choice == "6":
                top_tasks = tm.get_top_3_tasks()
                if top_tasks:
                    print("Top 3 Tasks:")
                    for t in top_tasks:
                        print(f"{t.task_id}: {t.title} (Priority: {t.priority})")
                else:
                    print("No tasks available.")

            elif choice == "7":
                title = input("Enter title to search: ")
                results = tm.linear_search(title)
                if results:
                    for task in results:
                        print(f"{task.task_id}: {task.title} (Priority: {task.priority})")
                else:
                    print("No matching tasks found.")

            elif choice == "8":
                try:
                    p = int(input("Enter priority to search: "))
                    results = tm.binary_search_by_priority(p)
                    if results:
                        for task in results:
                            print(f"{task.task_id}: {task.title} (Priority: {task.priority})")
                    else:
                        print("No tasks with that priority.")
                except ValueError:
                    print("Priority must be a number")

            elif choice == "9":
                print("Tasks sorted by priority:")
                sorted_tasks = tm.sort_by_priority()
                if sorted_tasks:
                    for t in sorted_tasks:
                        print(f"{t.task_id}: {t.title} (Priority: {t.priority})")
                else:
                    print("No tasks to sort.")

            elif choice == "10":
                print("Tasks sorted by date (newest first):")
                sorted_tasks = tm.sort_by_date()
                if sorted_tasks:
                    for t in sorted_tasks:
                        print(f"{t.task_id}: {t.title} (Created: {t.created_at})")
                else:
                    print("No tasks to sort.")

            elif choice == "11":
                if tm.undo():
                    print("Undo successful.")
                else:
                    print("Nothing to undo.")

            elif choice == "12":
                stats = tm.get_stats()
                print(f"Total: {stats['total']}, Completed: {stats['completed']}, Pending: {stats['pending']}")

            elif choice == "13":
                new_tasks = tm.scan_emails_for_tasks()
                if new_tasks:
                    print(f"\nFound {len(new_tasks)} new tasks!")
                    for task in new_tasks:
                        task_id = str(len(tm.tasks) + 1)
                        tm.add_task(task_id, task['description'], task['priority'])
                        print(f"Added: {task['description']}")
                else:
                    print("No new tasks found in email.")

            elif choice == "14":
                tm.create_config_file()
                print("Email settings updated successfully!")

            elif choice == "0":
                print("Exiting Task Manager. Goodbye!")
                break

            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            if choice in ["13", "14"]:  # 
                print(f"Error with email operation: {str(e)}")
            else:
                print("An error occurred. Please try again.")
            continue
