#!/usr/bin/env python3
"""a_5124 T1 — 주행 보상함수. /tel 텔레메트리만으로 계산한다(새 계측 불필요).

★설계 원칙: 오늘 실측된 실패양상을 하나씩 정면으로 벌한다. 임의 가중치 금지.

측정된 실패양상(무엇을 벌해야 하는가):
  1. 차로이탈이 사고의 전부다 — /tel crk 실측 {차로이탈:39, 추돌:8, 보행자:1}.
     => 사고는 '종류별로' 벌한다. 차로이탈이 가장 무겁다.
  2. 진행률이 0.176~0.180 에서 멈춘다(a_5111 실측, 3/3 런).
     => '정지'는 사고가 아니지만 실패다. 시간·정지 벌점이 없으면
        BC 모델처럼 v=0 으로 서 있는 것이 최적해가 된다(a_5106 실측: v=0, cr=0).
  3. xt(중심선 횡거리)가 margin 을 넘으면 이탈이다(a_5111: 1차로 margin 1.63m 에
     xt 2.55m). => 사고가 '나기 전에' xt 를 벌해야 학습신호가 조기에 생긴다.
  4. 도착이 한 번도 없었다(0/다수). => 도착은 크고 종단적인 보상.

★게임화(gaming) 방지 — 브리핑의 경고를 그대로 반영:
  · "사고 안 나면 +" 형태의 항은 없다. 서 있으면 STALL 벌점만 쌓인다.
  · 전진 보상은 '경로 진행률 증가분'이지 속도가 아니다. 속도 보상을 주면
    경로를 벗어나 빨리 달리는 것이 이득이 된다.
  · 추월 보상은 아주 작게(0.5). 크게 주면 추월 자체를 목적으로 삼아
    불필요하게 차로를 바꾼다.
"""

# ---- 계수(근거를 각 줄에 남긴다) ----
# ★u_5172 실측 재조정. 기존 100/200 은 PPO 를 돌리면 '정지'를 학습시킨다.
#   근거: v5 실측이 km당 사고 5회 → 11.4km 완주 시 사고 57회.
#     진행보상 +100, 사고벌점 57x40 = -2280 → 완주해도 -2180 점.
#     가만히 있으면 0 점이므로 정지가 최적해가 된다.
#   ⇒ 완주가 정지보다 확실히 이득이 되도록 진행 보상을 올린다.
#     사고 벌점을 낮추는 방향은 쓰지 않는다(안전을 포기하게 된다).
#     3000 이면 완주 +3000 - 2280 = +720 > 0. 사고를 줄일수록 더 벌어진다.
W_PROGRESS = 3000.0  # 진행률 1.0 완주 = +3000. 1m 당 +0.264.
W_ARRIVE   = 2000.0  # 도착 종단보상. '거의 다 가기'보다 '도착'이 이득이어야 한다.
W_XT       = 2.0     # margin 초과분 1m 당 -2. 사고 전에 미리 밀어낸다.
W_STALL    = 1.0     # 정지 1초당 -1. 0.176 정체를 직접 벌한다.
W_TIME     = 0.05    # 1초당 -0.05. 기어가기 방지(단, 신호대기까지 과벌하지 않게 작게).
W_OVERTAKE = 0.5     # 추월 1회 +0.5. 작게 — 목적이 아니라 부산물이어야 한다.

# 사고 종류별 벌점 — 빈도가 아니라 '위험도+빈도' 순.
CRASH_W = {
    '보행자':  120.0,   # 사람. 빈도(1)는 낮지만 절대 허용 불가 → 최대 벌점.
    '중앙선':   60.0,   # 역주행. 대형사고 직결.
    '차로이탈': 50.0,   # 실측 사고의 대부분(39/48). 주 타깃.
    '추돌':     40.0,   # 8/48.
    '건물':     40.0,
    '기타':     20.0,
}
STALL_V = 0.5        # m/s 미만이면 정지로 본다(decode v 단위와 동일)


