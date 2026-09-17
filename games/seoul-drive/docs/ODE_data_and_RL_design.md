# 오드(ODE) 학습 데이터·라벨링·강화학습 설계 (u_5268, 2026-09-17)

> 오너 지시: "자율주행 학습용 데이터 설계 최신 방법론, 로우 데이터 수집, 라벨링·라벨링 자동화,
> 강화학습에 대한 내용을 최신 트렌드에 맞게 설계하고 문서화."
> 대상 = 서울드라이브 시뮬레이터 위의 오드(ODE). 현 자산(교사 GEOM/teacher.js, DAgger,
> reward.py/ppo.py, /tel 텔레메트리)을 버리지 않고 그 위에 얹는 설계다.

## 0. 한 장 요약

```
교사(규칙) ──시연──▶ 로우 로그(프레임+텔레메트리+이벤트) ──자동라벨──▶ 학습셋
                                      ▲                              │
                                      │ DAgger(모델이 몰고 교사가 정답)  ▼
                                  오드 v_n ◀── BC 사전학습 ◀────────────┘
                                      │
                       폐루프 RL 미세조정(residual, 안전필터) ─▶ 오드 v_{n+1}
                                      │
                           평가(도착·사고0·법규) → 롱테일 채굴 → 다시 수집
```
- **데이터의 단위는 프레임이 아니라 '시나리오'** 다. 60지점 30구간 같은 커버리지 설계가 먼저다.
- **라벨은 사람이 안 단다.** 시뮬레이터가 진실값을 알고 있으므로 100% 자동 라벨 + 규칙 검증.
- **BC → DAgger → RL 미세조정** 순서. RL 은 처음부터가 아니라 IL 사전학습 위의 residual.
- **성공 기준은 지표가 아니라 도착·사고 0·법규 준수**(rules/model-drives-not-logic.md).

---

## 1. 최신 방법론 요약 (조사 결과 → 오드 적용점)

