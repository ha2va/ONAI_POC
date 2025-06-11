from datetime import datetime, timedelta
from database import query_db


def find_plans(origin_id, dest_id):
    """주어진 출발지와 도착지 사이의 가능한 모든 경로를 찾는다."""

    # 모든 Route 정보를 조회하여 그래프 형태로 변환
    routes = query_db(
        "SELECT r.id, r.origin_id, o.name as origin_name, r.destination_id, d.name as destination_name, r.base_cost, r.lead_time "
        "FROM Route r "
        "LEFT JOIN Location o ON r.origin_id=o.id "
        "LEFT JOIN Location d ON r.destination_id=d.id"
    )

    # 인접 리스트 형태의 그래프 생성
    adj = {}
    for r in routes:
        adj.setdefault(r['origin_id'], []).append(r)

    plans = []

    def dfs(current, path, visited):
        """깊이 우선 탐색으로 경로를 추적한다."""
        # 목적지에 도달하면 현재까지의 경로를 저장
        if current == dest_id:
            plans.append(list(path))
            return
        # 현재 노드에서 갈 수 있는 모든 노드를 순회
        for r in adj.get(current, []):
            # 이미 방문한 노드는 다시 방문하지 않음으로써 순환 방지
            if r['destination_id'] not in visited:
                visited.add(r['destination_id'])
                path.append(r)
                dfs(r['destination_id'], path, visited)
                path.pop()
                visited.remove(r['destination_id'])

    # 탐색 시작
    dfs(origin_id, [], {origin_id})

    # 경로별 총 리드타임 계산
    result = []
    for plan_routes in plans:
        total_lead = sum(r['lead_time'] or 0 for r in plan_routes)
        result.append({'routes': plan_routes, 'total_lead_time': total_lead})
    return result


def get_tariff_info(route_id, date_str):
    """특정 날짜에 적용되는 운임 정보를 반환"""
    return query_db(
        "SELECT id, cost FROM Tariff WHERE route_id=? AND date(?) BETWEEN valid_from AND valid_to",
        [route_id, date_str], one=True)


def get_tariff_cost(route_id, date_str):
    info = get_tariff_info(route_id, date_str)
    return info['cost'] if info else None


def recommend_plans(origin_id, dest_id, start_date, end_date):
    """모든 경로에 대해 비용과 시작일을 계산하여 추천"""
    plans = find_plans(origin_id, dest_id)
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    for plan in plans:
        best_cost = None
        best_date = None
        date = start_dt
        last_start = end_dt - timedelta(days=plan['total_lead_time'])
        best_costs = None
        best_ids = None
        while date <= last_start:
            total = 0
            costs = []
            ids = []
            valid = True
            for r in plan['routes']:
                info = get_tariff_info(r['id'], date.strftime('%Y-%m-%d'))
                if info is None:
                    valid = False
                    break
                costs.append(info['cost'])
                ids.append(info['id'])
                total += info['cost']
            if valid and (best_cost is None or total < best_cost):
                best_cost = total
                best_date = date
                best_costs = costs
                best_ids = ids
            date += timedelta(days=1)
        plan['total_cost'] = round(best_cost, 2) if best_cost is not None else None
        plan['recommended_start'] = best_date.strftime('%Y-%m-%d') if best_date else None
        if best_costs:
            for r, c, tid in zip(plan['routes'], best_costs, best_ids):
                r['tariff_cost'] = round(c, 2)
                r['tariff_id'] = tid
    plans.sort(key=lambda p: (p['total_cost'] if p['total_cost'] is not None else float('inf')))
    return plans
