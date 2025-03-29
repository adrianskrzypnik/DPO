#include <iostream>
#include <fstream>
#include <vector>
#include <queue>
#include <algorithm>
#include <chrono>
#include <climits>
#include <tuple>

using namespace std;
using namespace std::chrono;

struct Task {
    int id;
    int r; // czas dostarczenia
    int p; // czas trwania
    int q; // czas stygnięcia

    Task(int id, int r, int p, int q) : id(id), r(r), p(p), q(q) {}
};

struct CompareQ {
    bool operator()(const Task& a, const Task& b) const {
        return a.q < b.q;
    }
};

vector<Task> load_tasks_from_file(const string& filename) {
    ifstream file(filename);
    if (!file.is_open()) {
        throw runtime_error("Cannot open file: " + filename);
    }

    vector<Task> tasks;
    int n;
    file >> n;
    for (int i = 1; i <= n; ++i) {
        int r, p, q;
        file >> r >> p >> q;
        tasks.emplace_back(i, r, p, q);
    }
    return tasks;
}

int calculate_cmax(const vector<Task>& schedule) {
    int current_time = 0;
    int cmax = 0;

    for (const auto& task : schedule) {
        current_time = max(current_time, task.r) + task.p;
        cmax = max(cmax, current_time + task.q);
    }

    return cmax;
}

vector<Task> schrage_algorithm(const vector<Task>& tasks) {
    vector<Task> tasks_by_r = tasks;
    sort(tasks_by_r.begin(), tasks_by_r.end(), [](const Task& a, const Task& b) {
        return a.r < b.r;
    });

    int current_time = 0;
    vector<Task> schedule;
    priority_queue<Task, vector<Task>, CompareQ> available_tasks;

    size_t index = 0;
    while (index < tasks_by_r.size() || !available_tasks.empty()) {
        while (index < tasks_by_r.size() && tasks_by_r[index].r <= current_time) {
            available_tasks.push(tasks_by_r[index]);
            index++;
        }

        if (available_tasks.empty()) {
            if (index < tasks_by_r.size()) {
                current_time = tasks_by_r[index].r;
            }
            continue;
        }

        Task selected_task = available_tasks.top();
        available_tasks.pop();

        schedule.push_back(selected_task);
        current_time += selected_task.p;
    }

    return schedule;
}

vector<Task> weighted_schrage(const vector<Task>& tasks, double w_r = 1.0, double w_p = 1.0, double w_q = 1.0) {
    vector<Task> tasks_by_r = tasks;
    sort(tasks_by_r.begin(), tasks_by_r.end(), [](const Task& a, const Task& b) {
        return a.r < b.r;
    });

    int current_time = 0;
    vector<Task> schedule;

    auto compare = [w_r, w_p, w_q](const pair<double, Task>& a, const pair<double, Task>& b) {
        return a.first < b.first; // Max heap
    };
    priority_queue<pair<double, Task>, vector<pair<double, Task>>, decltype(compare)> available_tasks(compare);

    size_t index = 0;
    while (index < tasks_by_r.size() || !available_tasks.empty()) {
        while (index < tasks_by_r.size() && tasks_by_r[index].r <= current_time) {
            Task& task = tasks_by_r[index];
            double priority = w_q * task.q - w_r * task.r - w_p * task.p;
            available_tasks.emplace(priority, task);
            index++;
        }

        if (available_tasks.empty()) {
            if (index < tasks_by_r.size()) {
                current_time = tasks_by_r[index].r;
            }
            continue;
        }

        Task selected_task = available_tasks.top().second;
        available_tasks.pop();

        schedule.push_back(selected_task);
        current_time += selected_task.p;
    }

    return schedule;
}

vector<Task> insert_task(const vector<Task>& schedule, size_t task_idx, size_t new_pos) {
    vector<Task> new_schedule = schedule;
    Task task = new_schedule[task_idx];
    new_schedule.erase(new_schedule.begin() + task_idx);
    new_schedule.insert(new_schedule.begin() + new_pos, task);
    return new_schedule;
}