| 트렌드 | 내용 | 오드 적용 |
|---|---|---|
| End-to-End 주행 + 데이터 스케일링 | 화면→행동 직접 학습. 데이터 양·다양성이 성능을 지배(Data Scaling Laws for E2E AD, 2025) | 프레임 수보다 **구간·상황 다양성**을 늘린다. 같은 강남→시청 반복은 가치가 낮다 |
| 데이터 엔진 / 자동 라벨링 | 오프라인 자동 라벨 파이프라인(NVIDIA, AIDE CVPR'24), VLM 보조 라벨·검증 | 시뮬이 진실값을 알므로 오프라인 자동 라벨이 기본. VLM 은 **롱테일 태깅·QA** 에만 |
| 롱테일 채굴 / 능동학습 | VLMine, ActiveAD: 실패·불확실 구간만 골라 라벨 예산 절감(2~4×) | 사고·복귀·급제동·불확실(엔트로피↑) 프레임 우선 수집 |
| DAgger 변형 | 불확실도 기반 교사 질의, 필터링(MEGA-DAgger), 연속 보정(Residual DAgger) | 지금 dagger.py 에 **불확실도 게이트 + 라벨 필터** 추가 |
| 폐루프 RL 미세조정 | IL 사전학습 → RL 로 residual 학습, 충돌·이탈 지표 개선(Waymax/V-Max/CLEAR 2025~26) | ppo.py 를 **residual 정책**으로 재구성, 안전필터(CIMRL 식) 동반 |
| 월드모델 | 미래 프레임 예측으로 자기지도 표현학습·가상 시나리오 생성 | 2단계 과제. 먼저 시뮬 자체가 월드모델 역할(무료 롤아웃) |
| 추론 중심 데이터(VLA) | 상황 설명·이유 라벨(DriveLMM-o1, Alpamayo-R1) | 이벤트 태그(왜 감속했나)를 라벨에 남긴다 — 후에 VLA 로 확장 가능 |

---

## 2. 학습 데이터 설계

### 2.1 관측(입력) 스키마 — 현 자산 유지 + 확장
```
obs = {
  img      : 256x256x3  (상단 HUD 잘라낸 캔버스, net.py preprocess)      # 현재
  img_hist : 직전 2프레임(6ch) 또는 프레임차                              # 추가: 속도·상대운동
  state    : [v, steer_prev, thr_prev, brake_prev]                        # 추가: 저차원 상태
  nav      : [다음 회전 방향 onehot(S/L/R/U), 거리 aD/200, 목표차로 fin/nl, 현재차로 laneF/nl]  # 추가
}
```
- `nav` 는 실차의 내비 명령에 해당한다. 없으면 모델이 "어디로 갈지"를 화면만으로 추측해야 해서
  교차로마다 라벨이 모순된다(같은 화면, 다른 정답). **가장 값싸고 효과 큰 추가.**
- 전부 `/tel` 의 g2(aTurn, aD, fin, laneF, nl)로 이미 나온다 — 새 계측 불필요.

### 2.2 행동(라벨) 스키마
```
act = [steer(-1..1), thr(0..1), brake(0..1)]      # 현재 Y[:, :3]
aux = [wantStop(0/1), targetLane(idx), reason(enum)] # 보조목표(멀티태스크)
```
- `reason` ∈ {none, lead, ped, signal, turn_prep, lane_change, avoid, overtake, kturn, stall}.
  교사가 왜 그 행동을 냈는지. **라벨 정합성 검사와 롱테일 채굴의 키.**

### 2.3 시나리오 커버리지 (프레임 수 대신 이걸 센다)
| 축 | 값 | 최소 수집량(에피소드) |
|---|---|---|
| 도로 | 일방 1~4차로 / 왕복 1차로(6.5m) / 왕복 3차로+ / 램프·합류 | 각 30 |
| 조작 | 직진 / 좌·우회전 / 차선변경 / 유턴 / 3점회전 / 회피 / 추월 | 각 30 |
| 교통 | 신호 정지·출발 / 앞차 추종·정체 / 보행자(정상·무단횡단) | 각 30 |
| 밀도 | traffic light/medium/heavy | 각 1/3 |
| 시작 상태 | 정상 차로 / **의도적 이탈(0.5~2m)** / 저속·정지 | 정상 70%, 이탈 20%, 정지 10% |

- "의도적 이탈"이 핵심이다. 학습 8.5만 프레임 전부 on_road=1.00 이라 복구를 못 배웠다
  (rules/ode-teacher-todo.md A5). 교사가 **벗어난 상태에서 돌아오는 것**을 시연해야 한다.
- 커버리지 표는 `data/<set>/manifest.json` 에 자동 집계 → 부족 칸이 다음 수집 대상.

### 2.4 품질 게이트 (쓰레기 데이터 금지, rules/seoul-drive-workflow.md §2)
수집 에피소드는 아래를 통과해야 학습셋에 들어간다.
```
정지 프레임 비율 < 30%      (v<0.3 인 프레임. 23만 정지 프레임을 버린 적이 있다)
사고 0 또는 불가항력만      (crk 에 '무단횡단 불가항력' 외 항목 없음)
법규: 중앙선 0 · 회전차로 ≥ 95% · 차선물기(무단) < 5%
라벨 정합: |steer| 평균 < 0.5 (기존 셋 +0.95 = 한쪽 고정 조향 = 폐기)
텔레메트리 결손 0 (nav/g2 None 프레임은 버림)
```

---

## 3. 로우 데이터 수집

### 3.1 무엇을 남기나 (로우 = 재라벨 가능해야 한다)
```
data/raw/<date>/<episode_id>/
  frames/000123.jpg          256x256 (또는 원본 캔버스 PNG, 재전처리용)
  tel.jsonl                  프레임별 /tel 스냅샷 전체(top, tch, g2)  ← 라벨의 원천
  events.jsonl               사고·복귀·급제동·회피·추월·신호·보행자 이벤트(시각+종류)
  route.json                 출발/도착, wp 수, routeM, uturnHops, ktN, seed
  meta.json                  build hash, teacher 버전, traffic 밀도, 시작상태(정상/이탈), 결과
```
- 라벨을 로우에 굽지 않는다. **라벨 규칙이 바뀌면 재생성**(오늘 하루에만 판정 규칙이 5번 바뀌었다).
- 시각 동기: 프레임 캡처와 /tel 스냅샷은 같은 loop tick 에서 뽑는다(`loadId`+frame idx 로 결합).
- 결정성: 교통·보행자 난수 seed 를 meta 에 남겨 재현 가능하게 한다.

### 3.2 누가 모는가 (수집 모드)
| 모드 | 운전자 | 용도 | 비율 |
|---|---|---|---|
| Teacher | GEOM+teacher.js | BC 사전학습, 커버리지 채우기 | 40% |
| DAgger | 오드 v_n, 교사가 라벨 | 공변량 이동 교정(모델이 실제로 가는 상태) | 40% |
| Perturbed | 교사 + 주입 외란(조향 노이즈·시작 이탈) | 복구 시연 | 15% |
| Hard-case replay | 실패 시나리오 재현(seed 고정) | 롱테일 | 5% |

### 3.3 수집 하네스 (기존 스크립트 재사용)
- `sweep_test.py --pairs` = 커버리지 수집기. 결과 JSON → manifest 집계.
- `dagger.py` = DAgger 수집기. **추가할 것**: 불확실도 게이트(정책 엔트로피/앙상블 분산 상위 30% 프레임만 교사 질의·저장), 라벨 필터(교사 지령이 blockT·stall 상태면 폐기).
- `focus_test.py` = 실패 시나리오 재현·캡처(이미 이벤트마다 스크린샷).
- 수집 중 리로드 금지·리로드는 `reload.sh` 준비 폴링만 사용(콜드 로드 33~39초).

---

## 4. 라벨링 및 자동화

### 4.1 원칙: 시뮬레이터가 진실값이다
사람이 박스를 그릴 일이 없다. 라벨은 **/tel 로부터 결정론적으로 계산**하고, 규칙으로 검증한다.
```
label(frame) = f(tel[frame], tel[frame+1..+k], events)
```

### 4.2 자동 라벨 계층
| 계층 | 산출 | 출처 | 검증 |
|---|---|---|---|
| L0 행동 | steer/thr/brake | 교사 지령(tch.st/th/br), DAgger 면 교사 |  최상위 brk/st(적용값)와 혼동 금지 |
| L1 의도 | reason enum, wantStop | tch.gap/ped/sig/cap, g2.aTurn/fin, da.vmax | 물리 검산: ped 사고인데 조우 0 이면 계측 고장 |
| L2 상태 | 차로(laneF), 도로 좌표 nlat, 중앙선/이탈 여부 | g2 + 게임 onroad 판정 | 게임 자체 판정과 대조(불일치 5% 넘으면 규칙 오류) |
| L3 이벤트 | 사고·복귀·급제동·회피·추월·신호위반 | crk/tpN/blk*/events | 이벤트 수 = 설계 기대치와 비교(JAY_P×fps×초) |
| L4 서술 | 상황 한 줄(예: "왕복1차로, 앞차 12m 정체, 보행자 없음, 좌회전 40m") | L1~L3 템플릿 | VLM 은 **QA 표본 검사**(5%)만 |

### 4.3 라벨 QA 자동 규칙 (B2 교훈 반영)
1. 실제 키를 찍는다(`tch` 는 평평하다; `tch.d` 는 조향항).
2. 게임 자체 판정과 대조한다(onroad/crk).
3. 물리 검산(정지거리 `v·0.7 + v²/8`, 조향 분포, 속도 분포).
4. 분포 드리프트 경보: 새 셋의 steer/thr/brake 히스토그램이 기준셋과 KL > 0.2 면 사람 확인.

### 4.4 롱테일 채굴 (라벨 예산이 아니라 '수집 예산'을 아낀다)
- 우선순위 점수 = 사고·복귀 발생(+10) · 교사 급제동(+3) · 정책 불확실도 상위(+2) · 희소 셀(커버리지 부족, +2).
- 상위 시나리오는 seed 고정으로 재현·재수집(3.2 Hard-case replay).
- VLM 태깅은 여기서만 쓴다: 이벤트 프레임에 "왜 실패했나" 자연어 태그 → 사람 검토용.

---

## 5. 강화학습 설계

### 5.1 왜 RL 인가 (실측)
BC 는 교사 복제이고 '도착' 개념이 없다. v6~v14 전부 v5 보다 못했다(ppo.py 주석). 사고의 대부분이
차로이탈 = 교사가 시연 못 한 상태. RL 은 결과(도착·무사고)를 직접 최적화한다.

### 5.2 구조: IL 사전학습 + residual RL + 안전필터 (2025~26 주류)
```
a = clip( a_IL(obs) + π_res(obs) ,  안전필터 )
```
- `a_IL` = DAgger 로 학습한 오드(고정 또는 저 lr). `π_res` = 작은 보정 정책(초기 0).
- 안전필터 = 교사의 제동 거부권(teacher veto)만 남긴다: 정지거리 안 보행자·앞차·적신호면 brake=1.
  → 탐색 중 대형사고를 막아 학습이 무너지지 않게(CIMRL 방식).
- 처음부터 RL(현 ppo.py 가우시안 3차원 연속)은 정지 최적해에 빠졌다 — residual 은 시작점이 이미 '가는' 정책이라 그 함정을 피한다.

### 5.3 보상 (reward.py 원칙 유지, 항목만 정리)
| 항 | 값 | 근거 |
|---|---|---|
| 진행 | +Δprogress × W (완주 ≈ +2720 > 정지 0) | 속도 보상 금지(경로 이탈 유도) |
| 도착 | +큰 종단 보상 | 도착이 0 회였다 |
| 사고 | 종류별 −(차로이탈 > 추돌 > 보행자는 최대) | crk 실측 비율 |
| 이탈 전조 | −k·max(0, |xt|−margin) | 사고 전에 신호 |
| 정지 | −per-second (정지 의도 없을 때만: vmax>1, gap>정지거리, 적신호 아님) | 오늘 고친 '정상정지≠갇힘' 과 같은 규칙 |
| 법규 | 중앙선 −, 회전차로 위반 −, 신호위반 − | 도로교통법 = 룰 |
| 추월 | +0.5 (아주 작게) | 추월 자체를 목적화 방지 |

### 5.4 에피소드·커리큘럼
- 에피소드 = 소프트리셋 + 45~120초(리로드 없음). 시작 상태 분포 = 2.3 표(정상/이탈/정지).
- 커리큘럼은 **난이도 증가만**: 직진 → 회전 → 좁은 도로/유턴 → 밀집 교통. 
  단, '정지가 최적'이 되는 단계(사고 벌점만 있는 단계)를 두지 않는다(rules/ode-training-pitfalls).
- 병렬화: 브라우저 1개 = 1 env. 폐루프 RL 에는 부족하다 → 헤드리스 캔버스 N개(같은 build) 또는
  Waymax/GPUDrive 류 벡터화 시뮬 도입은 2단계 과제(단, 지도·규칙을 옮겨야 함).

### 5.5 평가 (성공 = 도착·사고 0·법규)
```
고정 벤치: 강남역→시청역 + 문제 구간 3개 + 랜덤 30구간 (seed 고정)
지표: 도착률, 사고/10km(종류별), 복귀/10km, 회전차로 준수, 차선물기(무단), 평균 속도
게이트: 도착률 ≥ 90% · 사고 0 · 복귀 0 이면 다음 버전 승격
```
오드가 몰 때만 성과다(DRV=GEOM 은 성과가 아님, rules/ode-driving-model.md).

---

## 6. 실행 순서 (다음 세션부터)
1. `nav` 입력 추가 + `reason` 보조라벨 → `net.py`, `dagger.py`, `train_straight.py` 반영.
2. 로우 로그 포맷(3.1) 도입: 프레임 + tel.jsonl + events.jsonl. 라벨은 별도 `label.py` 로 생성.
3. 커버리지 manifest + 품질 게이트(2.4) 자동화 → `sweep_test.py` 출력에 붙인다.
4. 교사 시연 수집(정상 70 / 이탈 20 / 정지 10) → BC v_next.
5. DAgger 3~5 라운드(불확실도 게이트) → 평가 게이트.
6. residual RL 미세조정(안전필터 포함) → 평가 게이트 → 오드 v2.
7. 월드모델·벡터화 시뮬은 6 이후.

## 7. 참고
- Data Scaling Laws for End-to-End Autonomous Driving — https://arxiv.org/pdf/2504.04338
- NVIDIA auto-labeling pipeline — https://developer.nvidia.com/blog/developing-an-end-to-end-auto-labeling-pipeline-for-autonomous-vehicle-perception/
- VLMine (VLM 롱테일 채굴) — https://arxiv.org/pdf/2409.15486
- CAR-Scenes (VLM 라벨 + 커버리지 감사) — https://arxiv.org/abs/2511.10701
- DAgger 변형(불확실도·필터·residual) — https://www.emergentmind.com/topics/dataset-aggregation-dagger
- Uncertainty-Aware DAgger — https://arxiv.org/pdf/1905.02780
- CIMRL (IL+RL+안전필터) — https://arxiv.org/pdf/2406.08878
- RL fine-tuning after IL (residual, waypoint space) — https://arxiv.org/pdf/2409.18343
- CLEAR: closed-loop RL at scale — https://arxiv.org/pdf/2607.02841
- Waymax / V-Max — https://arxiv.org/pdf/2310.08710 , https://arxiv.org/pdf/2503.08388
- World models survey — https://arxiv.org/abs/2501.11260
- E2E AD survey — https://arxiv.org/html/2306.16927v3
