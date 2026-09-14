# 최고 성능 모델 기록 (seoul-drive)

> 이 파일은 "지금 제일 좋은 게 뭐였지"를 다시 찾지 않기 위한 단일 기준점이다.
> 새 모델이 아래 수치를 **검증셋 기준으로** 넘을 때만 이 파일을 갱신한다.

## ★ 현재 최고: `bc_final.pt`  (2026-09-14)

| 항목 | 값 |
|---|---|
| 파일 | `games/seoul-drive/bc_final.pt` |
| MD5 | `25afcb5becaf2a34b84b364f654850ca` |
| 파라미터 | 203,139 |
| 학습 프레임 | 85,768 (heavy 2회분 병합) |
| **개선율(평균예측 대비)** | **96.2 % → LEARNED** |
| val MSE | 0.00224 (baseline 0.05892) |

### 조작별 성능 (held-out 4,000 프레임)
| 조작 | 개선율 | 상관계수 |
|---|---|---|
| steer | 97.8 % | 0.991 |
| thr   | 98.6 % | 0.993 |
| **brake** | **95.3 %** | **0.978** |

### ★긴급제동 — 이전 버전의 최대 약점이 해결됐다
급제동 상황(brake>0.7) 417프레임에서:
| 모델 | 실제 | 예측 | 급제동 판정률 |
|---|---|---|---|
| `bc_hv.pt`(이전) | 0.98 | 0.35 | 0 % |
| **`bc_final.pt`** | 0.98 | **0.94** | **100 %** |

해결 방법 두 가지를 같이 썼다(u_4980 오너 지시 "A B 둘 다"):
- (a) 급제동이 실제로 일어나는 상황을 만들었다 — 무단횡단 돌발(u_4981) + 내 차로 앞차 스폰.
  급제동 표본 77개 → 417개(5.4배).
- (b) 학습 시 급제동 프레임을 20배, 감속을 6배 자주 뽑았다(오버샘플링).
  검증셋에는 가중치를 걸지 않아 점수는 정직하다.

### 이 모델을 만든 조건 (재현용)
```bash
python3 games/seoul-drive/build.py --traffic heavy --speed 50
# 아티팩트 배포 → Chrome 리로드(16초). 창 901x662 (전체화면 금지)
python3 games/seoul-drive/collect_screen.py games/seoul-drive/data/t_hv  420
python3 games/seoul-drive/collect_screen.py games/seoul-drive/data/t_hv2 420
python3 games/seoul-drive/merge_sets.py games/seoul-drive/data/final \
        games/seoul-drive/data/t_hv games/seoul-drive/data/t_hv2 --stride 1
python3 games/seoul-drive/bc_train2.py games/seoul-drive/data/final \
        games/seoul-drive/bc_final.pt 16
```

### 이 버전에 들어간 핵심 수정 (이게 없으면 재현 안 됨)
1. `decode.py` — capture 의 **BGR 를 RGB 로 뒤집어** 읽는다. 빠지면 라벨 전 프레임 미검출.
2. `teacher.js` — **적신호 정지**. 없으면 '빨간불에 선다'가 0프레임.
3. `game.js` — **내 차로·앞쪽 우선 스폰**. 없으면 heavy 72대여도 앞차를 못 만나 제동 0%.
4. `game.js` — **무단횡단 돌발**. 급제동 표본을 만드는 핵심.
5. `teacher.js` — **목표속도 추종**. 없으면 늘 최고속이라 속도 개념이 안 생긴다.
6. `bc_train2.py` — **급제동 오버샘플링**. 없으면 브레이크를 덜 밟는다(0.35).
7. 창 901x662 + decode 좌상단 열만 스캔 → **102fps** (전체화면이면 27.9fps).

### 남은 약점
- 사고 4프레임(85,768 중) — 무단횡단 돌발을 넣은 뒤에도 완전 회피는 아니다.
- 신호등: 교사는 지키지만, 모델이 '신호를 봐서' 서는지 '앞차를 봐서' 서는지는 미분리.

## 이전 버전 (참고)
| 모델 | 프레임 | 개선율 | 비고 |
|---|---|---|---|
| `bc_hv.pt` | 42,716 | 97.2 % | heavy+신호, 급제동 예측 0.35 로 약함 |
| `bc_mix.pt` | 36,688 | 93.6 % | light/medium/heavy 혼합, 신호 미적용 |
| `bc_v5.pt` | 11,718 | 72.5 % | 단일 밀도, 신호 미적용 |
| `bc_v4.pt` | — | 99.7 %* | *도로밖 51% 데이터로 학습 — 수치는 높지만 무효 |
| 최초 BC | 351 | 0.2 % | COLLAPSED (상수 출력) |
