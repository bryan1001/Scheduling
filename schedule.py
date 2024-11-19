from ortools.sat.python import cp_model
from datetime import datetime, timedelta

# pre_assigned = {
#     range(0, 5): 0,  # Parent A: 11/17 to 11/22
#     range(5, 7): 1,  # Parent B: 11/22 to 11/24
#     range(10, 15): 0,  # Parent A: 11/27 to 12/1
#     range(35, 42): 1,  # Parent B: 12/22 to 12/29
# }


# Define problem parameters
start_date = datetime.strptime("2024-11-17", "%Y-%m-%d")
num_nights = 50

from ortools.sat.python import cp_model
from datetime import datetime, timedelta


def solve_shared_custody_exhaustive(start_date, num_nights, pre_assigned):
    model = cp_model.CpModel()

    # Variables: each night is assigned to Parent A (0) or Parent B (1)
    nights = [model.NewIntVar(0, 1, f"night_{i}") for i in range(num_nights)]

    # Pre-assigned nights (shifted back by 1 day from original dates)
    for indices, parent in pre_assigned.items():
        for i in indices:
            model.Add(nights[i] == parent)

    # Equal total number of nights
    model.Add(sum(nights) == num_nights // 2)
    model.Add(sum(1 - nights[i] for i in range(num_nights)) == num_nights // 2)

    # Equal weekend nights (Friday and Saturday nights)
    weekend_nights = []
    current_date = start_date
    for i in range(num_nights):
        if current_date.weekday() in [4, 5]:  # Friday is 4, Saturday is 5
            weekend_nights.append(i)
        current_date += timedelta(days=1)

    model.Add(sum(nights[i] for i in weekend_nights) == len(weekend_nights) // 2)
    model.Add(sum(1 - nights[i] for i in weekend_nights) == len(weekend_nights) // 2)

    # Full week indicators (Sunday night through Saturday night)
    full_weeks = []
    for i in range(0, num_nights - 6, 7):
        full_week_a = model.NewBoolVar(f"full_week_a_{i}")
        full_week_b = model.NewBoolVar(f"full_week_b_{i}")
        model.Add(sum(nights[j] for j in range(i, i + 7)) == 0).OnlyEnforceIf(
            full_week_a
        )  # Parent A
        model.Add(sum(nights[j] for j in range(i, i + 7)) == 7).OnlyEnforceIf(
            full_week_b
        )  # Parent B
        full_weeks.append(full_week_a)
        full_weeks.append(full_week_b)

    full_week_count = model.NewIntVar(0, 10, "full_week_count")
    model.Add(full_week_count == sum(full_weeks))
    for i in range(num_nights - 7):
        # Limit Parent A blocks (when nights[i] = 0)
        model.Add(sum(1 - nights[j] for j in range(i, i + 8)) <= 7)
        # Limit Parent B blocks (when nights[i] = 1)
        model.Add(sum(nights[j] for j in range(i, i + 8)) <= 7)

    # for i in range(1, num_nights - 1):
    #     # If day i is different from i-1, it must be same as i+1
    # model.Add(nights[i] == nights[i + 1]).OnlyEnforceIf(nights[i - 1].Not())
    #     model.Add(nights[i] == nights[i + 1]).OnlyEnforceIf(nights[i - 1])

    # model.Add(sum(full_weeks) >= 1)
    model.Maximize(full_week_count)

    solver = cp_model.CpSolver()
    # solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL,):
        schedule = ["Bry" if solver.Value(night) == 0 else "Mel" for night in nights]
        full_week_count = sum(solver.Value(week) for week in full_weeks)
        return schedule, full_week_count
    else:
        return None, 0


def format_schedule(schedule, start_date):
    ranges = []
    current_parent = schedule[0]
    current_start = start_date - timedelta(days=1)  # Start from night before

    for i in range(1, len(schedule)):
        if schedule[i] != current_parent:
            end_date = start_date + timedelta(days=i - 2)  # Adjust for nights
            ranges.append((current_parent, current_start, end_date))
            current_parent = schedule[i]
            current_start = start_date + timedelta(days=i - 1)

    # Add the last range
    end_date = start_date + timedelta(days=len(schedule) - 2)
    ranges.append((current_parent, current_start, end_date))
    return ranges
