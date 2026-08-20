"""
텔레그램 봇 상수 정의
- 대화 상태 (ConversationHandler States)
- Google News RSS URL 패턴
- 뉴스 토픽 목록
- 앵커 캐릭터 및 TTS 매핑
"""

from enum import IntEnum


# ─────────────────────────────────────────────
# 대화 상태 (ConversationHandler States)
# ─────────────────────────────────────────────

class States(IntEnum):
    """ConversationHandler 상태 코드"""
    NEWS_FETCH = 0         # 뉴스 수집 중
    NEWS_SELECT = 1        # 뉴스 목록 선택 대기
    RESEARCH = 2           # 기사 본문 스크래핑 중
    ANCHOR_SELECT = 3      # 앵커 캐릭터 선택 대기
    SCRIPT_REVIEW = 4      # 대본 검토 대기
    SCENARIO_REVIEW = 5    # 시나리오 검토 대기
    SCENE_EDIT = 6         # 씬 편집 대기
    GENERATE = 7           # 영상 생성 중 (큐에 등록됨)
    VERIFY = 8             # 영상 검증 대기
    COMPLETE = 9           # 완료
    VIDEO_MODE_SELECT = 10 # 영상 모드 선택 대기 (시나리오 확정 후)


# ─────────────────────────────────────────────
# Google News RSS URL 패턴
# ─────────────────────────────────────────────

