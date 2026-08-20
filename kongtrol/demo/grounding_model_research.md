# UI Grounding 모델 추천 (유저 다른-PC vLLM 설치용) — a_24 / a_47

> 목적: 유저 LAN GPU 서버(192.168.45.183:8000, NVIDIA vLLM)에 설치할 [UI grounding 특화 모델].
> 현 Qwen3-VL-8B-AWQ = 속도 0.3s 좋으나 ★좌표 부정확(일반 VL). → UI grounding 특화 필요.
> ★a_47: Holo still recommended; adapter now Holo-ready (`ground_vl.sh` auto-detects Holo* → 0-1000→LOGICAL). GPU install still user-other-PC.
> 리서치: WebSearch 2025~2026, ScreenSpot 벤치·vLLM·출처 기반.

## 1. 비교표 (ScreenSpot 벤치 · vLLM · 크기 · 라이선스)

| 모델 | ScreenSpot-V2 | ScreenSpot-Pro | 기반 | vLLM | 크기/VRAM | 라이선스 |
|---|---|---|---|---|---|---|
| **Holo1.5-7B** (Hcompany) | SOTA급 | **57.94** (최고) | Qwen2.5-VL-7B | ✅ | 7B·~16-20GB(bf16)·AWQ↓ | **Apache-2.0** |
| UI-TARS-1.5-7B (ByteDance) | **91.6** | text67.3/icon64.5 (재현~40) | 자체 VLM | ✅ 0.6.6+ | 7B·L40S 48G 권장 | Apache-2.0 |
| UGround-V1-7B (OSU-NLP) | 높음 | 31.1 | Qwen2-VL-7B | ✅ A100 80G | 7B | 오픈 |
| OS-Atlas-7B | 87.1 | 18.9 | Qwen2-VL | ✅ | 7B | 오픈 |
| Holo1.5-3B | 높음 | 준SOTA | Qwen2.5-VL-3B | ✅ | 3B·VRAM↓ | Apache-2.0 |
| Qwen3-VL-8B (현재) | — | ~29(일반VL) | — | ✅ | 8B AWQ | — |

- 출처: Holo1.5(marktechpost·HF Hcompany/Holo1.5-7B)·UI-TARS(arXiv 2501.12326·HF ByteDance-Seed)·UGround(x.com ScreenSpot-Pro 리더보드 31.1 SOTA·HF osunlp)·ScreenSpot-Pro(arXiv 2504.07981).

## 2. ★추천 (설치용)

### 추천 1 (최선): Holo1.5-7B (Hcompany/Holo1.5-7B)
- **이유**: ScreenSpot-Pro **57.94** = 현 SOTA(UGround 31.1·UI-TARS 재현40·Qwen2.5-VL 29 대비 압도). UI localization 특화(좌표 정확·일관). **Qwen2.5-VL-7B 기반 → vLLM 완전 호환**(현 서버 그대로). **Apache-2.0**(상용 가능). 3B 버전도 있어 VRAM 부족시 대체.
- **유저 액션**: "Hcompany/Holo1.5-7B 설치하세요." 현 Qwen3-VL-8B 교체 or 병행(grounding 전용).

### 추천 2 (대안): UI-TARS-1.5-7B (ByteDance-Seed/UI-TARS-1.5-7B)
- **이유**: ScreenSpot-V2 **91.6** SOTA·검증된 GUI 에이전트. vLLM 0.6.6+ 공식 지원. 단 ScreenSpot-Pro(고해상도) 재현 이슈(~40). 좌표+행동 통합 모델.

## 3. ★설치·서빙 명령 (그 PC에서 실행 · NVIDIA vLLM)

### Holo1.5-7B (추천1)
```bash
# HF 다운로드는 vllm 이 자동. AWQ 없으면 bf16(VRAM ~16-20GB) 또는 --quantization 옵션.
vllm serve Hcompany/Holo1.5-7B \
  --host 0.0.0.0 --port 8000 \
  --limit-mm-per-prompt '{"image":2,"video":0}' \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.90 \
  -tp 1
# VRAM 부족시: Hcompany/Holo1.5-3B 로 교체.
```

### UI-TARS-1.5-7B (추천2)
```bash
vllm serve ByteDance-Seed/UI-TARS-1.5-7B \
  --host 0.0.0.0 --port 8000 \
  --limit-mm-per-prompt '{"image":2,"video":0}' \
  --max-model-len 16384 -tp 1
```

## 4. kongtrol 연결법
- 두 모델 모두 vLLM = **OpenAI /v1 호환** → kongtrol ground_vl.sh 엔드포인트만 교체:
  - 현재: REMOTE-ONLY `http://192.168.45.183:8000/v1/chat/completions`(로컬 MLX 데몬 폐기·삭제됨, a_23 u_66/67).
  - 모델 교체 시 URL 동일, `VL_REMOTE_MODEL` 만 변경(ground_vl.sh env).
- 좌표 프롬프트: "Output ONLY {\"x\":int,\"y\":int}, 0-1000 normalized, center of <element>." (Holo1.5는 좌표 특화라 정확).
- ★좌표계: Holo* = 0-1000 normalized → shot px → LOGICAL (ground_vl.sh a_47). Qwen = resize-px → orig-px → LOGICAL + 3-sample median (`VL_CONSENSUS=1`).

## 5. 유저 설치 액션 (명확)
1. 그 PC(192.168.45.183)에서 위 `vllm serve Hcompany/Holo1.5-7B ...` 실행(현 Qwen3-VL 대체 or 다른 포트).
2. 기동 후 kongtrol ground_vl.sh 를 그 서버 URL 로 교체(OpenAI /v1).
3. Keynote 등에서 캔버스·도형·이미지 좌표 = Holo1.5 grounding(정확) + a11y(버튼·텍스트 <100ms) 하이브리드.

## 출처
- Holo1.5: marktechpost.com/2025/09/18 · HF Hcompany/Holo1.5-7B(Apache-2.0) · hcompany.ai/holo2
- UI-TARS-1.5-7B: arXiv 2501.12326 · HF ByteDance-Seed/UI-TARS-1.5-7B · github bytedance/UI-TARS README_deploy
- UGround-V1-7B: HF osunlp/UGround-V1-7B · ScreenSpot-Pro 리더보드(31.1 SOTA, x.com/ChiYeung_Law)
- ScreenSpot-Pro: arXiv 2504.07981 · vLLM Qwen2.5-VL recipes(recipes.vllm.ai)
