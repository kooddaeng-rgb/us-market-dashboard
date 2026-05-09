"""
미국 시장 일일 브리핑 - GitHub Actions 자동 생성 스크립트
매일 한국 시간 07:00 (UTC 22:00 전날) 실행
"""
import requests, urllib3, json, os, re
from datetime import datetime, timezone, timedelta

urllib3.disable_warnings()

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)

# 월요일이면 금요일 데이터, 아니면 전날
weekday = now.weekday()  # 0=월 6=일
if weekday == 0:
    target = now - timedelta(days=3)
elif weekday == 6:
    target = now - timedelta(days=2)
elif weekday == 5:
    target = now - timedelta(days=1)
else:
    target = now - timedelta(days=1)

DAY_KOR = ["월","화","수","목","금","토","일"]
label   = f"{target.month}/{target.day} {DAY_KOR[target.weekday()]}"
kor_day = f"{now.month}/{now.day} {DAY_KOR[now.weekday()]} 아침"
day_id  = f"d{target.month:02d}{target.day:02d}"
updated = now.strftime("%Y-%m-%d %H:%M")

# ── 1. 데이터 수집 ──────────────────────────────────────
def fetch(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(url, params={"interval":"1d","range":"1mo"},
                        headers={"User-Agent":"Mozilla/5.0"}, verify=False, timeout=10)
        result = r.json()["chart"]["result"][0]
        closes  = result["indicators"]["quote"][0]["close"]
        volumes = result["indicators"]["quote"][0]["volume"]
        pairs = [(c,v) for c,v in zip(closes,volumes) if c is not None]
        if len(pairs) < 2: return None
        prev, _ = pairs[-2]
        last, vol = pairs[-1]
        return {"close": round(last,2), "change_pct": round((last-prev)/prev*100,2),
                "volume": int(vol) if vol else 0}
    except:
        return None

print("📡 데이터 수집 중...")

indices = {"S&P500":"^GSPC","나스닥":"^IXIC","다우존스":"^DJI","러셀2000":"^RUT","VIX":"^VIX"}
index_data = {k: fetch(v) for k,v in indices.items()}

sectors = {
    "기술 XLK":"XLK","금융 XLF":"XLF","헬스케어 XLV":"XLV","에너지 XLE":"XLE",
    "소비재(임의) XLY":"XLY","소비재(필수) XLP":"XLP","산업재 XLI":"XLI",
    "소재 XLB":"XLB","유틸리티 XLU":"XLU","부동산 XLRE":"XLRE","통신 XLC":"XLC"
}
sector_data = {k: fetch(v) for k,v in sectors.items()}

tickers_to_fetch = [
    "NVDA","AMD","MU","AMAT","LRCX","KLAC","INTC",
    "MSFT","GOOGL","META","AMZN",
    "CRM","NOW","SNOW","DDOG","CRWD","PANW","FTNT","ZS",
    "CIEN","LITE","ANET","CSCO","GLW",
    "VRT","ETN","GEV","EMR","CMI",
    "TSLA","GM","F","ALB","LTHM","FLNC",
    "XOM","CVX","COP","SLB","ENPH","FSLR",
    "LLY","NVO","JNJ","ABBV","MRNA",
    "LMT","RTX","NOC","RKLB","ASTS",
    "JPM","BAC","GS","MS","V","MA",
    "NFLX","RBLX","EA","DIS",
    "ZIM","DAC","MATX",
    "NUE","STLD","FCX",
    "CCJ","CEG","BWXT","OKLO","UEC","LEU",
    "ROK","TER","ISRG",
    "EL","ULTA",
    "QCOM","TSM","AVGO","ARM",
    "GLD","SLV","NEM","WPM",
    "IONQ","RGTI","QUBT",
    "MSTR","MARA","RIOT","COIN",
]
stock_names = {
    "NVDA":"엔비디아","AMD":"AMD","MU":"마이크론","AMAT":"어플라이드머티리얼즈","LRCX":"램리서치","KLAC":"KLA","INTC":"인텔",
    "MSFT":"마이크로소프트","GOOGL":"알파벳","META":"메타","AMZN":"아마존",
    "CRM":"세일즈포스","NOW":"서비스나우","SNOW":"스노우플레이크","DDOG":"데이터독",
    "CRWD":"크라우드스트라이크","PANW":"팔로알토","FTNT":"포티넷","ZS":"지스케일러",
    "CIEN":"시에나","LITE":"라이트패스","ANET":"아리스타네트웍스","CSCO":"시스코","GLW":"코닝",
    "VRT":"버티브홀딩스","ETN":"이튼","GEV":"GE버노바","EMR":"에머슨","CMI":"커민스",
    "TSLA":"테슬라","GM":"GM","F":"포드","ALB":"알베말","LTHM":"리튬아메리카스","FLNC":"플루언스에너지",
    "XOM":"엑슨모빌","CVX":"쉐브론","COP":"코노코필립스","SLB":"슐럼버거","ENPH":"엔페이즈","FSLR":"퍼스트솔라",
    "LLY":"일라이릴리","NVO":"노보노디스크","JNJ":"존슨앤드존슨","ABBV":"애브비","MRNA":"모더나",
    "LMT":"록히드마틴","RTX":"레이시온","NOC":"노스롭그루먼","RKLB":"로켓랩","ASTS":"AST스페이스모바일",
    "JPM":"JP모건","BAC":"뱅크오브아메리카","GS":"골드만삭스","MS":"모건스탠리",
    "NFLX":"넷플릭스","RBLX":"로블록스","EA":"일렉트로닉아츠","DIS":"디즈니",
    "ZIM":"짐인티그레이션","DAC":"다나오스","MATX":"마트슨",
    "NUE":"뉴코","STLD":"스틸다이나믹스","FCX":"프리포트맥모란",
    "CCJ":"카메코","CEG":"컨스텔레이션에너지","BWXT":"BWX테크놀로지","OKLO":"오클로","UEC":"우라늄에너지","LEU":"센트러스에너지",
    "ROK":"로크웰오토메이션","TER":"테라다인","ISRG":"인튜이티브서지컬",
    "EL":"에스티로더","ULTA":"울타뷰티",
    "QCOM":"퀄컴","TSM":"TSMC","AVGO":"브로드컴","ARM":"ARM홀딩스",
    "GLD":"금ETF","SLV":"은ETF","NEM":"뉴몬트","WPM":"휠튼프레셔스",
    "IONQ":"아이온큐","RGTI":"리게티","QUBT":"퀀텀컴퓨팅",
    "MSTR":"마이크로스트래티지","MARA":"마라홀딩스","RIOT":"라이엇플랫폼스","COIN":"코인베이스",
    "V":"비자","MA":"마스터카드"
}

stock_data = {}
for t in tickers_to_fetch:
    d = fetch(t)
    if d:
        stock_data[t] = {"name": stock_names.get(t, t), **d}

fx_tickers = {"달러/원":"USDKRW=X","달러/엔":"USDJPY=X","달러/위안":"USDCNY=X"}
fx_data = {k: fetch(v) for k,v in fx_tickers.items()}

print(f"  종목 수집: {len(stock_data)}개")

# ── 2. 테마 분석 ─────────────────────────────────────────
THEMES = [
    ("🔐","사이버보안",        ["CRWD","PANW","FTNT","ZS"],          "안랩 / 이글루코퍼레이션 / 지니언스 / 한싹 / 샌즈랩"),
    ("☁️","클라우드·SaaS",    ["CRM","NOW","SNOW","DDOG"],           "더존비즈온 / 삼성SDS / NHN"),
    ("🤖","AI·데이터센터",     ["NVDA","MSFT","GOOGL","META","AMZN"],"SK하이닉스 / 삼성전자 / 네이버 / 카카오"),
    ("🔵","반도체 메모리·HBM", ["NVDA","AMD","MU"],                  "삼성전자 / SK하이닉스 / 한미반도체"),
    ("⚙️","반도체 장비·소재",  ["AMAT","LRCX","KLAC"],               "한미반도체 / 원익IPS / 주성엔지니어링"),
    ("💻","반도체 파운드리",   ["QCOM","TSM","AVGO","ARM"],           "삼성전자 / DB하이텍 / 삼성전기"),
    ("💡","광통신·네트워크",   ["CIEN","LITE","ANET","CSCO","GLW"],   "오이솔루션 / 우리로 / 에치에프알"),
    ("⚡","전력인프라·AI",     ["VRT","ETN","GEV","EMR","CMI"],       "GST / 삼성공조 / 한국단자 / 비에이치아이"),
    ("🦾","로봇·자동화",       ["ROK","TER","ISRG"],                  "레인보우로보틱스 / 현대로보틱스 / 에스피지"),
    ("🚗","자동차·모빌리티",   ["TSLA","GM","F"],                     "현대차 / 기아 / 현대모비스"),
    ("🔋","전기차·배터리",     ["TSLA","GM","F"],                     "LG에너지솔루션 / 삼성SDI / SK이노베이션"),
    ("⛏️","배터리 소재·리튬",  ["ALB","LTHM"],                        "에코프로 / 포스코홀딩스 / 엘앤에프"),
    ("🔆","ESS·에너지저장",    ["FLNC","ALB"],                        "삼성SDI / LG에너지솔루션 / 효성중공업"),
    ("☀️","신재생에너지",      ["ENPH","FSLR"],                       "한화솔루션 / OCI / 씨에스윈드"),
    ("☢️","원자력·SMR",        ["OKLO","CCJ","CEG","BWXT","UEC","LEU"],"두산에너빌리티 / 한전기술 / 보성파워텍 / 한전KPS"),
    ("⛽","에너지·정유",       ["XOM","CVX","COP","SLB"],             "S-Oil / SK이노베이션 / GS"),
    ("💊","바이오·헬스케어",   ["LLY","NVO","JNJ","ABBV","MRNA"],    "삼성바이오로직스 / 셀트리온 / 한미약품 / 유한양행"),
    ("🛡️","방산·우주드론",    ["LMT","RTX","NOC","RKLB","ASTS"],    "한화에어로스페이스 / 한국항공우주 / 현대로템"),
    ("🚢","조선·해운",         ["ZIM","DAC","MATX"],                  "HD현대중공업 / 삼성중공업 / 한화오션 / HMM"),
    ("🏗️","철강·금속",         ["NUE","STLD","FCX"],                  "포스코홀딩스 / 현대제철 / 고려아연"),
    ("🏦","금융·은행",          ["JPM","BAC","GS","MS"],               "KB금융 / 신한지주 / 하나금융지주 / 미래에셋증권"),
    ("🎮","게임·K-콘텐츠",     ["NFLX","RBLX","EA","DIS"],            "크래프톤 / 넷마블 / 하이브 / SM엔터"),
    ("💄","소비재·K-뷰티",    ["EL","ULTA"],                          "아모레퍼시픽 / LG생활건강 / 코스맥스"),
    ("🥇","귀금속·달러",       ["GLD","SLV","NEM","WPM"],             "이구산업 / 대창 / 풍산 / 고려아연"),
    ("🔮","양자컴퓨팅",        ["IONQ","RGTI","QUBT"],                "엑스게이트 / 케이씨에스 / 쏠리드"),
    ("🪙","코인·디지털자산",   ["MSTR","MARA","RIOT","COIN"],         "다날 / NHN KCP / 미투온 / 카카오페이"),
]

def sig(pct):
    if pct >=  1.5: return "hot"
    if pct >=  0.5: return "warm"
    if pct >= -0.5: return "neutral"
    if pct >= -1.5: return "cold"
    return "freeze"

theme_results = []
for icon, name, tickers, kr in THEMES:
    vals = [stock_data[t]["change_pct"] for t in tickers if t in stock_data]
    if not vals:
        continue
    avg = round(sum(vals)/len(vals), 2)
    us_parts = []
    for t in tickers:
        if t in stock_data:
            c = stock_data[t]["change_pct"]
            arr = "▲" if c >= 0 else "▼"
            us_parts.append(f"{t} {arr}{abs(c):.1f}%")
    us_str = " / ".join(us_parts[:4])
    s = sig(avg)
    note_map = {
        "hot":    f"{name} 강세 — 국내 연동주 매수 관심",
        "warm":   f"{name} 소폭 강세 — 국내 연동주 소폭 상승 기대",
        "neutral":f"{name} 혼조 — 관망",
        "cold":   f"{name} 소폭 약세 — 국내 연동주 주의",
        "freeze": f"{name} 약세 — 국내 연동주 하락 주의",
    }
    theme_results.append({
        "icon":icon,"name":name,"us":us_str,"kr":kr,
        "pct":avg,"sig":s,"note":note_map[s]
    })

# ── 3. 지수·섹터·환율 정리 ────────────────────────────────
idx_names = {"S&P500":"S&P 500","나스닥":"나스닥","다우존스":"다우존스","러셀2000":"러셀 2000","VIX":"VIX 공포"}
indices_out = []
for k,display in idx_names.items():
    d = index_data.get(k)
    if d:
        indices_out.append({"name":display,"val":f"{d['close']:,.2f}","chg":d['change_pct']})

sectors_sorted = []
for name, d in sector_data.items():
    if d:
        sectors_sorted.append({"name":name,"chg":d['change_pct']})
sectors_sorted.sort(key=lambda x: x['chg'], reverse=True)

all_stocks = [(t, sd['name'], sd['change_pct'], sd['volume'])
              for t,sd in stock_data.items() if 'change_pct' in sd]
gainers = sorted(all_stocks, key=lambda x: x[2], reverse=True)[:5]
losers  = sorted(all_stocks, key=lambda x: x[2])[:5]

def vol_str(v):
    if v >= 1_000_000: return f"{v/1_000_000:.0f}M"
    if v >= 1_000: return f"{v/1_000:.0f}K"
    return str(v)

gainers_out = [{"t":t,"n":n,"chg":round(c,2),"vol":vol_str(v)} for t,n,c,v in gainers]
losers_out  = [{"t":t,"n":n,"chg":round(c,2),"vol":vol_str(v)} for t,n,c,v in losers]

fx_out = []
for k,d in fx_data.items():
    if d:
        fx_out.append({"name":k,"val":f"{d['close']:,.2f}","chg":d['change_pct']})

# ── 4. 시장 판단 ─────────────────────────────────────────
sp = index_data.get("S&P500")
nasdaq = index_data.get("나스닥")
vix = index_data.get("VIX")
avg_idx = 0
cnt = 0
for k in ["S&P500","나스닥","다우존스"]:
    d = index_data.get(k)
    if d:
        avg_idx += d['change_pct']
        cnt += 1
avg_idx = avg_idx/cnt if cnt else 0

if avg_idx >= 1.0:
    headline, sub, statusCls = "강세 — 리스크온", "리스크온", "sig-hot"
elif avg_idx >= 0.3:
    headline, sub, statusCls = "소폭 강세", "소폭 리스크온", "sig-warm"
elif avg_idx >= -0.3:
    headline, sub, statusCls = "혼조 — 관망", "관망 우위", "sig-neutral"
elif avg_idx >= -1.0:
    headline, sub, statusCls = "소폭 약세", "소폭 리스크오프", "sig-cold"
else:
    headline, sub, statusCls = "약세 — 리스크오프", "리스크오프", "sig-freeze"

# ── 5. 인사이트 생성 ─────────────────────────────────────
hot_themes  = [t for t in theme_results if t['sig'] in ('hot','warm')][:3]
bear_themes = [t for t in theme_results if t['sig'] in ('freeze','cold')][:2]

insight_parts = []
if sp:
    insight_parts.append(f"S&P500 {sp['change_pct']:+.2f}%, 나스닥 {nasdaq['change_pct']:+.2f}% — {sub}.")
if hot_themes:
    names = " / ".join(f"{t['name']}({t['pct']:+.1f}%)" for t in hot_themes)
    insight_parts.append(f"강세 테마: {names} → 국내 연동주 매수 관심.")
if bear_themes:
    names = " / ".join(f"{t['name']}({t['pct']:+.1f}%)" for t in bear_themes)
    insight_parts.append(f"약세 테마: {names} → 국내 연동주 주의.")
if fx_out:
    krw = next((f for f in fx_out if "원" in f['name']), None)
    if krw:
        direction = "원화 약세" if krw['chg'] > 0 else "원화 강세"
        insight_parts.append(f"달러/원 {krw['val']} ({direction} {abs(krw['chg']):.2f}%) — 수출주 환율 영향 체크.")

insight = " ".join(insight_parts)

# ── 6. 뉴스 (기본 placeholder — Actions에서 추후 확장 가능) ──
news_out = [
    {"src":"Yahoo", "txt":f"S&P500 {sp['change_pct']:+.2f}% / 나스닥 {nasdaq['change_pct']:+.2f}% 마감" if sp and nasdaq else "지수 데이터 수집 완료"},
    {"src":"Yahoo", "txt":f"VIX {vix['close']:.2f} ({vix['change_pct']:+.2f}%)" if vix else "VIX 데이터"},
    {"src":"Auto",  "txt":f"강세 섹터: {sectors_sorted[0]['name']} {sectors_sorted[0]['chg']:+.2f}%" if sectors_sorted else ""},
    {"src":"Auto",  "txt":f"약세 섹터: {sectors_sorted[-1]['name']} {sectors_sorted[-1]['chg']:+.2f}%" if sectors_sorted else ""},
    {"src":"Auto",  "txt":f"급등 1위: {gainers_out[0]['t']} {gainers_out[0]['n']} {gainers_out[0]['chg']:+.1f}%" if gainers_out else ""},
]

# ── 7. 기존 HTML 읽어서 DAYS 배열 업데이트 ──────────────
print("📝 HTML 업데이트 중...")

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# DAYS 배열 추출
days_match = re.search(r'const DAYS = \[(.*?)\];\s*\n', html, re.DOTALL)
if not days_match:
    print("❌ DAYS 배열을 찾을 수 없습니다.")
    exit(1)

# 새 날짜 데이터를 JS 객체로 직렬화
def js_val(v):
    if isinstance(v, str): return json.dumps(v, ensure_ascii=False)
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    if isinstance(v, list): return "[" + ",".join(js_val(i) for i in v) + "]"
    if isinstance(v, dict): return "{" + ",".join(f"{json.dumps(k)}:{js_val(vv)}" for k,vv in v.items()) + "}"
    return json.dumps(v, ensure_ascii=False)

new_day = {
    "id": day_id,
    "label": label,
    "kor": kor_day,
    "headline": headline,
    "sub": sub,
    "statusCls": statusCls,
    "indices": indices_out,
    "sectors": sectors_sorted,
    "gainers": gainers_out,
    "losers": losers_out,
    "fx": fx_out,
    "news": news_out,
    "themes": theme_results,
    "insight": insight,
}

new_day_js = js_val(new_day)

# 기존 DAYS에서 같은 id가 있으면 교체, 없으면 추가 후 7개 초과 시 앞 제거
days_str = days_match.group(1).strip()

# id 패턴으로 해당 날짜 블록 찾아 교체 시도
id_pattern = rf'"id"\s*:\s*"{re.escape(day_id)}"'
if re.search(id_pattern, days_str):
    # 같은 날짜 이미 존재 → 전체 재구성은 복잡하므로 새 항목으로 교체 표시만
    print(f"  기존 {day_id} 항목 업데이트")

# DAYS 전체를 파싱하지 않고 단순히 맨 앞 항목 제거 + 새 항목 추가
# 기존 배열에서 첫 번째 { ... } 블록 찾아 제거 (7개 초과 시)
entry_count = len(re.findall(r'"id"\s*:', days_str))
print(f"  현재 항목 수: {entry_count}")

if entry_count >= 7:
    # 첫 번째 항목 제거: 첫 번째 { 부터 두 번째 { 직전까지
    # 블록 단위로 분리
    first_end = days_str.find('","id":', 10)
    if first_end == -1:
        # 다른 패턴 시도
        first_end = days_str.find('"id":', 5)
    # 간단하게: id 위치 기반으로 자르기
    id_positions = [m.start() for m in re.finditer(r'"id"\s*:', days_str)]
    if len(id_positions) >= 2:
        # 두 번째 id 앞의 { 찾기
        second_block_start = days_str.rfind('{', 0, id_positions[1])
        days_str = days_str[second_block_start:]
        print("  가장 오래된 항목 제거")

# 새 항목이 이미 있는지 확인
if re.search(id_pattern, days_str):
    # 해당 날짜 블록 전체를 새 것으로 교체
    id_positions = [m.start() for m in re.finditer(r'"id"\s*:', days_str)]
    target_pos = None
    for pos in id_positions:
        snippet = days_str[pos:pos+30]
        if day_id in snippet:
            target_pos = pos
            break
    if target_pos is not None:
        block_start = days_str.rfind('{', 0, target_pos)
        # 블록 끝 찾기 (중괄호 매칭)
        depth = 0
        block_end = block_start
        for i, ch in enumerate(days_str[block_start:], block_start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    block_end = i
                    break
        days_str = days_str[:block_start] + new_day_js + days_str[block_end+1:]
    new_days_content = days_str
else:
    # 새 항목 추가
    new_days_content = days_str.rstrip() + ",\n  " + new_day_js + "\n"

# HTML에서 DAYS 배열 교체
new_html = re.sub(
    r'(const DAYS = \[)(.*?)(\];\s*\n)',
    lambda m: m.group(1) + new_days_content + m.group(3),
    html, flags=re.DOTALL
)

# UPDATED 교체
new_html = re.sub(r'const UPDATED = ".*?"', f'const UPDATED = "{updated}"', new_html)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print(f"✅ index.html 생성 완료 ({label} 데이터)")
print(f"   테마: {len(theme_results)}개 / 종목: {len(stock_data)}개")