vector<Task> enhanced_local_search(const vector<Task>& schedule, int max_iterations = 100) {
    vector<Task> best_schedule = schedule;
    int best_cmax = calculate_cmax(best_schedule);

    int iteration = 0;
    bool improved = true;

    while (improved && iteration < max_iterations) {
        improved = false;
        iteration++;

        for (size_t i = 0; i < best_schedule.size(); ++i) {
            for (size_t j = i + 1; j < best_schedule.size(); ++j) {
                vector<Task> new_schedule = best_schedule;
                swap(new_schedule[i], new_schedule[j]);

                int new_cmax = calculate_cmax(new_schedule);

                if (new_cmax < best_cmax) {
                    best_schedule = new_schedule;
                    best_cmax = new_cmax;
                    improved = true;
                    break;
                }
            }
            if (improved) break;
        }

        if (!improved) {
            for (size_t i = 0; i < best_schedule.size(); ++i) {
                for (size_t j = 0; j < best_schedule.size(); ++j) {
                    if (i == j) continue;

                    vector<Task> new_schedule = insert_task(best_schedule, i, j);
                    int new_cmax = calculate_cmax(new_schedule);

                    if (new_cmax < best_cmax) {
                        best_schedule = new_schedule;
                        best_cmax = new_cmax;
                        improved = true;
                        break;
                    }
                }
                if (improved) break;
            }
        }

        if (!improved) {
            for (size_t i = 0; i < best_schedule.size(); ++i) {
                for (size_t j = i + 2; j < best_schedule.size(); ++j) {
                    vector<Task> new_schedule = best_schedule;
                    reverse(new_schedule.begin() + i, new_schedule.begin() + j + 1);

                    int new_cmax = calculate_cmax(new_schedule);

                    if (new_cmax < best_cmax) {
                        best_schedule = new_schedule;
                        best_cmax = new_cmax;
                        improved = true;
                        break;
                    }
                }
                if (improved) break;
            }
        }
    }

    return best_schedule;
}

vector<Task> multi_start_schrage(const vector<Task>& tasks, int num_starts = 5) {
    vector<Task> best_schedule;
    int best_cmax = INT_MAX;


    vector<tuple<double, double, double>> weight_configs = {
        {1.0, 0.5, 2.0},
        {0.5, 1.0, 2.0},
        {2.0, 0.5, 1.0},
        {1.0, 1.0, 1.0},
        {0.0, 0.0, 1.0},
    };

    for (int i = 0; i < min(num_starts, (int)weight_configs.size()); ++i) {
        double w_r, w_p, w_q;
        tie(w_r, w_p, w_q) = weight_configs[i];

        vector<Task> initial_schedule;
        if (i == 4) {
            initial_schedule = schrage_algorithm(tasks);
        } else {
            initial_schedule = weighted_schrage(tasks, w_r, w_p, w_q);
        }

        vector<Task> improved_schedule = enhanced_local_search(initial_schedule, 200);

        int cmax = calculate_cmax(improved_schedule);

        if (cmax < best_cmax) {
            best_schedule = improved_schedule;
            best_cmax = cmax;
        }
    }

    return best_schedule;
}
int main() {
    auto time_start = high_resolution_clock::now();

    vector<string> data_files = {"data1.txt", "data2.txt", "data3.txt", "data4.txt"};
    int sum_time = 0;

    for (const auto& file : data_files) {
        try {
            vector<Task> tasks = load_tasks_from_file(file);
            vector<Task> schedule = multi_start_schrage(tasks);
            int cmax = calculate_cmax(schedule);

            sum_time += cmax;

            cout << "\nWyniki dla pliku " << file << ": " << cmax << endl;
            cout << "Schedule: ";
            for (const auto& task : schedule) {
                cout << task.id << " ";
            }
            cout << endl;
        } catch (const exception& e) {
            cout << "Błąd przy przetwarzaniu pliku " << file << ": " << e.what() << endl;
        }
    }

    cout << "Zsumowany czas: " << sum_time << endl;

    auto end = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end - time_start);
    cout << "Czas wykonania: " << duration.count() / 1000.0 << " s" << endl;

    return 0;
}
