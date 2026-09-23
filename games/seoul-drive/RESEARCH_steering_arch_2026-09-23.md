# 조향 아키텍처 연구 메모 — 지각 헤드+규칙 제어기 vs 앞점 BC 개선 (2026-09-23)

대상: 오드(ODE) 2D 톱다운, 256px 입력, 24~30fps, CoreML 0.4ms, 라벨 = `/tel`.
현재: DriveNet → lp10/20/40/80(+전방거리) → 규칙 추종기. 실측(ar_5588): lp20 부호 반전 9~14회/s, 프레임 간 점프 p90≈1m, 26~37% 프레임이 >0.5m 점프, 핸드오버 2~5/min, 코너 조향률 규칙 대비 3~20배, 동일 구간 DAgger(mp4)·경로의도 조건(vdim8) 모두 이득 없음.

---

## Q1. 모듈형(지각→규칙/MPC) vs 종단간 BC — 폐루프 안정성 근거

**발견**
- 폐루프 성적이 좋은 시스템은 전부 **"기하/궤적을 내고, 규칙 제어기가 조향을 만든다."** 단일 프레임에서 조향각을 직접 내는 것은 PilotNet(2016)·CIL(2018)뿐이고 둘 다 폐루프 한계가 보고됐다.
  - openpilot: 차선 기반 고전 지각 → 3D 궤적(x,y,z m) 예측으로 바꿨고, 조향은 여전히 controls 스택(MPC)이 계산. 순진한 E2E 는 "사람의 최빈 궤적"만 배워 이탈 복구를 모름 → 시뮬 교란으로 복구를 명시 학습. https://blog.comma.ai/end-to-end-lateral-planning/ (2021)
  - Mobileye RSS: 학습 정책과 독립된 형식적 규칙 안전층(안전거리·끼어들기·우선권). 우리 Layer 1 과 같은 구조. https://arxiv.org/abs/1708.06374 (2017), https://www.mobileye.com/technology/responsibility-sensitive-safety/
  - Learning by Cheating: 특권 교사(BEV 정답)→ 비전 학생, K개 웨이포인트 히트맵 → **모든 점에 호(arc)를 맞춰 그 위 한 점을 향해 PID 조향**. 학생은 교사에게 임의 상태에서 질의(DAgger식). CARLA 100%·NoCrash 신기록. https://arxiv.org/abs/1912.12294 (2019)
  - CIL: 명령(follow/left/right/straight) 조건 + 조향·스로틀 직접 출력. 수집 중 시간상관 조향 잡음 주입으로 복구 시연. https://arxiv.org/abs/1710.02410 (2018)
  - CILRS: BC 한계 실증 — 정지 데이터 과다로 "저속↔무가속" 허위 상관(inertia), 동일 하이퍼파라미터·시드만 달라도 성적 **42%** 편차, 데이터 늘려도 정체·악화, 동적 물체에서 55~66% 하락. https://arxiv.org/abs/1904.08980 (2019)
  - ChauffeurNet: 입력 = 톱다운 렌더(도로·신호·경로·과거 자세), 출력 = 0.2s 간격 10점(2s) 자세, 컨트롤러가 실행. **궤적 중점 횡 ±0.5m·헤딩 ±π/3 교란**, 교란 표본 가중 1/10, 곡률 상한 필터. 이탈 복구 0%→100%, 정차 차량 회피 20%→90%. https://arxiv.org/abs/1812.03079 (2018)
  - DAgger: BC 오차는 T²로 누적, 자기 분포에서 교사 라벨을 모아 no-regret 보장. https://arxiv.org/abs/1011.0686 (2011)
  - PilotNet: 픽셀→조향 직접, 3카메라 + 인공 이동·회전 증강(**σ = 사람 운전 표준편차의 2배**, 라벨 = "2초 안에 복귀"하는 조향). https://arxiv.org/abs/1604.07316 (2016)
  - TCP: 궤적 브랜치 + 제어 브랜치, 궤적은 PID 로 변환. **회전에서 궤적+PID 가 약함**(도로이탈 위반의 64.2%가 회전) → 회전 중엔 제어 브랜치 0.7 가중. https://arxiv.org/abs/2206.08129 (2022)
  - InterFuser: 웨이포인트 + 물체 밀도맵·신호 등 해석 가능한 중간 출력으로 **안전 제어기가 행동을 제약**. https://arxiv.org/abs/2207.14024 (2022)
  - TransFuser: GRU 가 목표점(goal)을 입력받아 4개 웨이포인트 자기회귀 예측, 횡 PID 는 웨이포인트 방향, 종 PID 는 간격. 보조 과제(깊이·분할·HD맵·검출). https://arxiv.org/abs/2205.15997 (2022)
  - LAV: 명령 6종 + 50~100m 간격 GNSS 목표점, 10점 웨이포인트, PID 2개, 충돌 감지 비상제동. https://arxiv.org/abs/2203.11934 (2022)