def crash_penalty(crk_before, crk_after):
    """사고 종류별 증가분에 가중치를 곱해 합산한다."""
    p = 0.0
    for k, w in CRASH_W.items():
        d = int(crk_after.get(k, 0)) - int(crk_before.get(k, 0))
        if d > 0:
            p += w * d
    # 알려지지 않은 새 종류가 생겨도 놓치지 않는다
    for k in crk_after:
        if k not in CRASH_W:
            d = int(crk_after.get(k, 0)) - int(crk_before.get(k, 0))
            if d > 0:
                p += CRASH_W['기타'] * d
    return p


def xt_penalty(lde_new):
    """이번 스텝에 새로 기록된 이탈 기하에서 margin 초과분을 벌한다.

    lde 항목: {xt, margin, ...}. xt<=margin 이면 0(차도 안).
    """
    p = 0.0
    for r in lde_new:
        try:
            over = float(r.get('xt', 0)) - float(r.get('margin', 0))
        except (TypeError, ValueError):
            continue
        if over > 0:
            p += W_XT * over
    return p


def step_reward(prev, cur, dt):
    """한 스텝 보상. prev/cur = /tel 스냅샷(dict), dt = 경과초.

    반환: (reward, terms) — terms 는 항목별 기여도(디버깅·보고용).
    """
    terms = {}

    # + 경로 진행률 증가분. 실제 목적 그 자체.
    dprog = float(cur.get('prog', 0)) - float(prev.get('prog', 0))
    # ★리셋(대파/재시작)으로 prog 가 뒤로 튀는 건 '후퇴'가 아니다 → 0 으로 막는다.
    if dprog < -0.5:
        dprog = 0.0
    terms['progress'] = W_PROGRESS * dprog

    # - 사고(종류별)
    terms['crash'] = -crash_penalty(prev.get('crk', {}) or {}, cur.get('crk', {}) or {})

    # - 차도 밖으로 나간 정도(사고 전 조기신호)
    pl, cl = prev.get('lde', []) or [], cur.get('lde', []) or []
    terms['xt'] = -xt_penalty(cl[len(pl):] if len(cl) >= len(pl) else cl)

    # - 정지/시간
    v = float(cur.get('v', 0))
    terms['stall'] = -(W_STALL * dt) if v < STALL_V else 0.0
    terms['time'] = -W_TIME * dt

    # + 추월(부산물로만)
    dot = int(cur.get('otN', 0)) - int(prev.get('otN', 0))
    terms['overtake'] = W_OVERTAKE * max(0, dot)

    return sum(terms.values()), terms


def terminal_reward(arrived):
    """종단 보상. 도착만 크게 준다. '사고 없이 서 있기'에는 아무 보상도 없다."""
    return W_ARRIVE if arrived else 0.0


if __name__ == '__main__':
    # 자기검증: 설계 의도가 수식으로 지켜지는지 확인한다.
    idle = ({'prog': .176, 'v': 0, 'crk': {}, 'lde': [], 'otN': 0},
            {'prog': .176, 'v': 0, 'crk': {}, 'lde': [], 'otN': 0})
    move = ({'prog': .176, 'v': 6, 'crk': {}, 'lde': [], 'otN': 0},
            {'prog': .200, 'v': 6, 'crk': {}, 'lde': [], 'otN': 0})
    crash = ({'prog': .200, 'v': 6, 'crk': {}, 'lde': [], 'otN': 0},
             {'prog': .200, 'v': 6, 'crk': {'차로이탈': 1}, 'lde': [], 'otN': 0})
    for nm, (a, b) in (('idle 1s', idle), ('progress +0.024', move), ('lane-departure', crash)):
        r, t = step_reward(a, b, 1.0)
        print('%-18s r=%+8.3f  %s' % (nm, r, {k: round(v, 3) for k, v in t.items() if v}))
    print('arrival bonus = %+.1f' % terminal_reward(True))
