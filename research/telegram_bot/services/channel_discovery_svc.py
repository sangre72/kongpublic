"""채널 발견 서비스: claude -p 기반 채널 탐색 + RSS 검증."""

import json
import logging
import os
import re
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class ChannelDiscoveryService:
    """claude -p 기반 채널 발견 + 실패 채널 대안 탐색."""

    # Claude CLI 타임아웃 (초)
    CLAUDE_TIMEOUT = 60

    def discover_for_domain(
        self,
        domain_name: str,
        display_name: str,
        core_keywords: list[str],
        existing_channels: list[str],
    ) -> list[dict]:
        """claude -p로 도메인에 적합한 채널 탐색.

        Args:
            domain_name: 도메인 키 (예: 'ai', 'blockchain').
            display_name: 도메인 표시 이름 (예: 'AI/인공지능').
            core_keywords: 핵심 키워드 목록.
            existing_channels: 이미 등록된 채널 URL 목록 (중복 방지).

        Returns:
            [{"name": str, "channel_type": str, "method_config": dict,
              "source_url": str, "interval_seconds": int, "priority": int}, ...]
        """
        keywords_str = ", ".join(core_keywords) if core_keywords else domain_name
        existing_str = "\n".join(f"- {url}" for url in existing_channels) if existing_channels else "없음"

        prompt = f"""다음 리서치 도메인에 적합한 뉴스/정보 채널을 추천해주세요.

도메인: {display_name} ({domain_name})
핵심 키워드: {keywords_str}

이미 등록된 채널 (중복 제외):
{existing_str}

요구사항:
- RSS 피드가 있는 뉴스 사이트, 블로그, 공식 채널 우선
- 채널당 method_config는 JSON 객체로 제공
- RSS 방식: {{"url": "피드URL"}}
- 최대 10개 채널 추천
- 각 채널은 최근 30일 이내 업데이트 된 곳만

반드시 아래 JSON 배열 형식으로만 응답 (다른 텍스트 없이):
[
  {{
    "name": "채널 이름",
    "channel_type": "rss",
    "method_config": {{"url": "https://..."}},
    "source_url": "https://...",
    "interval_seconds": 900,
    "priority": 5
  }}
]"""

        output = self._call_claude(prompt)
        if not output:
            return []

        channels = self._parse_channel_list(output)
        # 기존 채널 URL과 중복 제거
        existing_set = set(existing_channels)
        return [ch for ch in channels if ch.get("source_url", "") not in existing_set]

    def recover_failed_channel(self, channel: dict) -> Optional[dict]:
        """실패한 채널의 대안 method_config를 claude -p로 탐색.

        Args:
            channel: research_channels 테이블 row dict.
                     필수 키: name, source_url, channel_type, last_error, consecutive_failures.

        Returns:
            대안 method_config dict 또는 None.
        """
        name = channel.get("name", "")
        source_url = channel.get("source_url", "")
        last_error = channel.get("last_error", "")
        failures = channel.get("consecutive_failures", 0)

        prompt = f"""다음 채널의 수집이 반복 실패하고 있습니다. 대안 수집 방법을 찾아주세요.

채널 이름: {name}
소스 URL: {source_url}
마지막 오류: {last_error}
연속 실패 횟수: {failures}

대안 방법 탐색:
1. 다른 RSS 피드 URL 시도 (url/feed, /rss, /atom.xml, /feed.xml 등)
2. 공식 API 엔드포인트 확인
3. 미러 사이트나 대체 채널 URL

반드시 아래 JSON 형식으로만 응답 (다른 텍스트 없이):
{{
  "channel_type": "rss",
  "method_config": {{"url": "https://..."}}
}}

대안을 찾을 수 없으면: null"""

        output = self._call_claude(prompt)
        if not output:
            return None

        return self._parse_method_config(output)

    def validate_rss_url(self, url: str) -> bool:
        """RSS URL 유효성 검증 (feedparser로 파싱 시도).

        Args:
            url: RSS 피드 URL.

        Returns:
            파싱 성공 여부.
        """
        try:
            import feedparser
            feed = feedparser.parse(url)
            # bozo=True는 파싱 오류, entries가 없으면 유효하지 않은 피드
            if feed.bozo and not feed.entries:
                return False
            return len(feed.entries) > 0
        except Exception as e:
            logger.warning(f"RSS 검증 실패 ({url}): {e}")
            return False

    def probe_rss_variants(self, base_url: str) -> Optional[str]:
        """일반적인 RSS URL 패턴으로 유효한 피드 탐색.

        Args:
            base_url: 사이트 기본 URL.

        Returns:
            유효한 RSS URL 또는 None.
        """
        # 이미 피드 URL이면 바로 검증
        if self.validate_rss_url(base_url):
            return base_url

        # 슬래시 정규화
        base = base_url.rstrip("/")
        candidates = [
            f"{base}/feed",
            f"{base}/feed/",
            f"{base}/rss",
            f"{base}/rss.xml",
            f"{base}/feed.xml",
            f"{base}/atom.xml",
            f"{base}/index.xml",
            f"{base}/?feed=rss2",
        ]

        for url in candidates:
            try:
                if self.validate_rss_url(url):
                    logger.info(f"RSS 피드 발견: {url}")
                    return url
            except Exception:
                continue

        return None

    def _call_claude(self, prompt: str) -> Optional[str]:
        """claude -p 호출 래퍼.

        Args:
            prompt: Claude에 전달할 프롬프트.

        Returns:
            Claude 응답 문자열 또는 None (실패 시).
        """
        try:
            env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=self.CLAUDE_TIMEOUT,
                env=env,
            )
            if result.returncode != 0:
                logger.warning(f"Claude CLI 오류: {result.stderr[:200]}")
                return None
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Claude CLI 타임아웃 ({self.CLAUDE_TIMEOUT}초)")
            return None
        except FileNotFoundError:
            logger.error("Claude CLI 미설치")
            return None
        except Exception as e:
            logger.error(f"Claude CLI 호출 실패: {e}")
            return None

    def _parse_channel_list(self, claude_output: str) -> list[dict]:
        """claude 응답에서 채널 목록 JSON 파싱.

        Args:
            claude_output: Claude CLI 응답 문자열.

        Returns:
            채널 dict 목록 (파싱 실패 시 빈 리스트).
        """
        try:
            json_str = self._extract_json_string(claude_output)
            if not json_str:
                return []

            data = json.loads(json_str)
            if not isinstance(data, list):
                logger.warning("채널 목록 파싱: 배열이 아닌 응답")
                return []

            channels = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                # 필수 필드 검증
                if not item.get("name") or not item.get("channel_type") or not item.get("method_config"):
                    continue
                channels.append({
                    "name": str(item["name"]),
                    "channel_type": str(item["channel_type"]),
                    "method_config": item["method_config"] if isinstance(item["method_config"], dict) else {},
                    "source_url": str(item.get("source_url", "")),
                    "interval_seconds": int(item.get("interval_seconds", 900)),
                    "priority": int(item.get("priority", 5)),
                })
            return channels

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"채널 목록 JSON 파싱 실패: {e}, 응답: {claude_output[:200]}")
            return []

    def _parse_method_config(self, claude_output: str) -> Optional[dict]:
        """claude 응답에서 method_config JSON 파싱.

        Args:
            claude_output: Claude CLI 응답 문자열.

        Returns:
            method_config dict 또는 None.
        """
        try:
            output = claude_output.strip()

            # null 응답 처리
            if output.lower() in ("null", "none", ""):
                return None

            json_str = self._extract_json_string(output)
            if not json_str:
                return None

            data = json.loads(json_str)
            if not isinstance(data, dict):
                return None

            # method_config 키가 있는 경우
            if "method_config" in data and isinstance(data["method_config"], dict):
                return {
                    "channel_type": data.get("channel_type", "rss"),
                    "method_config": data["method_config"],
                }

            return None

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"method_config JSON 파싱 실패: {e}")
            return None

    @staticmethod
    def _extract_json_string(text: str) -> Optional[str]:
        """응답 텍스트에서 JSON 부분 추출.

        코드 블록(```) 제거 후 배열/객체 경계 탐색.

        Args:
            text: 원본 텍스트.

        Returns:
            JSON 문자열 또는 None.
        """
        if not text:
            return None

        # 코드 블록 제거
        if "```" in text:
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        # 배열 우선 탐색
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and start < end:
            return text[start:end + 1]

        # 객체 탐색
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return text[start:end + 1]

        return None
