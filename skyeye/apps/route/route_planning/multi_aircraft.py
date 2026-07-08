import math
import multiprocessing
import os
import random
from concurrent.futures import ProcessPoolExecutor, as_completed


def euclidean_distance(point_a, point_b):
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def route_distance(route, depot):
    """Calculate a closed sortie distance: depot -> points -> depot."""
    if not route:
        return 0.0
    distance = euclidean_distance(depot, route[0][1])
    distance += sum(
        euclidean_distance(route[index][1], route[index + 1][1])
        for index in range(len(route) - 1)
    )
    distance += euclidean_distance(route[-1][1], depot)
    return distance


def _best_insertion(route, indexed_point, depot, current_distance=None):
    if not route:
        return [indexed_point], 2 * euclidean_distance(depot, indexed_point[1])

    if current_distance is None:
        current_distance = route_distance(route, depot)

    point = indexed_point[1]
    best_index = 0
    best_delta = math.inf
    for index in range(len(route) + 1):
        previous_point = depot if index == 0 else route[index - 1][1]
        next_point = depot if index == len(route) else route[index][1]
        delta = (
            euclidean_distance(previous_point, point)
            + euclidean_distance(point, next_point)
            - euclidean_distance(previous_point, next_point)
        )
        if delta < best_delta:
            best_index = index
            best_delta = delta

    best_route = route[:best_index] + [indexed_point] + route[best_index:]
    return best_route, current_distance + best_delta


def _two_opt(route, depot, max_passes=10):
    if len(route) < 3:
        return route

    best = route[:]
    for _ in range(max_passes):
        improved = False
        for start in range(len(best) - 1):
            point_before = depot if start == 0 else best[start - 1][1]
            first = best[start][1]
            for end in range(start + 1, len(best)):
                last = best[end][1]
                point_after = depot if end == len(best) - 1 else best[end + 1][1]
                old_edges = (
                    euclidean_distance(point_before, first)
                    + euclidean_distance(last, point_after)
                )
                new_edges = (
                    euclidean_distance(point_before, last)
                    + euclidean_distance(first, point_after)
                )
                if new_edges + 1e-6 < old_edges:
                    best[start:end + 1] = reversed(best[start:end + 1])
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return best


def _candidate_orders(indexed_points, depots, attempts):
    indexed = list(indexed_points)

    def nearest_depot_distance(item):
        return min(euclidean_distance(item[1], depot) for depot in depots)

    yield sorted(indexed, key=nearest_depot_distance, reverse=True)
    yield sorted(
        indexed,
        key=lambda item: math.atan2(
            item[1][1] - depots[0][1],
            item[1][0] - depots[0][0],
        ),
    )

    rng = random.Random(20260618)
    for _ in range(max(0, attempts - 2)):
        candidate = indexed[:]
        rng.shuffle(candidate)
        yield candidate


def _aircraft_elapsed(distance_m, sortie_count, speed_m_per_minute, turnaround_minutes):
    flight_minutes = distance_m / speed_m_per_minute
    turnaround_total = max(0, sortie_count - 1) * turnaround_minutes
    return flight_minutes + turnaround_total


