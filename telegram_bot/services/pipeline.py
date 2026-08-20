"""파이프라인 오케스트레이터 - Playwright UI 조작 방식

localhost:4000 UI를 Playwright로 조작하여 영상 생성 파이프라인을 실행한다.

실제 UI 버튼/필드 (2026-03-31 확인):
  탭: "③ 시나리오"
  주제 입력: placeholder "예: 2026년 AI 트렌드 총정리"
  스타일: button "Shorts" (텍스트에 Shorts 포함)
  참고 스크립트: placeholder "트렌드 영상에서 추출한 스크립트를 붙여넣으면"
  시나리오 생성: button "시나리오 생성"
  TTS: button "전체 TTS 생성"
  영상: button "전체 영상 생성"
  출력: button "전체 영상 출력"
  저장: button "저장"
  프로젝트 제목: placeholder "프로젝트 제목을 입력하세요"
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_UI_BASE_URL = "http://localhost:4000"
_SCREENSHOT_DIR = Path("tests/screenshots/pipeline")
_MAX_RETRIES = 3

# 타임아웃 (밀리초)
_NAV_TIMEOUT = 30_000
_ACTION_TIMEOUT = 10_000
_SCENARIO_TIMEOUT = 120_000   # 시나리오 생성 2분
_TTS_TIMEOUT = 300_000        # TTS 5분
_VIDEO_TIMEOUT = 1_200_000    # 영상 20분
_SAVE_TIMEOUT = 30_000

# 브라우저 싱글턴
_browser_instance = None
_page_instance = None


async def _get_page():
    """매 파이프라인 실행마다 새 컨텍스트로 깨끗한 페이지 반환."""
    global _browser_instance, _page_instance
    from playwright.async_api import async_playwright

    # 브라우저만 재사용, 컨텍스트는 매번 새로 (이전 세션 상태 격리)
    if _browser_instance is None:
        pw = await async_playwright().start()
        _browser_instance = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )

    # 이전 페이지가 있으면 컨텍스트 닫기
    if _page_instance is not None:
        try:
            ctx = _page_instance.context
            await ctx.close()
        except Exception:
            pass
        _page_instance = None

    ctx = await _browser_instance.new_context(viewport={"width": 1440, "height": 900})
    _page_instance = await ctx.new_page()
    return _page_instance


async def _close_browser():
    global _browser_instance, _page_instance
    if _browser_instance:
        await _browser_instance.close()
    _browser_instance = None
    _page_instance = None


async def _send_telegram(job, text: str):
    """텔레그램으로 텍스트 메시지 전송."""
    if not job or not job.chat_id:
        return
    try:
        from telegram_bot.bot import get_app
        app = get_app()
        if app:
            await app.bot.send_message(chat_id=job.chat_id, text=text)
    except Exception:
        pass


async def _screenshot(page, name: str, job=None):
    """현재 뷰포트만 스크린샷 저장 + 텔레그램으로 전송."""
    try:
        _SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = _SCREENSHOT_DIR / f"{name}.png"
        # full_page=False → 현재 보이는 뷰포트만 캡처 (dimensions 에러 방지)
        await page.screenshot(path=str(path), full_page=False)

        # 텔레그램으로 스크린샷 전송
        if job and job.chat_id:
            try:
                from telegram_bot.bot import get_app
                app = get_app()
                if app:
                    with open(str(path), "rb") as photo:
                        await app.bot.send_photo(
                            chat_id=job.chat_id,
                            photo=photo,
                            caption=f"📸 {name}",
                        )
            except Exception as exc:
                logger.warning(f"[pipeline] 스크린샷 텔레그램 전송 실패: {exc}")
    except Exception:
        pass


def _update_db_sync(news_project_id: str, **kwargs):
    from database.repository import update_news_project
    kwargs.setdefault("updated_at", datetime.now(tz=timezone.utc).isoformat())
    update_news_project(news_project_id, **kwargs)


async def run_pipeline(
    job,
    news_project_id: str,
    script_content: str,
    scenario_data: dict,
    anchor_name: str,
    character_data: dict,
) -> dict:
    """Playwright로 UI를 조작하여 영상 생성 파이프라인 실행.

    흐름:
      1. localhost:4000 접속
      2. 시나리오 탭 → 주제/대본 입력 → Shorts 선택 → 캐릭터 선택
      3. 시나리오 생성 → 완료 대기
      4. 전체 TTS 생성 → 완료 대기
      5. 전체 영상 생성 → 완료 대기 (진행률 추적)
      6. 프로젝트 저장
      7. 결과 파일 확인
    """
    news_title = scenario_data.get("title", "뉴스")
    title = f"{anchor_name}_{news_title}"
    scenes = scenario_data.get("scenes", [])

    page = None
    try:
        # ─── Step 1: 브라우저 접속 ──────────────────
        job.progress = "브라우저 접속 중..."
        job.progress_pct = 5
        logger.info("[pipeline] Step 1: 브라우저 접속")

        page = await _get_page()
        await page.goto(_UI_BASE_URL, wait_until="networkidle", timeout=_NAV_TIMEOUT)

        # 이전 프로젝트 초기화 — "새 프로젝트" 클릭
        try:
            new_proj_btn = page.get_by_role("button", name="새 프로젝트")
            if await new_proj_btn.is_visible(timeout=3000):
                await new_proj_btn.click()
                await page.wait_for_timeout(2000)
                logger.info("[pipeline] 새 프로젝트 초기화 완료")
        except Exception:
            pass

        await _screenshot(page, "step1_home", job)

        # ─── Step 2: 프로젝트 제목 설정 ─────────────
        job.progress = "프로젝트 설정 중..."
        job.progress_pct = 8

        # 프로젝트 제목 입력
        proj_title = page.get_by_placeholder("프로젝트 제목을 입력하세요")
        if await proj_title.is_visible():
            await proj_title.fill(title[:50])

        # ─── Step 3: 시나리오 탭 → 입력 → 생성 ──────
        job.progress = "시나리오 탭 설정 중..."
        job.progress_pct = 10
        logger.info("[pipeline] Step 3: 시나리오 탭")

        # 탭 클릭
        tab = page.get_by_role("tab", name="③ 시나리오")
        await tab.click()
        await page.wait_for_timeout(2000)

        # 주제 입력
        topic = page.get_by_placeholder("예: 2026년 AI 트렌드 총정리")
        if await topic.is_visible():
            await topic.fill(title[:100])
            logger.info(f"[pipeline] 주제 입력: {title[:50]}")

        # Shorts 선택
        shorts_btn = page.locator("button:has-text('Shorts')")
        if await shorts_btn.count() > 0:
            await shorts_btn.first.click()
            logger.info("[pipeline] Shorts 스타일 선택")

        # 목표 영상 길이 20초 선택
        try:
            duration_select = page.locator("text=목표 영상 길이").locator("..").locator("select, [role='combobox']")
            if await duration_select.count() > 0:
                await duration_select.first.click()
                await page.wait_for_timeout(500)
                option_20 = page.locator("[data-value='20'], li:has-text('20초')")
                if await option_20.count() > 0:
                    await option_20.first.click()
                    logger.info("[pipeline] 목표 영상 길이 20초 선택")
                    await page.wait_for_timeout(500)
        except Exception as exc:
            logger.warning(f"[pipeline] 목표 시간 선택 실패 (무시): {exc}")

        # 참고 스크립트 입력
        ref_script = page.get_by_placeholder("트렌드 영상에서 추출한 스크립트를 붙여넣으면")
        if await ref_script.is_visible():
            await ref_script.fill(script_content[:3000])
            logger.info("[pipeline] 참고 스크립트 입력")

        # 캐릭터 선택 — 이름 텍스트의 부모 DIV 클릭
        try:
            # 캐릭터 영역으로 스크롤
            char_label = page.get_by_text("캐릭터 선택")
            if await char_label.is_visible():
                await char_label.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)

            # 캐릭터 이름 텍스트 찾기 → 부모(카드) 클릭
            name_el = page.locator(f"text='{anchor_name}'")
            clicked = False
            for i in range(await name_el.count()):
                el = name_el.nth(i)
                if await el.is_visible():
                    parent = el.locator("..")
                    await parent.click()
                    await page.wait_for_timeout(500)
                    logger.info(f"[pipeline] 캐릭터 선택 완료: {anchor_name}")
                    clicked = True
                    break

            if not clicked:
                logger.warning(f"[pipeline] 캐릭터 '{anchor_name}' 텍스트를 찾지 못함")
        except Exception as exc:
            logger.warning(f"[pipeline] 캐릭터 선택 에러: {exc}")

        await _screenshot(page, "step3_form_filled", job)

        # ─── Step 3.5: 중간 저장 (대본+캐릭터 입력 후) ──
        job.progress = "중간 저장 중..."
        try:
            save_btn = page.get_by_role("button", name="저장").first
            if await save_btn.is_visible() and await save_btn.is_enabled():
                await save_btn.click()
                await page.wait_for_timeout(2000)
                logger.info("[pipeline] Step 3.5: 중간 저장 완료 (대본+캐릭터)")
        except Exception as exc:
            logger.warning(f"[pipeline] 중간 저장 실패 (무시): {exc}")

        # 시나리오 생성 버튼 — 참고 스크립트가 있으면 라이트 시나리오 우선
        job.progress = "시나리오 생성 중..."
        job.progress_pct = 15

        light_btn = page.locator("button:has-text('라이트 시나리오')")
        gen_btn = page.get_by_role("button", name="시나리오 생성")

        # 라이트 시나리오 버튼이 보이면 우선 사용 (대본 유지 모드)
        if await light_btn.count() > 0 and await light_btn.first.is_visible():
            await light_btn.first.click()
            logger.info("[pipeline] 라이트 시나리오 클릭 (대본 유지)")
        elif await gen_btn.is_enabled():
            await gen_btn.click()
            logger.info("[pipeline] 시나리오 생성 클릭")

            # 씬이 나타날 때까지 대기
            for i in range(24):  # 최대 2분
                scene_text = page.locator("text=/씬 \\d+/")
                if await scene_text.count() > 0:
                    logger.info(f"[pipeline] 씬 생성 완료 ({(i+1)*5}초)")
                    break
                await page.wait_for_timeout(5000)
                job.progress = f"시나리오 생성 중... ({(i+1)*5}초)"
        else:
            logger.warning("[pipeline] 시나리오 생성 버튼 비활성 — 건너뜀")

        await _screenshot(page, "step3_scenario_done", job)
        job.progress_pct = 25

        # ─── Step 4: 스토리보드 생성 완료 대기 ─────────
        job.progress = "스토리보드 생성 대기 중..."
        job.progress_pct = 30
        logger.info("[pipeline] Step 4: 스토리보드 생성 완료 대기")

        # "스토리보드 생성 중..." 텍스트가 사라질 때까지 대기
        for i in range(60):  # 최대 5분
            storyboard_loading = page.locator("text=/스토리보드 생성 중/")
            if await storyboard_loading.count() == 0:
                logger.info(f"[pipeline] 스토리보드 생성 완료 ({(i+1)*5}초)")
                break
            await page.wait_for_timeout(5000)
            job.progress = f"스토리보드 생성 대기 중... ({(i+1)*5}초)"
            job.progress_pct = 30 + min(15, i)

        await _screenshot(page, "step4_storyboard_done", job)
        job.progress_pct = 50
        logger.info("[pipeline] Step 4: 스토리보드 완료")

        # ─── Step 5: 전체 영상 생성 (UI가 순차 처리) ───
        job.progress = "전체 영상 생성 시작..."
        job.progress_pct = 50
        logger.info("[pipeline] Step 5: 전체 영상 생성")
        await _send_telegram(job, "🎬 전체 영상 생성을 시작합니다...")

        # "전체 영상 생성" 버튼 클릭
        all_video_btn = page.get_by_role("button", name="전체 영상 생성")
        try:
            await all_video_btn.scroll_into_view_if_needed()
            await all_video_btn.wait_for(state="visible", timeout=_ACTION_TIMEOUT)
            await all_video_btn.click()
            logger.info("[pipeline] 전체 영상 생성 클릭")

            # 클릭 후 5초 대기 (UI 상태 변경 시간)
            await page.wait_for_timeout(5000)

            # 영상 생성 완료 대기 (씬당 약 1~2분, 최대 10분)
            for i in range(60):  # 최대 10분 (10초 간격)
                await page.wait_for_timeout(10000)

                # 진행률 파싱
                try:
                    progress_el = page.locator("text=/영상 생성 중/")
                    if await progress_el.count() > 0:
                        text = await progress_el.first.inner_text()
                        m = re.search(r"\((\d+)/(\d+)\)", text)
                        if m:
                            cur, total = int(m.group(1)), int(m.group(2))
                            pct = 50 + int((cur / max(total, 1)) * 35)
                            job.progress_pct = pct
                            job.progress = f"영상 생성 중... ({cur}/{total})"
                            logger.info(f"[pipeline] 영상 진행: {cur}/{total}")
                            # N/N 도달 시 완료로 판정
                            if cur >= total:
                                logger.info(f"[pipeline] 전체 영상 생성 완료 ({cur}/{total}, {(i+1)*10}초)")
                                break
                            continue
                except Exception:
                    pass

                # 완료 감지: "영상 생성 중" 텍스트가 사라짐 or 버튼 재활성화
                try:
                    progress_gone = page.locator("text=/영상 생성 중/")
                    if await progress_gone.count() == 0:
                        logger.info(f"[pipeline] 전체 영상 생성 완료 (진행 텍스트 소멸, {(i+1)*10}초)")
                        break
                    if await all_video_btn.is_visible(timeout=2000):
                        btn_text = await all_video_btn.inner_text()
                        if "전체 영상 생성" in btn_text and await all_video_btn.is_enabled():
                            logger.info(f"[pipeline] 전체 영상 생성 완료 ({(i+1)*10}초)")
                            break
                except Exception:
                    pass

                job.progress = f"영상 생성 중... ({(i+1)*10}초)"

        except Exception as exc:
            logger.warning(f"[pipeline] 전체 영상 생성 실패: {exc}")
            await _screenshot(page, f"error_video_{datetime.now().strftime('%H%M%S')}")

        await _screenshot(page, "step5_video_done", job)
        job.progress_pct = 85

        # ─── Step 6: 프로젝트 저장 ──────────────────
        job.progress = "프로젝트 저장 중..."
        job.progress_pct = 90
        logger.info("[pipeline] Step 6: 저장")

        save_btn = page.get_by_role("button", name="저장").first
        try:
            if await save_btn.is_visible() and await save_btn.is_enabled():
                await save_btn.click()
                await page.wait_for_timeout(5000)  # 저장 API 완료 대기 (3→5초)
                logger.info("[pipeline] 프로젝트 저장 완료")
        except Exception as exc:
            logger.warning(f"[pipeline] 저장 실패: {exc}")

        await _screenshot(page, "step6_saved", job)

        # ─── Step 7: 결과 확인 ──────────────────────
        job.progress = "결과 확인 중..."
        job.progress_pct = 95
        logger.info("[pipeline] Step 7: 결과 확인")

        # projects/ 에서 최신 프로젝트의 final 영상 찾기
        projects_dir = Path(__file__).resolve().parent.parent.parent / "projects"
        video_path = ""
        thumbnail_path = ""
        file_size = 0
        duration = 0.0

        if projects_dir.exists():
            # 최신 프로젝트 디렉토리 찾기
            dirs = sorted(projects_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
            for d in dirs[:3]:
                finals = list(d.glob("final*.mp4"))
                if finals:
                    video_path = str(finals[0])
                    file_size = finals[0].stat().st_size
                    logger.info(f"[pipeline] 최종 영상: {video_path} ({file_size} bytes)")
                    break

                # final이 없으면 scene mp4 확인
                scene_mp4s = list(d.glob("scene_*.mp4"))
                if scene_mp4s:
                    video_path = str(scene_mp4s[0])
                    file_size = scene_mp4s[0].stat().st_size
                    logger.info(f"[pipeline] 씬 영상: {video_path} ({file_size} bytes)")
                    break

        # DB 업데이트
        try:
            await asyncio.to_thread(
                _update_db_sync,
                news_project_id,
                status="complete",
                final_video_path=video_path,
                thumbnail_path=thumbnail_path,
                title=title,
            )
        except Exception as exc:
            logger.error(f"[pipeline] DB 업데이트 실패: {exc}")

        # ─── Step 8: project.json 보강 저장 ──────────
        # UI 저장은 폼 상태가 빈값일 수 있으므로, 파이프라인 데이터를 직접 보강
        try:
            if video_path:
                proj_dir = Path(video_path).parent
            elif projects_dir.exists():
                dirs = sorted(projects_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
                proj_dir = dirs[0] if dirs else None
            else:
                proj_dir = None

            if proj_dir and (proj_dir / "project.json").exists():
                import json as _json
                proj_file = proj_dir / "project.json"
                with open(proj_file) as f:
                    proj = _json.load(f)

                # scenario 섹션 보강
                sc = proj.get("scenario", {})
                if not sc.get("topic"):
                    sc["topic"] = news_title
                if not sc.get("sourceScript"):
                    sc["sourceScript"] = script_content
                if sc.get("targetDuration", 300) > 60:
                    sc["targetDuration"] = 20
                if not sc.get("result") or sc.get("result") is None:
                    sc["result"] = scenario_data
                proj["scenario"] = sc

                # page 섹션 보강
                pg = proj.get("page", {})
                if not pg.get("scriptForScenario"):
                    pg["scriptForScenario"] = script_content
                pg["videoMode"] = "shorts"
                proj["page"] = pg

                # media 섹션 보강 — 실제 scene_*.mp4 파일 스캔으로 videoFiles 강제 동기화
                # 프론트 저장이 비동기로 일부만 기록할 수 있으므로, 디스크 파일 기준으로 덮어씀
                media = proj.get("media", {})
                video_files = {}  # 빈 딕셔너리로 시작 (디스크 파일 기준 재구축)
                import re as _re_scan
                for mp4 in sorted(proj_dir.glob("scene_*.mp4")):
                    m = _re_scan.search(r"scene_(\d+)\.mp4", mp4.name)
                    if m:
                        scene_num = str(int(m.group(1)))
                        video_files[scene_num] = mp4.name
                if video_files:
                    logger.info(f"[pipeline] videoFiles 동기화: {video_files}")
                media["videoFiles"] = video_files
                proj["media"] = media

                with open(proj_file, "w") as f:
                    _json.dump(proj, f, ensure_ascii=False, indent=2)
                logger.info(f"[pipeline] project.json 보강 저장 완료: {proj_file}")
        except Exception as exc:
            logger.warning(f"[pipeline] project.json 보강 실패: {exc}")

        job.progress = "완료"
        job.progress_pct = 100

        result = {
            "success": True,
            "video_path": video_path,
            "thumbnail_path": thumbnail_path,
            "title": title,
            "description": "",
            "tags": [],
            "duration": duration,
            "file_size": file_size,
        }
        logger.info(f"[pipeline] 파이프라인 완료: {result}")
        return result

    except Exception as exc:
        logger.exception(f"[pipeline] 파이프라인 에러: {exc}")
        if page:
            await _screenshot(page, f"error_{datetime.now().strftime('%H%M%S')}")

        try:
            await asyncio.to_thread(
                _update_db_sync,
                news_project_id,
                status="failed",
                error_message=str(exc)[:200],
            )
        except Exception:
            pass

        job.error = str(exc)
        return {"success": False, "error": str(exc)}
