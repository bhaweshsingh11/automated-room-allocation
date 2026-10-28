import tkinter as tk
from tkinter import ttk, messagebox
import copy

# ==========================================
# MODELS (Chapter 4: System Design)
# ==========================================
class Student:
    def __init__(self, s_id, group_id, needs_accessible):
        self.s_id = s_id
        self.group_id = group_id
        self.needs_accessible = needs_accessible

class Seat:
    def __init__(self, room_id, row, col, is_accessible=False, is_blocked=False):
        self.room_id = room_id
        self.row = row
        self.col = col
        self.is_accessible = is_accessible
        self.is_blocked = is_blocked
        self.seat_id = f"{room_id}-R{row}-C{col}"

    def __eq__(self, other):
        return self.seat_id == other.seat_id

    def __hash__(self):
        return hash(self.seat_id)

# ==========================================
# CSP SOLVER (Chapter 5: Implementation)
# ==========================================
class RoomAllocationCSP:
    def __init__(self, students, seats):
        self.students = students
        self.seats = seats
        self.domains = self._build_initial_domains()

    def _build_initial_domains(self):
        """Construct eligible seat domains for each student."""
        domains = {}
        for student in self.students:
            eligible_seats = []
            for seat in self.seats:
                if seat.is_blocked:
                    continue
                # Accessibility constraint
                if student.needs_accessible and not seat.is_accessible:
                    continue
                eligible_seats.append(seat)
            domains[student.s_id] = eligible_seats
        return domains

    def get_adjacent_seats(self, seat):
        """Returns side-by-side adjacent seats (Same Room, Same Row, Col +- 1)."""
        adj = []
        for s in self.seats:
            if s.room_id == seat.room_id and s.row == seat.row and abs(s.col - seat.col) == 1:
                adj.append(s)
        return adj

    def solve(self):
        unassigned = self.students.copy()
        return self.backtrack({}, self.domains, unassigned)

    def backtrack(self, assignment, domains, unassigned_students):
        """Backtracking with MRV and Forward Checking."""
        if not unassigned_students:
            return assignment  # Complete allocation

        # MRV Heuristic: Sort by smallest domain size first
        unassigned_students.sort(key=lambda s: len(domains[s.s_id]))
        student = unassigned_students.pop(0)

        for seat in domains[student.s_id]:
            # Try assigning the seat
            assignment[student.s_id] = seat
            
            # Constraint Propagation (Forward Checking)
            new_domains = copy.deepcopy(domains)
            is_valid = True
            
            # 1. Remove occupied seat from all unassigned domains
            for other in unassigned_students:
                if seat in new_domains[other.s_id]:
                    new_domains[other.s_id].remove(seat)
                if len(new_domains[other.s_id]) == 0:
                    is_valid = False
                    break
                    
            # 2. Group Separation: Remove adjacent seats for same-group students
            if is_valid:
                adjacent_seats = self.get_adjacent_seats(seat)
                for other in unassigned_students:
                    if other.group_id == student.group_id:
                        for adj_seat in adjacent_seats:
                            if adj_seat in new_domains[other.s_id]:
                                new_domains[other.s_id].remove(adj_seat)
                        if len(new_domains[other.s_id]) == 0:
                            is_valid = False
                            break
                            
            # Continue search if domains are valid
            if is_valid:
                result = self.backtrack(assignment, new_domains, unassigned_students)
                if result:
                    return result
                
            # Undo assignment if branch failed
            del assignment[student.s_id]
            
        unassigned_students.append(student)
        return None

# ==========================================
# GUI MODULE
# ==========================================
class AllocationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automated Room Allocation System")
        self.root.geometry("850x600")
        
        self.students = []
        self.seats = []

        self.setup_ui()
        self.load_sample_data()

    def setup_ui(self):
        # Layout Frames
        left_frame = tk.Frame(self.root, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        right_frame = tk.Frame(self.root, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Output Text Area
        tk.Label(right_frame, text="Allocation Report & Seating Chart", font=('Arial', 12, 'bold')).pack(anchor=tk.NW)
        self.output_text = tk.Text(right_frame, height=30, width=60)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Controls
        tk.Label(left_frame, text="System Controls", font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Button(left_frame, text="Load Sample Data", command=self.load_sample_data, width=20).pack(pady=5)
        tk.Button(left_frame, text="Run CSP Solver", command=self.run_allocation, width=20, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(left_frame, text="Clear Data", command=self.clear_data, width=20).pack(pady=5)

    def load_sample_data(self):
        self.clear_data()
        
        # Load Sample Students (Format: ID, Group, Needs_Accessible)
        self.students = [
            Student("Aarav", "G1", False),
            Student("Meera", "G2", False),
            Student("Kabir", "G1", False),
            Student("Diya", "G2", False),
            Student("Rohan", "G3", True), # Needs accessible seat
            Student("Sana", "G1", False),
            Student("Ishaan", "G2", False)
        ]
        
        # Load Sample Room & Seats (Room A: 3x3 grid)
        # 1st row of seats is accessible
        for r in range(1, 4):
            for c in range(1, 4):
                is_acc = (r == 1) # Row 1 is accessible
                is_blk = (r == 3 and c == 1) # Seat 3,1 is blocked
                self.seats.append(Seat("Room_A", r, c, is_accessible=is_acc, is_blocked=is_blk))
                
        self.log("Sample Data Loaded:\n- 7 Students\n- 1 Room (3x3 grid, Row 1 Accessible, Seat R3-C1 Blocked)\n")

    def clear_data(self):
        self.students = []
        self.seats = []
        self.output_text.delete(1.0, tk.END)
        self.log("Data cleared.\n")

    def run_allocation(self):
        if not self.students or not self.seats:
            messagebox.showerror("Error", "Please load data first.")
            return

        self.log("Initializing CSP Solver...")
        csp = RoomAllocationCSP(self.students, self.seats)
        
        self.log("Running Backtracking with MRV and Forward Checking...")
        assignment = csp.solve()

        if assignment:
            self.log("\n✅ SOLUTION FOUND!\n")
            self.generate_seating_chart(assignment)
        else:
            self.log("\n❌ ALLOCATION FAILED. Conflict detected! No valid assignment satisfies all constraints.\n")

    def generate_seating_chart(self, assignment):
        """Generates the room-wise chart as specified in Chapter 6."""
        # Reverse mapping: seat_id -> student
        seat_map = {seat.seat_id: student_id for student_id, seat in assignment.items()}
        
        self.log("-" * 40)
        self.log("SEATING CHART: Room_A")
        self.log("-" * 40)
        
        for r in range(1, 4):
            row_str = f"Row {r} | "
            for c in range(1, 4):
                seat_id = f"Room_A-R{r}-C{c}"
                
                # Check if blocked
                seat_obj = next((s for s in self.seats if s.seat_id == seat_id), None)
                if seat_obj and seat_obj.is_blocked:
                    row_str += "[BLOCKED]\t"
                    continue
                
                if seat_id in seat_map:
                    student_id = seat_map[seat_id]
                    # Find group for display
                    group = next(s.group_id for s in self.students if s.s_id == student_id)
                    row_str += f"{student_id} ({group})\t"
                else:
                    row_str += "[EMPTY]\t"
            self.log(row_str)
            
        self.log("-" * 40)

    def log(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = AllocationGUI(root)
    root.mainloop()