**오드 적용**: 우리도 이미 "점 → 규칙 추종기" 구조라 큰 틀은 문헌과 같다. 차이는 **모델이 내는 양**이다. lp40/80 은 그림에 없는 경로 의도에 좌우돼(MAE 4~10m) 프레임마다 다른 답을 내고, 추종기는 그 잡음을 그대로 조향에 싣는다. 문헌의 승자들은 짧은 시평(LbC K점, ChauffeurNet 2s, TransFuser 4점)만 모델에 맡기고 먼 곳은 목표점/명령으로 넘겼다.

**판정**: 모듈형 우세. 단, "조향각 직접 출력"이 아니라 **관측 가능한 차로 기하(횡오차·헤딩오차·곡률·차로 인덱스)를 내고 규칙(Stanley/Pure Pursuit)이 조향**하는 형태.

## Q2. 갈지자·진동의 원인과 처방

**발견**
- 인과 혼동: 관측이 많을수록 허위 상관을 배워 분포 이동에서 무너짐(브레이크등 예). 처방 = 개입·질의로 인과 모델 식별. https://arxiv.org/abs/1905.11979 (2019)
- 복사꾼(copycat): 관측 이력을 넣으면 **직전 행동을 베끼는** 지름길 학습 → 시간 프레임 스택/이전 조향 입력은 위험. https://arxiv.org/abs/2010.14876 (2020)
- Pure Pursuit 앞점 거리 = 감쇠계수: 짧으면 2차계 진동, 길면 완만 수렴하되 곡선을 못 따름; 조향 1차 지연 때문에 복귀가 늦음. Coulter, CMU-RI-TR-92-01 https://publications.ri.cmu.edu/storage/publications/pub_files/pub3/coulter_r_craig_1992_1/coulter_r_craig_1992_1.pdf (1992)
- 행동 청킹·시간 앙상블(ACT): 한 번에 k 스텝 예측, 매 스텝 재질의해 겹치는 예측을 w_i=exp(−m·i) 로 평균 → 오차 누적 감소·부드러움. k=1→100 에서 성공 1%→44%, 앙상블 +3~4%p. https://arxiv.org/abs/2304.13705 (2023)
- TCP 의 "궤적+PID 는 회전에서 약함", CILRS 의 "학습 시드만으로 42% 편차"는 우리 lp 실험(모델 간 차이 = 잡음, 코너 3~20배 거침)과 정확히 같은 현상.

**오드 적용**: 반전 9~14회/s 는 제어기 진동이 아니라 **모델 출력의 프레임 간 분산**이다(규칙 추종기는 같은 경로선으로 3.4회/min). 처방 순서 — (1) 출력을 관측 가능한 양으로 바꿔 분산 자체를 줄인다, (2) 시간 앙상블(자차 이동 보정 후 최근 3~5프레임 지수 가중 평균; 프레임 스택 입력은 금지 — copycat), (3) 앞점 거리 = 속도 비례 + 오차 클 때 길게(Coulter 감쇠), (4) 조향률 상한.

**판정**: 스무딩은 필요조건이지 해법이 아니다. 근본은 출력 정의.

## Q3. 데이터 — 무작위 구간+자세 교란 vs 고정 경로

**발견**: ChauffeurNet 횡 ±0.5m·헤딩 ±60°(교란 표본 가중 1/10) / PilotNet σ=사람 2배·2초 복귀 라벨 / CIL 시간상관 조향 잡음 / LbC·DAgger 는 학생 분포에서 교사 질의 / openpilot 은 시뮬 교란 없이는 복구 불가. 검증은 CARLA 계열 전부 **미학습 타운·날씨**(CILRS·TransFuser·LAV).

**오드 적용**: 우리 "동일 3구간 DAgger 무이득"은 문헌과 일치 — 분포가 안 넓어졌다. 오너 u_5596("장소가 아니라 유사한 곳의 규칙")과 같은 결론. 기하 라벨의 장점: 교란 상태에서도 라벨(차로 대비 내 위치)이 **정답 그대로**라 "2초 복귀" 같은 인위 라벨이 필요 없다.