def _build_schedule(
    indexed_points,
    aircraft,
    max_distance,
    speed_m_per_minute,
    turnaround_minutes,
    progress_callback=None,
):
    schedules = [
        {
            'aircraft': aircraft_item,
            'sorties': [],
            'distance_m': 0.0,
        }
        for aircraft_item in aircraft
    ]

    total_points = len(indexed_points)
    report_step = max(1, total_points // 20)
    for point_position, indexed_point in enumerate(indexed_points, start=1):
        choices = []
        for aircraft_index, schedule in enumerate(schedules):
            depot = schedule['aircraft']['depot']

            # Insert into any existing sortie.
            for sortie_index, sortie in enumerate(schedule['sorties']):
                inserted, inserted_distance = _best_insertion(
                    sortie['route'],
                    indexed_point,
                    depot,
                    current_distance=sortie['distance_m'],
                )
                if inserted_distance > max_distance + 1e-6:
                    continue
                new_aircraft_distance = (
                    schedule['distance_m']
                    - sortie['distance_m']
                    + inserted_distance
                )
                new_elapsed = _aircraft_elapsed(
                    new_aircraft_distance,
                    len(schedule['sorties']),
                    speed_m_per_minute,
                    turnaround_minutes,
                )
                projected_makespan = max(
                    new_elapsed if index == aircraft_index else _aircraft_elapsed(
                        other['distance_m'],
                        len(other['sorties']),
                        speed_m_per_minute,
                        turnaround_minutes,
                    )
                    for index, other in enumerate(schedules)
                )
                choices.append((
                    projected_makespan,
                    new_elapsed,
                    inserted_distance - sortie['distance_m'],
                    0,
                    aircraft_index,
                    sortie_index,
                    inserted,
                    inserted_distance,
                ))

            # Start another sortie for this aircraft.
            new_sortie_distance = 2 * euclidean_distance(depot, indexed_point[1])
            if new_sortie_distance <= max_distance + 1e-6:
                new_aircraft_distance = schedule['distance_m'] + new_sortie_distance
                new_sortie_count = len(schedule['sorties']) + 1
                new_elapsed = _aircraft_elapsed(
                    new_aircraft_distance,
                    new_sortie_count,
                    speed_m_per_minute,
                    turnaround_minutes,
                )
                projected_makespan = max(
                    new_elapsed if index == aircraft_index else _aircraft_elapsed(
                        other['distance_m'],
                        len(other['sorties']),
                        speed_m_per_minute,
                        turnaround_minutes,
                    )
                    for index, other in enumerate(schedules)
                )
                choices.append((
                    projected_makespan,
                    new_elapsed,
                    new_sortie_distance,
                    1,
                    aircraft_index,
                    len(schedule['sorties']),
                    [indexed_point],
                    new_sortie_distance,
                ))

        if not choices:
            return None

        choice = min(choices, key=lambda item: item[:6])
        (
            _,
            _,
            _,
            is_new_sortie,
            aircraft_index,
            sortie_index,
            route,
            distance_m,
        ) = choice
        schedule = schedules[aircraft_index]
        if is_new_sortie:
            schedule['sorties'].append({
                'route': route,
                'distance_m': distance_m,
            })
            schedule['distance_m'] += distance_m
        else:
            previous_distance = schedule['sorties'][sortie_index]['distance_m']
            schedule['sorties'][sortie_index] = {
                'route': route,
                'distance_m': distance_m,
            }
            schedule['distance_m'] += distance_m - previous_distance
        if progress_callback and (
            point_position == total_points or point_position % report_step == 0
        ):
            progress_callback(point_position, total_points)

    for schedule in schedules:
        depot = schedule['aircraft']['depot']
        schedule['distance_m'] = 0.0
        for sortie in schedule['sorties']:
            sortie['route'] = _two_opt(sortie['route'], depot)
            sortie['distance_m'] = route_distance(sortie['route'], depot)
            schedule['distance_m'] += sortie['distance_m']
    return schedules


def _deduplicate_indexed_points(points):
    """按毫米级投影坐标去重，同时保留首次出现的全局航点下标。"""
    unique_points = []
    seen = set()
    for point_index, point in enumerate(points):
        normalized = (float(point[0]), float(point[1]))
        key = (round(normalized[0], 3), round(normalized[1], 3))
        if key in seen:
            continue
        seen.add(key)
        unique_points.append((point_index, normalized))
    return unique_points


def _partition_points(indexed_points, aircraft, max_distance):
    """
    将航点预分区给飞机。

    先处理离所有起点都较远的困难航点，再按“预计新增作业距离”选择飞机，
    既保证服务范围约束，也避免所有飞机反复竞争全部航点。
    """
    partitions = [[] for _ in aircraft]
    estimated_loads = [0.0 for _ in aircraft]
    point_options = []

    for indexed_point in indexed_points:
        point = indexed_point[1]
        eligible = []
        for aircraft_index, aircraft_item in enumerate(aircraft):
            distance = euclidean_distance(point, aircraft_item['depot'])
            if 2 * distance <= max_distance + 1e-6:
                eligible.append((aircraft_index, distance))
        if not eligible:
            raise ValueError('存在任一飞机起点往返都无法覆盖的航点')
        point_options.append((
            min(distance for _, distance in eligible),
            indexed_point,
            eligible,
        ))

    # 远点和可选飞机少的点优先，减少后续分区不均与不可行风险。
    point_options.sort(
        key=lambda item: (len(item[2]), -item[0]),
    )
    for _, indexed_point, eligible in point_options:
        aircraft_index, distance = min(
            eligible,
            key=lambda option: (
                estimated_loads[option[0]] + 2 * option[1],
                option[1],
                option[0],
            ),
        )
        partitions[aircraft_index].append(indexed_point)
        estimated_loads[aircraft_index] += 2 * distance

    return partitions


def _score_schedules(schedules, speed_m_per_minute, turnaround_minutes):
    elapsed = [
        _aircraft_elapsed(
            schedule['distance_m'],
            len(schedule['sorties']),
            speed_m_per_minute,
            turnaround_minutes,
        )
        for schedule in schedules
    ]
    return (
        max(elapsed, default=0.0),
        sum(elapsed),
        sum(len(schedule['sorties']) for schedule in schedules),
        sum(schedule['distance_m'] for schedule in schedules),
    )


def _copy_schedules(schedules):
    return [
        {
            'aircraft': schedule['aircraft'],
            'sorties': [
                {
                    'route': sortie['route'][:],
                    'distance_m': sortie['distance_m'],
                }
                for sortie in schedule['sorties']
            ],
            'distance_m': schedule['distance_m'],
        }
        for schedule in schedules
    ]


def _refresh_schedule(schedule, use_two_opt=False):
    depot = schedule['aircraft']['depot']
    refreshed = []
    total_distance = 0.0
    for sortie in schedule['sorties']:
        route = sortie['route']
        if not route:
            continue
        if use_two_opt:
            route = _two_opt(route, depot, max_passes=3)
        distance_m = route_distance(route, depot)
        refreshed.append({'route': route, 'distance_m': distance_m})
        total_distance += distance_m
    schedule['sorties'] = refreshed
    schedule['distance_m'] = total_distance


def _solution_cost(score):
    """Scalar cost for annealing; makespan remains the dominant term."""
    makespan, total_elapsed, sortie_count, total_distance = score
    return (
        makespan
        + 0.05 * total_elapsed
        + 0.01 * sortie_count
        + total_distance / 1_000_000
    )


def _select_weighted_operator(operators, weights, rng):
    threshold = rng.random() * sum(weights)
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if threshold <= cumulative:
            return index, operators[index]
    return len(operators) - 1, operators[-1]


def _all_route_points(schedules):
    return [
        (aircraft_index, sortie_index, point_position, indexed_point)
        for aircraft_index, schedule in enumerate(schedules)
        for sortie_index, sortie in enumerate(schedule['sorties'])
        for point_position, indexed_point in enumerate(sortie['route'])
    ]


def _remove_point_indexes(schedules, point_indexes):
    removed = []
    point_indexes = set(point_indexes)
    for schedule in schedules:
        for sortie in schedule['sorties']:
            kept = []
            for indexed_point in sortie['route']:
                if indexed_point[0] in point_indexes:
                    removed.append(indexed_point)
                else:
                    kept.append(indexed_point)
            sortie['route'] = kept
        _refresh_schedule(schedule)
    return removed


def _destroy_random(schedules, remove_count, rng):
    points = _all_route_points(schedules)
    chosen = rng.sample(
        [item[3][0] for item in points],
        min(remove_count, len(points)),
    )
    return _remove_point_indexes(schedules, chosen)


def _destroy_worst(schedules, remove_count, rng):
    savings = []
    for schedule in schedules:
        depot = schedule['aircraft']['depot']
        for sortie in schedule['sorties']:
            route = sortie['route']
            for point_position, indexed_point in enumerate(route):
                reduced = route[:point_position] + route[point_position + 1:]
                saving = sortie['distance_m'] - route_distance(reduced, depot)
                savings.append((saving, rng.random(), indexed_point[0]))
    savings.sort(reverse=True)
    return _remove_point_indexes(
        schedules,
        [item[2] for item in savings[:remove_count]],
    )


def _destroy_related(schedules, remove_count, rng):
    points = [item[3] for item in _all_route_points(schedules)]
    if not points:
        return []
    seed = rng.choice(points)
    related = sorted(
        points,
        key=lambda item: (
            euclidean_distance(seed[1], item[1]),
            rng.random(),
        ),
    )
    return _remove_point_indexes(
        schedules,
        [item[0] for item in related[:remove_count]],
    )


def _insertion_options(
    schedules,
    indexed_point,
    max_distance,
    speed_m_per_minute,
    turnaround_minutes,
):
    options = []
    elapsed = [
        _aircraft_elapsed(
            schedule['distance_m'],
            len(schedule['sorties']),
            speed_m_per_minute,
            turnaround_minutes,
        )
        for schedule in schedules
    ]
    total_elapsed = sum(elapsed)
    total_sorties = sum(len(schedule['sorties']) for schedule in schedules)
    total_distance = sum(schedule['distance_m'] for schedule in schedules)

    for aircraft_index, schedule in enumerate(schedules):
        depot = schedule['aircraft']['depot']
        old_elapsed = elapsed[aircraft_index]
        for sortie_index, sortie in enumerate(schedule['sorties']):
            route, distance_m = _best_insertion(
                sortie['route'],
                indexed_point,
                depot,
                current_distance=sortie['distance_m'],
            )
            if distance_m > max_distance + 1e-6:
                continue
            new_aircraft_distance = (
                schedule['distance_m'] - sortie['distance_m'] + distance_m
            )
            new_elapsed = _aircraft_elapsed(
                new_aircraft_distance,
                len(schedule['sorties']),
                speed_m_per_minute,
                turnaround_minutes,
            )
            projected_elapsed = elapsed[:]
            projected_elapsed[aircraft_index] = new_elapsed
            score = (
                max(projected_elapsed, default=0.0),
                total_elapsed - old_elapsed + new_elapsed,
                total_sorties,
                total_distance - sortie['distance_m'] + distance_m,
            )
            options.append((
                score,
                distance_m - sortie['distance_m'],
                aircraft_index,
                sortie_index,
                route,
                distance_m,
            ))

        distance_m = 2 * euclidean_distance(depot, indexed_point[1])
        if distance_m <= max_distance + 1e-6:
            new_aircraft_distance = schedule['distance_m'] + distance_m
            new_sortie_count = len(schedule['sorties']) + 1
            new_elapsed = _aircraft_elapsed(
                new_aircraft_distance,
                new_sortie_count,
                speed_m_per_minute,
                turnaround_minutes,
            )
            projected_elapsed = elapsed[:]
            projected_elapsed[aircraft_index] = new_elapsed
            score = (
                max(projected_elapsed, default=0.0),
                total_elapsed - old_elapsed + new_elapsed,
                total_sorties + 1,
                total_distance + distance_m,
            )
            options.append((
                score,
                distance_m,
                aircraft_index,
                None,
                [indexed_point],
                distance_m,
            ))

    options.sort(key=lambda item: (item[0], item[1], item[2]))
    return options


def _apply_insertion(schedules, option):
    _, _, aircraft_index, sortie_index, route, distance_m = option
    schedule = schedules[aircraft_index]
    if sortie_index is None:
        schedule['sorties'].append({
            'route': route,
            'distance_m': distance_m,
        })
        schedule['distance_m'] += distance_m
        return
    previous_distance = schedule['sorties'][sortie_index]['distance_m']
    schedule['sorties'][sortie_index] = {
        'route': route,
        'distance_m': distance_m,
    }
    schedule['distance_m'] += distance_m - previous_distance


def _repair_greedy(
    schedules,
    removed,
    max_distance,
    speed_m_per_minute,
    turnaround_minutes,
    rng,
):
    pending = removed[:]
    rng.shuffle(pending)
    for indexed_point in pending:
        options = _insertion_options(
            schedules,
            indexed_point,
            max_distance,
            speed_m_per_minute,
            turnaround_minutes,
        )
        if not options:
            return False
        _apply_insertion(schedules, options[0])
    return True


def _repair_regret(
    schedules,
    removed,
    max_distance,
    speed_m_per_minute,
    turnaround_minutes,
    rng,
):
    pending = removed[:]
    while pending:
        chosen = None
        chosen_position = None
        chosen_key = None
        for position, indexed_point in enumerate(pending):
            options = _insertion_options(
                schedules,
                indexed_point,
                max_distance,
                speed_m_per_minute,
                turnaround_minutes,
            )
            if not options:
                continue
            best_cost = _solution_cost(options[0][0])
            second_cost = (
                _solution_cost(options[1][0])
                if len(options) > 1
                else best_cost + max(1.0, best_cost * 0.1)
            )
            key = (second_cost - best_cost, -best_cost, rng.random())
            if chosen_key is None or key > chosen_key:
                chosen_key = key
                chosen = options[0]
                chosen_position = position
        if chosen is None:
            return False
        _apply_insertion(schedules, chosen)
        pending.pop(chosen_position)
    return True


def _run_alns(
    initial_schedules,
    max_distance,
    speed_m_per_minute,
    turnaround_minutes,
    iterations,
    random_seed,
    progress_callback=None,
):
    rng = random.Random(random_seed)
    current = _copy_schedules(initial_schedules)
    current_score = _score_schedules(
        current, speed_m_per_minute, turnaround_minutes
    )
    best = _copy_schedules(current)
    best_score = current_score
    destroy_operators = [_destroy_random, _destroy_worst, _destroy_related]
    repair_operators = [_repair_greedy, _repair_regret]
    destroy_weights = [1.0] * len(destroy_operators)
    repair_weights = [1.0] * len(repair_operators)
    destroy_rewards = [0.0] * len(destroy_operators)
    repair_rewards = [0.0] * len(repair_operators)
    destroy_usage = [0] * len(destroy_operators)
    repair_usage = [0] * len(repair_operators)
    temperature = max(0.01, _solution_cost(current_score) * 0.05)
    cooling = math.exp(math.log(0.01) / max(1, iterations))
    segment_length = max(10, min(30, iterations // 8 or 10))
    point_count = sum(
        len(sortie['route'])
        for schedule in current
        for sortie in schedule['sorties']
    )

    for iteration in range(1, iterations + 1):
        destroy_index, destroy = _select_weighted_operator(
            destroy_operators, destroy_weights, rng
        )
        repair_index, repair = _select_weighted_operator(
            repair_operators, repair_weights, rng
        )
        destroy_usage[destroy_index] += 1
        repair_usage[repair_index] += 1
        candidate = _copy_schedules(current)
        fraction = rng.uniform(0.05, 0.15)
        remove_count = max(
            1,
            min(point_count, 30, math.ceil(point_count * fraction)),
        )
        removed = destroy(candidate, remove_count, rng)
        feasible = repair(
            candidate,
            removed,
            max_distance,
            speed_m_per_minute,
            turnaround_minutes,
            rng,
        )
        reward = 0.0
        if feasible:
            for schedule in candidate:
                _refresh_schedule(schedule, use_two_opt=True)
            candidate_score = _score_schedules(
                candidate, speed_m_per_minute, turnaround_minutes
            )
            candidate_cost = _solution_cost(candidate_score)
            current_cost = _solution_cost(current_score)
            delta = candidate_cost - current_cost
            accepted = (
                delta <= 0
                or rng.random() < math.exp(-delta / max(temperature, 1e-9))
            )
            if accepted:
                current = candidate
                current_score = candidate_score
                reward = 2.0 if delta < 0 else 0.5
            if candidate_score < best_score:
                best = _copy_schedules(candidate)
                best_score = candidate_score
                reward = 8.0

        destroy_rewards[destroy_index] += reward
        repair_rewards[repair_index] += reward
        temperature *= cooling

        if iteration % segment_length == 0:
            reaction = 0.25
            for index in range(len(destroy_weights)):
                performance = (
                    destroy_rewards[index] / destroy_usage[index]
                    if destroy_usage[index]
                    else 0.0
                )
                destroy_weights[index] = max(
                    0.1,
                    (1 - reaction) * destroy_weights[index]
                    + reaction * performance,
                )
            for index in range(len(repair_weights)):
                performance = (
                    repair_rewards[index] / repair_usage[index]
                    if repair_usage[index]
                    else 0.0
                )
                repair_weights[index] = max(
                    0.1,
                    (1 - reaction) * repair_weights[index]
                    + reaction * performance,
                )
            destroy_rewards = [0.0] * len(destroy_operators)
            repair_rewards = [0.0] * len(repair_operators)
            destroy_usage = [0] * len(destroy_operators)
            repair_usage = [0] * len(repair_operators)

        if progress_callback and (
            iteration == iterations or iteration % max(1, iterations // 20) == 0
        ):
            progress_callback(iteration, iterations)

    return best


def _optimize_aircraft_partition(payload):
    """独立优化一架飞机的分区；该函数保持模块级以支持 Windows spawn。"""
    indexed_points = payload['indexed_points']
    aircraft_item = payload['aircraft']
    attempts = payload['attempts']
    early_stop_rounds = payload['early_stop_rounds']
    max_distance = payload['max_distance']
    speed_m_per_minute = payload['speed_m_per_minute']
    turnaround_minutes = payload['turnaround_minutes']

    if not indexed_points:
        return {
            'schedule': {
                'aircraft': aircraft_item,
                'sorties': [],
                'distance_m': 0.0,
            },
            'attempts_run': 0,
        }

    best_schedule = None
    best_score = None
    stale_rounds = 0
    attempts_run = 0
    depots = [aircraft_item['depot']]

    for order in _candidate_orders(indexed_points, depots, attempts):
        attempts_run += 1
        schedules = _build_schedule(
            order,
            [aircraft_item],
            max_distance,
            speed_m_per_minute,
            turnaround_minutes,
        )
        if schedules is None:
            stale_rounds += 1
        else:
            score = _score_schedules(
                schedules,
                speed_m_per_minute,
                turnaround_minutes,
            )
            if best_score is None or score < best_score:
                best_schedule = schedules[0]
                best_score = score
                stale_rounds = 0
            else:
                stale_rounds += 1

        if stale_rounds >= early_stop_rounds:
            break

    if best_schedule is None:
        raise ValueError(
            f"{aircraft_item.get('name') or '飞机'}的分区无法生成有效架次"
        )
    return {
        'schedule': best_schedule,
        'attempts_run': attempts_run,
    }


def plan_multi_base_sorties(
    points,
    aircraft,
    speed_kmh=25.0,
    max_flight_minutes=30.0,
    max_distance_km=None,
    turnaround_minutes=0.0,
    attempts=12,
    early_stop_rounds=3,
    parallel=True,
    progress_callback=None,
    alns_iterations=None,
    random_seed=20260623,
):
    """
    Plan repeated closed sorties for aircraft with different depots.

    The primary objective is minimum makespan: all aircraft start concurrently,
    while sorties belonging to the same aircraft execute sequentially.
    """
    if not aircraft:
        raise ValueError('至少需要一架飞机')
    if speed_kmh <= 0 or max_flight_minutes <= 0:
        raise ValueError('飞行速度和最大飞行时间必须大于 0')
    if max_distance_km is not None and max_distance_km <= 0:
        raise ValueError('单条航线最大长度必须大于 0')
    if turnaround_minutes < 0:
        raise ValueError('再次起飞准备时间不能小于 0')
    if not points:
        raise ValueError('没有可规划的航点')
    if attempts <= 0:
        raise ValueError('优化次数必须大于 0')
    if early_stop_rounds <= 0:
        raise ValueError('提前停止轮数必须大于 0')
    if alns_iterations is not None and alns_iterations <= 0:
        raise ValueError('ALNS 迭代次数必须大于 0')

    normalized_aircraft = []
    for index, item in enumerate(aircraft):
        depot = item.get('depot')
        if not depot or len(depot) != 2:
            raise ValueError(f'第 {index + 1} 架飞机缺少有效起点')
        normalized_aircraft.append({
            **item,
            'index': item.get('index', index + 1),
            'depot': (float(depot[0]), float(depot[1])),
        })

    max_distance = (
        float(max_distance_km) * 1000
        if max_distance_km is not None
        else speed_kmh * 1000 * max_flight_minutes / 60
    )
    speed_m_per_minute = speed_kmh * 1000 / 60
    indexed_points = _deduplicate_indexed_points(points)
    unreachable = [
        point_index
        for point_index, point in indexed_points
        if all(
            2 * euclidean_distance(point, item['depot']) > max_distance + 1e-6
            for item in normalized_aircraft
        )
    ]
    if unreachable:
        limit_text = (
            f'{float(max_distance_km):g} km'
            if max_distance_km is not None
            else f'{max_flight_minutes:g} 分钟续航'
        )
        raise ValueError(
            f'有 {len(unreachable)} 个航点从任一飞机起点往返都超过 '
            f'{limit_text}'
        )

    partitions = _partition_points(
        indexed_points,
        normalized_aircraft,
        max_distance,
    )
    payloads = [
        {
            'indexed_points': partition,
            'aircraft': aircraft_item,
            'attempts': attempts,
            'early_stop_rounds': early_stop_rounds,
            'max_distance': max_distance,
            'speed_m_per_minute': speed_m_per_minute,
            'turnaround_minutes': turnaround_minutes,
        }
        for partition, aircraft_item in zip(partitions, normalized_aircraft)
    ]

    results = [None] * len(payloads)
    completed = 0
    active_count = sum(bool(payload['indexed_points']) for payload in payloads)
    if parallel and active_count > 1:
        try:
            cpu_workers = max(1, (os.cpu_count() or 2) - 1)
            max_workers = min(active_count, cpu_workers)
            spawn_context = multiprocessing.get_context('spawn')
            with ProcessPoolExecutor(
                max_workers=max_workers,
                mp_context=spawn_context,
            ) as executor:
                future_indexes = {
                    executor.submit(_optimize_aircraft_partition, payload): index
                    for index, payload in enumerate(payloads)
                    if payload['indexed_points']
                }
                for future in as_completed(future_indexes):
                    results[future_indexes[future]] = future.result()
                    completed += 1
        except (OSError, PermissionError):
            # 某些受限部署环境禁止创建子进程，自动降级为顺序执行，
            # 保证规划任务仍能完成。
            results = [None] * len(payloads)
            completed = 0
            parallel = False

    if not parallel or active_count <= 1:
        for index, payload in enumerate(payloads):
            if not payload['indexed_points']:
                continue
            results[index] = _optimize_aircraft_partition(payload)
            completed += 1

    best_schedule = []
    for result, aircraft_item in zip(results, normalized_aircraft):
        if result is None:
            best_schedule.append({
                'aircraft': aircraft_item,
                'sorties': [],
                'distance_m': 0.0,
            })
        else:
            best_schedule.append(result['schedule'])

    iterations = (
        int(alns_iterations)
        if alns_iterations is not None
        else max(60, int(attempts) * 20)
    )
    if alns_iterations is None:
        if len(indexed_points) > 400:
            iterations = min(iterations, 160)
        elif len(indexed_points) > 200:
            iterations = min(iterations, 200)
    best_schedule = _run_alns(
        best_schedule,
        max_distance,
        speed_m_per_minute,
        turnaround_minutes,
        iterations,
        random_seed,
        progress_callback=progress_callback,
    )

    result = []
    for schedule in best_schedule:
        aircraft_item = schedule['aircraft']
        elapsed_before = 0.0
        sorties = []
        for sortie_index, sortie in enumerate(schedule['sorties'], start=1):
            flight_minutes = sortie['distance_m'] / speed_m_per_minute
            start_minute = elapsed_before
            end_minute = start_minute + flight_minutes
            sorties.append({
                'sortie_index': sortie_index,
                'point_indexes': [item[0] for item in sortie['route']],
                'distance_m': sortie['distance_m'],
                'flight_time_minutes': flight_minutes,
                'start_minute': start_minute,
                'end_minute': end_minute,
            })
            elapsed_before = end_minute + turnaround_minutes

        completion_minutes = (
            sorties[-1]['end_minute'] if sorties else 0.0
        )
        result.append({
            'aircraft_index': aircraft_item['index'],
            'aircraft_id': aircraft_item.get('id'),
            'aircraft_name': aircraft_item.get('name') or f"飞机{aircraft_item['index']}",
            'plane_sn': aircraft_item.get('plane_sn', ''),
            'depot': aircraft_item['depot'],
            'sortie_count': len(sorties),
            'distance_m': schedule['distance_m'],
            'completion_minutes': completion_minutes,
            'sorties': sorties,
        })

    return {
        'aircraft_schedules': result,
        'makespan_minutes': max(item['completion_minutes'] for item in result),
        'total_distance_m': sum(item['distance_m'] for item in result),
        'total_sorties': sum(item['sortie_count'] for item in result),
        'speed_kmh': speed_kmh,
        'max_flight_minutes': max_flight_minutes,
        'max_sortie_distance_m': max_distance,
        'turnaround_minutes': turnaround_minutes,
        'optimizer': 'ALNS',
        'alns_iterations': iterations,
    }


def plan_multi_aircraft_routes(
    points,
    depot,
    aircraft_count=4,
    speed_kmh=25.0,
    max_flight_minutes=30.0,
    attempts=12,
):
    """Backward-compatible common-depot wrapper."""
    aircraft = [
        {'index': index + 1, 'depot': depot}
        for index in range(aircraft_count)
    ]
    plan = plan_multi_base_sorties(
        points,
        aircraft,
        speed_kmh=speed_kmh,
        max_flight_minutes=max_flight_minutes,
        attempts=attempts,
    )
    routes = []
    for schedule in plan['aircraft_schedules']:
        for sortie in schedule['sorties']:
            routes.append({
                'aircraft_index': schedule['aircraft_index'],
                'sortie_index': sortie['sortie_index'],
                'point_indexes': sortie['point_indexes'],
                'distance_m': sortie['distance_m'],
                'flight_time_minutes': sortie['flight_time_minutes'],
            })
    return routes