RSS_URL_PATTERNS: dict[str, str] = {
    "TOP": "https://news.google.com/rss?hl={lang}&gl={country}&ceid={country}:{lang}",
    "TECHNOLOGY": (
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "BUSINESS": (
        "https://news.google.com/rss/headlines/section/topic/BUSINESS"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "SPORTS": (
        "https://news.google.com/rss/headlines/section/topic/SPORTS"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "ENTERTAINMENT": (
        "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "HEALTH": (
        "https://news.google.com/rss/headlines/section/topic/HEALTH"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "SCIENCE": (
        "https://news.google.com/rss/headlines/section/topic/SCIENCE"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "NATION": (
        "https://news.google.com/rss/headlines/section/topic/NATION"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "WORLD": (
        "https://news.google.com/rss/headlines/section/topic/WORLD"
        "?hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
    "SEARCH": (
        "https://news.google.com/rss/search?q={query}"
        "&hl={lang}&gl={country}&ceid={country}:{lang}"
    ),
}


# ─────────────────────────────────────────────
# 분야별 직접 RSS 소스
# 각 분야 키에 대응하는 RSS URL 목록.
# Google News 외에 개별 매체 피드를 직접 수집한다.
# ─────────────────────────────────────────────

CATEGORY_RSS_FEEDS: dict[str, list[dict[str, str]]] = {
    "general": [
        {"name": "연합뉴스 전체", "url": "https://www.yna.co.kr/rss/news.xml"},
        {"name": "BBC News",      "url": "http://feeds.bbci.co.uk/news/rss.xml"},
        {"name": "CNN",           "url": "http://rss.cnn.com/rss/edition.rss"},
    ],
    "tech": [
        {"name": "TechCrunch",  "url": "https://techcrunch.com/feed/"},
        {"name": "VentureBeat", "url": "https://venturebeat.com/feed/"},
        {"name": "전자신문",     "url": "https://rss.etnews.com/Section901.xml"},
    ],
    "economy": [
        {"name": "CNBC",     "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex"},
        {"name": "한국경제",  "url": "https://www.hankyung.com/feed/all-news"},
        {"name": "매일경제",  "url": "https://www.mk.co.kr/rss/30000001/"},
    ],
    "politics": [
        {"name": "BBC News",    "url": "http://feeds.bbci.co.uk/news/rss.xml"},
        {"name": "CNN",         "url": "http://rss.cnn.com/rss/edition.rss"},
        {"name": "조선일보",    "url": "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml"},
        {"name": "한겨레",      "url": "https://www.hani.co.kr/rss/"},
        {"name": "연합뉴스 정치", "url": "https://www.yna.co.kr/rss/politics.xml"},
    ],
    "international": [
        {"name": "BBC World",       "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "CNN World",       "url": "http://rss.cnn.com/rss/edition_world.rss"},
        {"name": "연합뉴스 국제",    "url": "https://www.yna.co.kr/rss/international.xml"},
    ],
    "society": [
        {"name": "SBS 사회",       "url": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=01&plink=RSSREADER"},
        {"name": "연합뉴스 사회",   "url": "https://www.yna.co.kr/rss/society.xml"},
    ],
    "entertainment": [
        {"name": "Soompi",         "url": "https://www.soompi.com/feed"},
        {"name": "스포츠경향 연예", "url": "https://sports.khan.co.kr/rss/entertainment"},
        {"name": "SBS 연예",       "url": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=14&plink=RSSREADER"},
    ],
    "culture": [
        {"name": "한국연예스포츠신문 문화", "url": "http://www.koreaes.com/rss/allArticle.xml"},
        {"name": "SBS 생활문화",           "url": "https://news.sbs.co.kr/news/SectionRssFeed.do?sectionId=09&plink=RSSREADER"},
    ],
    "sports": [
        {"name": "ESPN",           "url": "https://www.espn.com/espn/rss/news"},
        {"name": "BBC Sport",      "url": "http://feeds.bbci.co.uk/sport/rss.xml"},
        {"name": "스포츠경향",      "url": "https://sports.khan.co.kr/rss/sports-all"},
    ],
    "science": [
        {"name": "Nature",       "url": "https://www.nature.com/nature.rss"},
        {"name": "ScienceDaily", "url": "https://www.sciencedaily.com/rss/all.xml"},
        {"name": "Space.com",    "url": "https://www.space.com/feeds/all"},
    ],
    "lifestyle": [
        {"name": "연합뉴스 생활", "url": "https://www.yna.co.kr/rss/lifestyle.xml"},
    ],
    # ─── 멀티채널 신규 도메인 (G1) ───────────────────────────────────────
    "ai": [
        # 뉴스
        {"name": "TechCrunch AI",   "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
        {"name": "VentureBeat AI",  "url": "https://venturebeat.com/category/ai/feed/"},
        {"name": "Wired AI",        "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
        {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
        {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/index"},
        {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "THE DECODER",     "url": "https://the-decoder.com/feed/"},
        {"name": "Unite.AI",        "url": "https://unite.ai/feed"},
        {"name": "DailyAI",         "url": "https://dailyai.com/feed"},
        {"name": "AI Trends",       "url": "https://www.aitrends.com/feed/"},
        # 기업 블로그
        {"name": "OpenAI Blog",     "url": "https://openai.com/blog/rss/"},
        {"name": "Google AI Blog",  "url": "http://feeds.feedburner.com/blogspot/gJZg"},
        {"name": "Meta AI Blog",    "url": "https://ai.meta.com/blog/rss/"},
        {"name": "Microsoft AI Blog", "url": "https://blogs.microsoft.com/ai/feed/"},
        {"name": "Microsoft Research", "url": "https://www.microsoft.com/en-us/research/feed/"},
        {"name": "NVIDIA AI Blog",  "url": "http://feeds.feedburner.com/nvidiablog"},
        {"name": "Google DeepMind Blog", "url": "https://deepmind.com/blog/feed/basic/"},
        {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml"},
        {"name": "LangChain Blog",  "url": "https://blog.langchain.dev/rss/"},
        {"name": "AWS ML Blog",     "url": "https://aws.amazon.com/blogs/machine-learning/feed"},
        # 뉴스레터
        {"name": "Import AI",       "url": "https://importai.substack.com/feed"},
        {"name": "The Batch (DeepLearning.AI)", "url": "https://www.deeplearning.ai/the-batch/feed"},
        {"name": "Ben's Bites",     "url": "https://news.bensbites.com/feed"},
        {"name": "Last Week in AI", "url": "https://lastweekin.ai/feed"},
        {"name": "TheSequence",     "url": "https://thesequence.substack.com/feed"},
        # 포럼 / Reddit
        {"name": "Hacker News AI",  "url": "https://hnrss.org/newest?q=AI"},
        {"name": "Lobste.rs AI",    "url": "https://lobste.rs/t/ai.rss"},
        {"name": "Reddit r/MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/.rss"},
        {"name": "Reddit r/LocalLLaMA", "url": "https://www.reddit.com/r/LocalLLaMA/.rss"},
        # 리서치 허브
        {"name": "arXiv cs.AI",     "url": "https://rss.arxiv.org/rss/cs.AI"},
        {"name": "arXiv cs.CL",     "url": "https://rss.arxiv.org/rss/cs.CL"},
        {"name": "arXiv cs.CV",     "url": "https://rss.arxiv.org/rss/cs.CV"},
        {"name": "arXiv cs.LG",     "url": "https://rss.arxiv.org/rss/cs.LG"},
        # 개인 블로그
        {"name": "Simon Willison",  "url": "https://simonwillison.net/atom/everything/"},
        {"name": "Lil'Log (Lilian Weng)", "url": "https://lilianweng.github.io/index.xml"},
        # 학술
        {"name": "BAIR Blog",       "url": "https://bair.berkeley.edu/blog/feed.xml"},
        {"name": "MIT News AI",     "url": "http://news.mit.edu/rss/topic/artificial-intelligence2"},
        # 한국 뉴스
        {"name": "전자신문 AI",     "url": "http://rss.etnews.com/Section901.xml"},
    ],
    "blockchain": [
        # 주요 뉴스
        {"name": "CoinDesk",        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"},
        {"name": "CoinTelegraph",   "url": "https://cointelegraph.com/rss"},
        {"name": "Decrypt",         "url": "https://decryptmedia.com/feed/"},
        {"name": "CryptoSlate",     "url": "https://cryptoslate.com/feed/"},
        {"name": "Blockworks",      "url": "https://blockworks.co/feed/"},
        {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/feed"},
        {"name": "BeInCrypto",      "url": "https://beincrypto.com/feed/"},
        {"name": "Bitcoinist",      "url": "https://bitcoinist.com/feed/"},
        {"name": "NewsBTC",         "url": "https://newsbtc.com/feed/"},
        {"name": "CryptoNews",      "url": "https://cryptonews.com/news/feed/"},
        {"name": "The Defiant",     "url": "https://thedefiant.io/api/feed"},
        # L1 / 프로토콜 블로그
        {"name": "Ethereum Blog",   "url": "https://blog.ethereum.org/feed.xml"},
        {"name": "Vitalik Buterin Blog", "url": "https://vitalik.ca/feed.xml"},
        {"name": "Bitcoin Core Blog", "url": "https://bitcoincore.org/en/rss.xml"},
        {"name": "Chainlink Blog",  "url": "https://blog.chain.link/rss/"},
        {"name": "Polkadot Blog",   "url": "https://polkadot.network/blog/feed"},
        # 거래소 블로그
        {"name": "Coinbase Blog",   "url": "https://blog.coinbase.com/feed"},
        # 리서치
        {"name": "Messari Research", "url": "https://messari.io/rss"},
        {"name": "Glassnode Insights", "url": "https://insights.glassnode.com/rss/"},
        {"name": "Chainalysis Blog", "url": "https://blog.chainalysis.com/feed/"},
        {"name": "Paradigm",        "url": "https://www.paradigm.xyz/rss/feed.xml"},
        {"name": "a16z Crypto",     "url": "https://a16z.com/category/blockchain-cryptocurrencies/feed/"},
        # 뉴스레터
        {"name": "Week in Ethereum", "url": "https://weekinethereumnews.com/feed/"},
        {"name": "Bitcoin Optech",  "url": "https://bitcoinops.org/feed.xml"},
        {"name": "The Pomp Letter", "url": "https://pomp.substack.com/feed"},
        # Reddit
        {"name": "Reddit r/CryptoCurrency", "url": "https://www.reddit.com/r/CryptoCurrency/.rss"},
        {"name": "Reddit r/ethereum", "url": "https://www.reddit.com/r/ethereum/.rss"},
        {"name": "Reddit r/bitcoin", "url": "https://www.reddit.com/r/bitcoin/.rss"},
        # 팟캐스트
        {"name": "Bankless",        "url": "https://feeds.megaphone.fm/bankless"},
        # NFT / DeFi
        {"name": "DappRadar Blog",  "url": "https://dappradar.com/blog/feed"},
        # L2 블로그
        {"name": "Aave Mirror",     "url": "https://aave.mirror.xyz/feed/atom"},
        {"name": "Optimism Mirror", "url": "https://optimism.mirror.xyz/feed/atom"},
    ],
    "tesla": [
        # Tesla 전문
        {"name": "Electrek",        "url": "https://electrek.co/feed/"},
        {"name": "Teslarati",       "url": "https://www.teslarati.com/feed/"},
        {"name": "Not A Tesla App", "url": "https://www.notateslaapp.com/feed/"},
        {"name": "TESMANIAN",       "url": "https://www.tesmanian.com/blogs/tesmanian-blog.atom"},
        {"name": "Drive Tesla Canada", "url": "https://driveteslacanada.ca/feed/"},
        {"name": "Tesla Blog",      "url": "https://www.tesla.com/blog/feed"},
        {"name": "EVANNEX",         "url": "https://evannex.com/blogs/news.atom"},
        # EV 종합
        {"name": "InsideEVs",       "url": "https://insideevs.com/rss/news/all/"},
        {"name": "CleanTechnica",   "url": "https://cleantechnica.com/feed/"},
        {"name": "Green Car Reports", "url": "https://www.greencarreports.com/rss"},
        {"name": "CarScoops",       "url": "https://www.carscoops.com/feed/"},
        {"name": "The Drive",       "url": "https://www.thedrive.com/feed"},
        {"name": "Charged EVs",     "url": "https://chargedevs.com/feed/"},
        {"name": "CnEVPost",        "url": "https://cnevpost.com/feed/"},
        # SpaceX / 우주
        {"name": "NASASpaceflight", "url": "https://www.nasaspaceflight.com/feed/"},
        {"name": "SpaceNews",       "url": "https://spacenews.com/feed/"},
        {"name": "Spaceflight Now", "url": "https://spaceflightnow.com/feed/"},
        {"name": "Ars Technica Space", "url": "https://arstechnica.com/space/feed/"},
        {"name": "Everyday Astronaut", "url": "https://everydayastronaut.com/feed/"},
        {"name": "Teslarati SpaceX", "url": "https://www.teslarati.com/category/spacex/feed/"},
        # 자율주행
        {"name": "The Road to Autonomy", "url": "https://www.roadtoautonomy.com/feed/"},
        {"name": "Torque News",     "url": "https://www.torquenews.com/rss.xml"},
        # Reddit
        {"name": "Reddit r/TeslaMotors", "url": "https://www.reddit.com/r/TeslaMotors/.rss"},
        {"name": "Reddit r/SpaceX", "url": "https://www.reddit.com/r/spacex/.rss"},
        {"name": "Reddit r/electricvehicles", "url": "https://www.reddit.com/r/electricvehicles/.rss"},
        # 에너지
        {"name": "Energy-Storage.News", "url": "https://www.energy-storage.news/feed/"},
        {"name": "Canary Media",    "url": "https://www.canarymedia.com/rss-feed"},
        # 테크 뉴스 Tesla 태그
        {"name": "TechCrunch Tesla", "url": "https://techcrunch.com/tag/tesla/feed/"},
        {"name": "Ars Technica Cars", "url": "https://arstechnica.com/cars/feed/"},
        # 한국 EV
        {"name": "EV Post 한국",    "url": "https://www.evpost.co.kr/wp/feed/"},
    ],
}

# 분야 키 → Google News 토픽 키 매핑 (보조 소스)
CATEGORY_TO_GOOGLE_TOPIC: dict[str, str] = {
    "general": "TOP",
    "tech": "TECHNOLOGY",
    "economy": "BUSINESS",
    "politics": "NATION",
    "international": "WORLD",
    "society": "NATION",
    "entertainment": "ENTERTAINMENT",
    "culture": "ENTERTAINMENT",
    "sports": "SPORTS",
    "science": "SCIENCE",
    "lifestyle": "HEALTH",
    # 멀티채널 신규 도메인 (G1)
    "ai": "TECHNOLOGY",
    "blockchain": "BUSINESS",
    "tesla": "TECHNOLOGY",
}


# ─────────────────────────────────────────────
# 뉴스 토픽 목록 (UI 표시용)
# ─────────────────────────────────────────────

NEWS_TOPICS: list[dict] = [
    {"key": "general",       "label": "전체",       "emoji": ""},
    {"key": "tech",          "label": "테크/IT",    "emoji": ""},
    {"key": "economy",       "label": "경제/금융",  "emoji": ""},
    {"key": "politics",      "label": "정치",       "emoji": ""},
    {"key": "international", "label": "국제",       "emoji": ""},
    {"key": "society",       "label": "사회",       "emoji": ""},
    {"key": "entertainment", "label": "연예",       "emoji": ""},
    {"key": "culture",       "label": "문화/예술",  "emoji": ""},
    {"key": "sports",        "label": "스포츠",     "emoji": ""},
    {"key": "science",       "label": "과학",       "emoji": ""},
    {"key": "lifestyle",     "label": "생활",       "emoji": ""},
    # 멀티채널 신규 도메인 (G1)
    {"key": "ai",            "label": "AI/인공지능",    "emoji": ""},
    {"key": "blockchain",    "label": "블록체인/크립토", "emoji": ""},
    {"key": "tesla",         "label": "테슬라/EV",       "emoji": ""},
    {"key": "SEARCH",        "label": "키워드 검색", "emoji": ""},
]


# ─────────────────────────────────────────────
# 리서치 도메인 시드 데이터 (초기 등록용)
# ResearchDomainService.seed_initial_domains() 에서 사용
# ─────────────────────────────────────────────

RESEARCH_DOMAIN_SEED_DATA: list[dict] = [
    {
        "name": "ai",
        "display_name": "AI/인공지능",
        "description": "인공지능, 머신러닝, LLM, 딥러닝 관련 뉴스 및 연구 수집",
        "core_keywords": [
            "artificial intelligence", "AI", "machine learning", "LLM",
            "GPT", "ChatGPT", "Claude", "Gemini", "deep learning",
            "neural network", "OpenAI", "Anthropic", "Google DeepMind",
            "transformer", "RAG", "AI agent", "인공지능", "머신러닝",
        ],
    },
    {
        "name": "blockchain",
        "display_name": "블록체인/크립토",
        "description": "블록체인, 암호화폐, DeFi, NFT, Web3 관련 뉴스 수집",
        "core_keywords": [
            "blockchain", "cryptocurrency", "Bitcoin", "BTC", "Ethereum", "ETH",
            "DeFi", "NFT", "Web3", "crypto", "smart contract", "Layer 2",
            "staking", "wallet", "CoinDesk", "블록체인", "암호화폐", "비트코인",
        ],
    },
    {
        "name": "tesla",
        "display_name": "테슬라/EV",
        "description": "테슬라, 전기차, SpaceX, FSD, 배터리 기술 관련 뉴스 수집",
        "core_keywords": [
            "Tesla", "TSLA", "Elon Musk", "electric vehicle", "EV",
            "FSD", "Full Self-Driving", "Autopilot", "SpaceX", "Starship",
            "Cybertruck", "Model S", "Model 3", "Model Y", "battery",
            "charging", "테슬라", "전기차", "자율주행",
        ],
    },
]


# ─────────────────────────────────────────────
# 앵커 캐릭터 목록과 TTS 매핑
# 모든 캐릭터는 ko-KR-SunHiNeural 음성 사용
# ─────────────────────────────────────────────

# edge-tts에서 지원하는 한국어 뉴스 음성
DEFAULT_TTS_VOICE = "ko-KR-SunHiNeural"

ANCHOR_CHARACTERS: dict[str, dict] = {
    "Emma": {
        "name": "Emma",
        "display_name": "Emma (연예/트렌드)",
        "character_sheet_id": "Emma",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "밝고 에너지 넘치는 뉴스 진행, 트렌드에 민감",
    },
    "Sophia": {
        "name": "Sophia",
        "display_name": "Sophia (정치/경제)",
        "character_sheet_id": "Sophia",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "시크하고 지적인 분석형 뉴스 진행",
    },
    "Ruby": {
        "name": "Ruby",
        "display_name": "Ruby (테크/IT)",
        "character_sheet_id": "Ruby",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "호기심 많고 활기차며 기술을 쉽게 설명",
    },
    "Hana": {
        "name": "Hana",
        "display_name": "Hana (사회/문화)",
        "character_sheet_id": "Hana",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "따뜻하고 공감 능력 뛰어난 부드러운 진행",
    },
    "Mia": {
        "name": "Mia",
        "display_name": "Mia (스포츠)",
        "character_sheet_id": "Mia",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "자신감 넘치고 에너지 있는 스포츠 뉴스 진행",
    },
    "Chihiro": {
        "name": "Chihiro",
        "display_name": "Chihiro (지브리풍)",
        "character_sheet_id": "Chihiro",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "순수하고 맑은 목소리로 따뜻하게 전달",
    },
    "Rina": {
        "name": "Rina",
        "display_name": "Rina (애니풍)",
        "character_sheet_id": "Rina",
        "default_voice": DEFAULT_TTS_VOICE,
        "tone": "신비롭고 우아한 분위기로 뉴스 전달",
    },
}


# ─────────────────────────────────────────────
# 기타 상수
# ─────────────────────────────────────────────

# 뉴스 수집 기본 설정
DEFAULT_NEWS_LANGUAGE = "en"
DEFAULT_NEWS_COUNTRY = "US"
DEFAULT_NEWS_LIMIT = 10
MAX_NEWS_LIMIT = 20

# 콜백 데이터 접두사
CALLBACK_TOPIC_PREFIX = "topic_"
CALLBACK_NEWS_PREFIX = "news_"
CALLBACK_ANCHOR_PREFIX = "anchor_"
CALLBACK_SCENE_PREFIX = "scene_"
CALLBACK_CONFIRM = "confirm"
CALLBACK_REGENERATE = "regenerate"
CALLBACK_CANCEL = "cancel"
