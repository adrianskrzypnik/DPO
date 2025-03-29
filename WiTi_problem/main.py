import functools


def parse_input(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    tasks = []
    idx = 0
    while idx < len(lines):
        if lines[idx].startswith("data"):
            n = int(lines[idx + 1].strip())
            jobs = []
            for i in range(n):
                p, w, d = map(int, lines[idx + 2 + i].strip().split())
                jobs.append((p, w, d, i + 1))  # Dodajemy indeks zadania
            tasks.append(jobs)
        idx += 1

    return tasks


def calculate_tardiness(order, jobs):
    time = 0
    tardiness = 0

    for job in order:
        p, w, d, _ = jobs[job]
        time += p
        tardiness += max(0, time - d) * w

    return tardiness


@functools.lru_cache(None)
def dp(mask, time, n, jobs):
    if mask == (1 << n) - 1:
        return 0, []

    best_tardiness = float('inf')
    best_order = None

    for i in range(n):
        if not (mask & (1 << i)):
            p, w, d, _ = jobs[i]
            new_time = time + p
            tardiness, order = dp(mask | (1 << i), new_time, n, jobs)
            tardiness += max(0, new_time - d) * w

            if tardiness < best_tardiness or (
                    tardiness == best_tardiness and (best_order is None or [i] + order < best_order)):
                best_tardiness = tardiness
                best_order = [i] + order

    return best_tardiness, best_order


def find_optimal_permutation(jobs):
    n = len(jobs)
    best_tardiness, best_order = dp(0, 0, n, tuple(jobs))
    return [jobs[i][3] for i in best_order], best_tardiness


if __name__ == "__main__":
    file_path = "witi.data.txt"  # Ścieżka do pliku
    tasks = parse_input(file_path)

    for i, jobs in enumerate(tasks, 10):  # Numeracja zgodnie z formatem pliku
        optimal_order, best_tardiness = find_optimal_permutation(jobs)
        print(f"data.{i}: Optimal order: {optimal_order}")
        print(f"Total WiTi: {best_tardiness}")
