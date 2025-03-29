import time
import heapq
from copy import deepcopy
## 100 000 do optymalizacji 4 sekundy

def load_tasks_from_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
    return load_tasks_from_text(content)


def load_tasks_from_text(text):
    lines = text.strip().split('\n')
    n = int(lines[0])
    tasks = []

    for i in range(1, n + 1):
        if i < len(lines):
            r, p, q = map(int, lines[i].split())
            tasks.append(Task(i, r, p, q))

    return tasks


class Task:
    def __init__(self, id, r, p, q):
        self.id = id
        self.r = r  # czas dostarczenia
        self.p = p  # czas trwania
        self.q = q  # czas stygnięcia

    def __str__(self):
        return f"Task(id={self.id}, r={self.r}, p={self.p}, q={self.q})"


def calculate_cmax(schedule):
    current_time = 0
    cmax = 0

    for task in schedule:
        current_time = max(current_time, task.r) + task.p
        cmax = max(cmax, current_time + task.q)

    return cmax


def schrage_with_queue(tasks):
    """Standard Schrage algorithm with a priority queue"""
    tasks_by_r = sorted([(task.r, i, task) for i, task in enumerate(tasks)])

    current_time = 0
    schedule = []
    available_tasks = []

    tasks_index = 0
    tasks_len = len(tasks_by_r)

    while tasks_index < tasks_len or available_tasks:
        # Add all tasks that have arrived by current_time to available_tasks
        while tasks_index < tasks_len and tasks_by_r[tasks_index][0] <= current_time:
            task = tasks_by_r[tasks_index][2]
            heapq.heappush(available_tasks, (-task.q, tasks_by_r[tasks_index][1], task))
            tasks_index += 1

        if not available_tasks:
            if tasks_index < tasks_len:
                current_time = tasks_by_r[tasks_index][0]
            continue

        # Select task with highest q value
        _, _, selected_task = heapq.heappop(available_tasks)

        schedule.append(selected_task)
        current_time += selected_task.p

    return schedule


def weighted_schrage(tasks, w_r=1.0, w_p=1.0, w_q=1.0):
    """Schrage variant with weighted priorities"""
    tasks_by_r = sorted([(task.r, i, task) for i, task in enumerate(tasks)])

    current_time = 0
    schedule = []
    available_tasks = []

    tasks_index = 0
    tasks_len = len(tasks_by_r)

    while tasks_index < tasks_len or available_tasks:
        while tasks_index < tasks_len and tasks_by_r[tasks_index][0] <= current_time:
            task = tasks_by_r[tasks_index][2]
            # Combined priority based on weighted r, p, q values
            priority = -(w_q * task.q - w_r * task.r - w_p * task.p)
            heapq.heappush(available_tasks, (priority, tasks_by_r[tasks_index][1], task))
            tasks_index += 1

        if not available_tasks:
            if tasks_index < tasks_len:
                current_time = tasks_by_r[tasks_index][0]
            continue

        _, _, selected_task = heapq.heappop(available_tasks)

        schedule.append(selected_task)
        current_time += selected_task.p

    return schedule


def insert_task(schedule, task_idx, new_pos):
    """Insert a task at a new position in the schedule"""
    new_schedule = schedule.copy()
    task = new_schedule.pop(task_idx)
    new_schedule.insert(new_pos, task)
    return new_schedule





def enhanced_local_search(schedule, max_iterations=100):
    """Enhanced local search with multiple neighborhoods"""
    best_schedule = schedule.copy()
    best_cmax = calculate_cmax(best_schedule)

    iteration = 0
    improved = True

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # 1. Try simple pairwise swaps
        for i in range(len(best_schedule)):
            for j in range(i + 1, len(best_schedule)):
                new_schedule = best_schedule.copy()
                new_schedule[i], new_schedule[j] = new_schedule[j], new_schedule[i]

                new_cmax = calculate_cmax(new_schedule)

                if new_cmax < best_cmax:
                    best_schedule = new_schedule
                    best_cmax = new_cmax
                    improved = True
                    break

            if improved:
                break

        # 2. Try task insertions if no swap improved the solution
        if not improved:
            for i in range(len(best_schedule)):
                for j in range(len(best_schedule)):
                    if i == j:
                        continue

                    new_schedule = insert_task(best_schedule, i, j)
                    new_cmax = calculate_cmax(new_schedule)

                    if new_cmax < best_cmax:
                        best_schedule = new_schedule
                        best_cmax = new_cmax
                        improved = True
                        break

                if improved:
                    break

        # 3. Try reversing segments if no insertion improved the solution
        if not improved:
            for i in range(len(best_schedule)):
                for j in range(i + 2, len(best_schedule)):
                    new_schedule = best_schedule.copy()
                    new_schedule[i:j + 1] = reversed(new_schedule[i:j + 1])

                    new_cmax = calculate_cmax(new_schedule)

                    if new_cmax < best_cmax:
                        best_schedule = new_schedule
                        best_cmax = new_cmax
                        improved = True
                        break

                if improved:
                    break

    return best_schedule


def multi_start_schrage(tasks, num_starts=5):
    """Multi-start approach with different initial solutions"""
    best_schedule = None
    best_cmax = float('inf')

    # Different priority weightings for initial solutions
    weight_configs = [
        (1.0, 0.5, 2.0),  # Emphasize q
        (0.5, 1.0, 2.0),  # Balanced p and q
        (2.0, 0.5, 1.0),  # Emphasize r
        (1.0, 1.0, 1.0),  # Equal weights
        (0.0, 0.0, 1.0),  # Only q (standard Schrage)
    ]

    for w_r, w_p, w_q in weight_configs[:num_starts]:
        # Generate initial solution with different weights
        initial_schedule = weighted_schrage(tasks, w_r, w_p, w_q)

        # Improve with local search
        improved_schedule = enhanced_local_search(initial_schedule)

        cmax = calculate_cmax(improved_schedule)

        if cmax < best_cmax:
            best_schedule = improved_schedule
            best_cmax = cmax

    return best_schedule



def main():
    time_start = time.time()

    data_files = ["data1.txt", "data2.txt", "data3.txt", "data4.txt"]
    sum_time = 0

    for file in data_files:
        try:
            tasks = load_tasks_from_file(file)
            schedule = multi_start_schrage(tasks)
            cmax = calculate_cmax(schedule)

            sum_time += cmax

            print(f"\nWyniki dla pliku {file}: {cmax}")
            print("Schedule:", " ".join(str(task.id) for task in schedule))
        except Exception as e:
            print(f"Błąd przy przetwarzaniu pliku {file}: {e}")

    print(f'Zsumowany czas: {sum_time}')

    end = time.time()
    print(f"Czas wykonania: {end - time_start:.4f} s")


if __name__ == "__main__":
    main()