## Q4. 회전 준비 구간의 의도 모호성

**발견**: CIL/LbC/LAV = 이산 명령(+분기 헤드), TransFuser/LAV = 목표점, ChauffeurNet = 경로를 그림에 렌더. 어느 쪽이든 **의도는 교차로 근처에서만 의미**가 있고 직진(T0)에서는 무관 — vdim8 이 T0 에서 무이득인 것과 일치(PLAN §9-C mp3c vs mp3c8).

**오드 적용**: 우리는 톱다운이라 경로선을 그림에 그릴 수도 있지만, 그러면 모델이 경로선을 베끼는 지름길(사실상 규칙 추종기 복제)이 된다. 가장 깨끗한 분리: **모델은 "차로가 어디 있나"(차로 기하·인덱스·차로수)만 답하고, 목표 차로 선택은 Layer 3 규칙**(/tel 회전 종류·거리·fin)이 한다. 의도를 모델에 넣지 않으면 모호성이 사라진다.

---

## FINAL

### (1) 권고 아키텍처 — 가설 **검증됨(조건부)**
"지각 헤드(차로 기하) + 규칙 제어기"를 채택한다. 근거: 폐루프 성공 시스템 전부가 기하/짧은 궤적 → 규칙 제어기(Q1); 우리 진동은 비관측 양(먼 경로 의도)의 프레임 간 분산(Q2); 의도는 규칙층으로 뺄 수 있음(Q4). 반대 가설(앞점 BC + 스무딩/앙상블/교란)은 "보조"로만 남긴다 — 스무딩은 잡음을 지연으로 바꿀 뿐이다.
```
화면 → DriveNet 헤드 ─ e_y, e_psi, κ, lc10/20/40, lane_idx, n_lanes, conf
        ↓ 시간 앙상블(자차 이동 보정, exp 가중 3~5프레임)
Layer3 규칙: 목표 차로 = f(/tel 회전·aD·fin) → 목표 e_y* = (target_lane − lane_idx)·lane_w
제어기: Stanley  δ = (e_psi) + atan(k·(e_y−e_y*)/(v+ε)) + κ 피드포워드, 조향률 상한
Layer1 페일세이프 그대로(제동), 속도 모델 v9 그대로.
```

### (2) 라벨 규격 `L.npy` (모두 /tel 기하에서, 도로 절대좌표 기준)
| 열 | 이름 | 단위 | 정의 |
|---|---|---|---|
| 0 | e_y | m | 현재 차로 중심 대비 차 기준점 횡오차(+우) |
| 1 | e_psi | rad | 차로 접선 대비 헤딩 오차 |
| 2 | kappa0 | 1/m | 차 위치 차로 곡률(부호) |
| 3~5 | lc10, lc20, lc40 | m | 차 좌표계에서 10/20/40m 앞 **차로 중심**의 횡오프셋(경로선 아님) |
| 6 | lane_idx | 정수 | 진행방향 차로 인덱스(0=1차로) |
| 7 | n_lanes | 정수 | 진행방향 차로수 |
| 8 | lane_w | m | 차로 폭 |
| 9 | d_left, 10 d_right | m | 차도 좌·우 가장자리까지(기존 Y 5~6열 이전) |
| 11 | valid | 0/1 | g2/차로 정보 존재 |
`M.npy`(gap/ped/sig/turn/aD/fin…)는 규칙층·필터용으로만 유지, 모델 입력 금지. 기존 lp/lf 열은 폐기.

### (3) 수집 계획
- **전 지도 무작위 구간**: 스폰 위치를 지도 전체 way 에서 균등 샘플(간선·골목 비율 유지), 구간당 60~120초, 규칙 조향. pairs30 고정 구간 수집 중단.
- **자세 교란**(ChauffeurNet·PilotNet 준용, 차로 3.25m 기준): 횡 e_y ~ N(0, 0.6m) 절단 ±1.4m, 헤딩 ~ N(0, 10°) 절단 ±35°, 전체 프레임의 40%. 교란 직후 규칙이 복귀하는 2~3초도 그대로 기록(라벨은 기하라 오염 없음). 교란 표본 학습 가중 0.5.
- 규모: 15만 프레임(교란 6만 + 정상 9만), 좌우반전 증강 시 e_y·e_psi·κ·lc·lane_idx 부호/순서 반전.
- 홀드아웃: 지도 격자 중 20구간(청크 단위로 제외, 인접 청크 포함 금지)을 수집·학습에서 완전 배제.
- 3 시드 학습(CILRS 42% 편차 교훈) → 홀드아웃 오프라인 오차로 선택.

### (4) 검증 프로토콜 — 미학습 20구간 × 300초, 무단횡단 ×5, v9 속도, GPU 파이프라인
오프라인 관문(홀드아웃): e_y MAE ≤0.15m, e_psi ≤2°, lane_idx 정확도 ≥95%, lc20 MAE ≤0.4m.
폐루프 합격(모두 충족, 3구간 rule 기준선 대비):
- 회피가능 사고 0(20구간 합계), 차로이탈 0
- 복귀(순간이동·offRev) ≤ 1/구간, 합계 ≤ 규칙 주행 동일 조건의 1.5배
- 직선(aD>80) 반전 ≤ 6/min(규칙 1.9~3.4), 코너 조향률 p95 ≤ 규칙 ×2
- 횡 진폭 p95 ≤ 0.35m(규칙 0.07~0.30)
- 핸드오버 ≤ 2/min, T1 이양(회전 준비·차로 변경) 포함해서 측정 — T0 만으로는 판정 불가(ar_5581 S2)
- 완주 강남역→시청역 1회 도착.

### (5) 폐기
- lp40/80 및 전방거리(lf) 8점 라벨, 경로선 기반 lp 라벨 전부.
- `cond_vec` vdim8/9(모델 의도 입력) — 의도는 규칙층으로.
- 동일 3구간 반복 DAgger(mp4 계열), `LP_RATE/LP_TAU` 를 해법으로 삼는 것(안전용 조향률 상한만 유지).
- 프레임 스택·이전 조향 입력 도입 계획(copycat).
- pairs30 고정 구간 = 주 지표 사용 중단(회귀 케이스로만).

---

## 출처 검증 (2026-09-23 fetch)
- https://blog.comma.ai/end-to-end-lateral-planning/ — OK (2021)
- https://arxiv.org/abs/1708.06374 — OK (RSS 2017)
- https://www.mobileye.com/technology/responsibility-sensitive-safety/ — OK
- https://arxiv.org/abs/1912.12294 + https://ar5iv.labs.arxiv.org/html/1912.12294 — OK (LbC 2019)
- https://arxiv.org/abs/1710.02410 — OK (CIL 2018)
- https://arxiv.org/abs/1904.08980 + https://ar5iv.labs.arxiv.org/html/1904.08980 — OK (CILRS 2019)
- https://arxiv.org/abs/1812.03079 + https://ar5iv.labs.arxiv.org/html/1812.03079 — OK (ChauffeurNet 2018)
- https://arxiv.org/abs/1011.0686 — OK (DAgger 2011)
- https://arxiv.org/abs/1604.07316 + https://ar5iv.labs.arxiv.org/html/1604.07316 — OK (PilotNet 2016)
- https://arxiv.org/abs/2206.08129 + https://ar5iv.labs.arxiv.org/html/2206.08129 — OK (TCP 2022)
- https://arxiv.org/abs/2207.14024 — OK (InterFuser 2022)
- https://arxiv.org/abs/2205.15997 + https://ar5iv.labs.arxiv.org/html/2205.15997 — OK (TransFuser 2022)
- https://arxiv.org/abs/2203.11934 + https://ar5iv.labs.arxiv.org/html/2203.11934 — OK (LAV 2022)
- https://arxiv.org/abs/1905.11979 — OK (causal confusion 2019)
- https://arxiv.org/abs/2010.14876 — OK (copycat 2020)
- https://arxiv.org/abs/2304.13705 + https://arxiv.org/html/2304.13705 — OK (ACT 2023)
- https://publications.ri.cmu.edu/storage/publications/pub_files/pub3/coulter_r_craig_1992_1/coulter_r_craig_1992_1.pdf — OK (PDF 로컬 판독, 1992; 원 ri.cmu.edu 경로는 301 리다이렉트)
- 실패: https://github.com/commaai/openpilot/blob/master/selfdrive/modeld/README.md, …/models/README.md, raw.githubusercontent 동일 경로 — 404(README 이동/삭제). openpilot 근거는 blog 로 대체. arxiv.org/pdf 직접 fetch 는 바이너리라 판독 불가 → ar5iv/html 로 대체.
