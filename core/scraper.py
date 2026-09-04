

import os
import time
import random
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STEAM_STORE_API = "https://store.steampowered.com/api/appdetails"
STEAM_REVIEWS_API = "https://store.steampowered.com/appreviews/{}"
STEAM_USER_API = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
TEST_APPID = 730

LANGUAGE_MENU = [
    ("english", "英语"),
    ("schinese", "简体中文"),
    ("japanese", "日语"),
    ("russian", "俄语"),
    ("french", "法语"),
    ("german", "德语"),
    ("spanish", "西班牙语"),
    ("brazilian", "葡萄牙语"),
    ("koreana", "韩语"),
    ("tchinese", "繁體中文"),
    ("all", "全部语言"),
]

LANG_CODE_TO_CN = {
    "english": "英语", "schinese": "简体中文", "japanese": "日语", "russian": "俄语",
    "french": "法语", "german": "德语", "spanish": "西班牙语", "brazilian": "葡萄牙语",
    "koreana": "韩语", "tchinese": "繁體中文", "all": "全部语言",
    "vietnamese": "越南语", "polish": "波兰语", "thai": "泰语", "ukrainian": "乌克兰语",
    "bulgarian": "保加利亚语", "czech": "捷克语", "danish": "丹麦语", "dutch": "荷兰语",
    "finnish": "芬兰语", "greek": "希腊语", "hungarian": "匈牙利语", "indonesian": "印度尼西亚语",
    "italian": "意大利语", "norwegian": "挪威语", "portuguese": "葡萄牙语-葡萄牙",
    "romanian": "罗马尼亚语", "swedish": "瑞典语", "turkish": "土耳其语", "latinamerican": "西班牙语-拉丁美洲",
    "malay": "马来语", "catalan": "加泰罗尼亚语", "arabic": "阿拉伯语", "unknown": "未知语言",
}

REVIEW_FILTERS = [
    ("recent", "全部"),
    ("positive", "仅好评"),
    ("negative", "仅差评"),
]

PURCHASE_TYPES = [
    ("all", "所有购买方式"),
    ("steam", "仅Steam商店购买"),
    ("non_steam", "仅非Steam购买"),
]

TIME_FIELDS = [
    ("playtime_forever", "游戏总时长"),
    ("playtime_at_review", "评测时游戏时长"),
]

EXPORT_FORMATS = [
    ("all", "全部"),
    ("csv", "仅 CSV"),
    ("txt", "仅 TXT"),
]

PURCHASE_DISPLAY = {
    "steam": "Steam直购",
    "non_steam": "非Steam直购",
    "unknown": "未知来源",
}

def format_playtime(minutes: int) -> str:

    if minutes <= 0:
        return "0秒"
    total = int(minutes * 60)
    hours, remainder = divmod(total, 3600)
    mins, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}小时")
    if mins:
        parts.append(f"{mins}分钟")
    if secs:
        parts.append(f"{secs}秒")
    return "".join(parts)

def ts_to_str(ts: int) -> str:

    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else ""

def safe_int(value, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def build_filename(appid: int, language: str, review_type: str, purchase_type: str) -> str:

    return f"steam_{appid}_{language}_{review_type}_{purchase_type}"

class ScraperConfig:

    def __init__(self, **kwargs):

        self.timeout = 5.0
        self.retries = 2
        self.backoff = 0.2
        self.page_size = 100
        self.base_sleep = 0.2
        self.jitter = 0.05
        self.game_name_timeout = 5.0
        self.game_name_worker_timeout = 6.0

        self.export_dir = ""

        self.log_line_limit = 500
        self.auto_scroll_log = False
        self.auto_switch_to_log = False
        self.log_timestamp = True

        self.accent_color = "青绿"
        self.bg_image = ""
        self.card_transparency = 90
        self.bg_blur = 0

        self.steam_api_key = ""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> "ScraperConfig":
        cfg = cls()
        if isinstance(data, dict):
            for key, value in data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
        return cfg

class ScraperEngine:

    def __init__(self, config: Optional[ScraperConfig] = None,
                 on_log: Optional[Callable[[str], None]] = None):
        self.config = config or ScraperConfig()
        self.on_log = on_log or (lambda msg: None)
        self._stop_requested = False

    def _log(self, msg: str) -> None:
        try:
            self.on_log(str(msg))
        except Exception:
            pass

    def request_stop(self) -> None:
        self._stop_requested = True

    def reset_stop(self) -> None:
        self._stop_requested = False

    def _request(self, method: str, url: str, silent: bool = False,
                 timeout: Optional[float] = None, **kwargs) -> Optional[requests.Response]:
        headers = kwargs.pop("headers", {})
        headers.setdefault("User-Agent", USER_AGENT)
        kwargs["headers"] = headers
        kwargs["verify"] = False
        timeout = self.config.timeout if timeout is None else timeout

        attempts = max(1, int(self.config.retries)) + 1
        last_error = None
        for attempt in range(attempts):
            try:
                resp = requests.request(method, url, timeout=timeout, **kwargs)
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    wait = self.config.backoff * (2 ** attempt) + random.uniform(0, 0.5)
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait = int(retry_after)
                        except ValueError:
                            pass
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(self.config.backoff * (attempt + 1) + random.uniform(0, 0.5))
            except requests.exceptions.HTTPError:
                return None
            except Exception as exc:
                last_error = exc
                break
        if not silent and last_error is not None:
            self._log(f"[网络] 请求失败: {url} - {last_error}")
        return None

    def fetch_game_info(self, appid: int) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:

        def fetch(lang: str) -> Optional[str]:
            try:
                resp = requests.get(
                    STEAM_STORE_API,
                    params={"appids": appid, "l": lang},
                    timeout=self.config.game_name_timeout,
                    headers={"User-Agent": USER_AGENT},
                    verify=False,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    entry = data.get(str(appid), {})
                    if entry.get("success"):
                        return entry["data"]["name"]
            except Exception:
                pass
            return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            eng_future = pool.submit(fetch, "english")
            chn_future = pool.submit(fetch, "schinese")
            timeout = self.config.game_name_worker_timeout
            try:
                eng = eng_future.result(timeout=timeout)
            except FuturesTimeoutError:
                eng = None
            try:
                chn = chn_future.result(timeout=timeout)
            except FuturesTimeoutError:
                chn = None

        if eng is None and chn is None:
            return None, None, None
        eng, chn = eng or chn, chn or eng
        summary = self.fetch_reviews_summary(appid)
        return eng, chn, summary

    def test_connection(self) -> Tuple[bool, str, str]:

        self._log("正在测试 Steam 接口 ...")
        eng, chn, _ = self.fetch_game_info(TEST_APPID)
        if not eng:
            self._log("失败：无法获取游戏信息，请检查网络/代理后重试。")
            return False, "", ""
        self._log(f"成功：{eng} / {chn}")
        return True, eng, chn

    def fetch_reviews_summary(self, appid: int, language: str = "all",
                              review_filter: str = "recent",
                              purchase_type: str = "all") -> Optional[Dict]:
        params = {
            "json": 1, "language": language, "filter": review_filter,
            "purchase_type": purchase_type, "num_per_page": 1, "cursor": "*",
        }
        resp = self._request("GET", STEAM_REVIEWS_API.format(appid), params=params, silent=True)
        if not resp:
            return None
        try:
            return resp.json().get("query_summary")
        except Exception:
            return None

    def fetch_reviews(
        self,
        appid: int,
        language: str = "schinese",
        max_reviews: int = 0,
        review_filter: str = "recent",
        min_hours: float = 0.0,
        time_filter_field: str = "playtime_forever",
        purchase_type: str = "all",
        goal: int = 0,
        progress_cb: Optional[Callable[[int, int, int], None]] = None,
    ) -> Tuple[List[Dict], float, float, Dict]:

        self.reset_stop()
        start_time = time.time()
        cursor = "*"
        filtered: List[Dict] = []
        total_raw = 0
        min_minutes = min_hours * 60 if min_hours > 0 else 0
        target = max_reviews if max_reviews > 0 else float("inf")

        lang_cn = LANG_CODE_TO_CN.get(language, language)
        self._log(
            f"[抓取] AppID {appid} | 语言: {lang_cn} | "
            f"类型: {REVIEW_FILTERS_CN.get(review_filter, '全部')} | "
            f"购买: {PURCHASE_TYPES_CN.get(purchase_type, '所有购买方式')} | "
            f"时长≥{min_hours}h | 目标: {max_reviews or '不限'}"
        )

        while len(filtered) < target:
            if self._stop_requested:
                self._log("已收到停止指令，提前结束")
                break
            params = {
                "json": 1, "language": language, "filter": review_filter,
                "purchase_type": purchase_type, "num_per_page": self.config.page_size,
                "cursor": cursor,
            }
            resp = self._request("GET", STEAM_REVIEWS_API.format(appid), params=params, silent=True)
            if not resp:
                self._log("API 请求失败，停止抓取")
                break
            try:
                data = resp.json()
            except Exception as exc:
                self._log(f"JSON 解析失败: {exc}")
                break

            reviews = data.get("reviews")
            if not isinstance(reviews, list) or not reviews:
                self._log("已无更多评测，抓取结束")
                break

            total_raw += len(reviews)
            for item in reviews:
                if min_minutes > 0:
                    author = item.get("author") or {}
                    if safe_int(author.get(time_filter_field)) < min_minutes:
                        continue
                filtered.append(item)
                if len(filtered) >= target:
                    break

            valid = len(filtered)
            positive = sum(1 for r in filtered if r.get("voted_up"))
            if goal and goal > 0:
                self._log(f"[进度] 已抓取 {valid} 条 · {valid / goal * 100:.1f}%")
            else:
                self._log(f"[进度] 已抓取 {valid} 条")
            if progress_cb:
                try:
                    progress_cb(total_raw, valid, positive)
                except Exception:
                    pass

            cursor = data.get("cursor", "")
            if not cursor:
                break
            if len(filtered) < target:
                time.sleep(self.config.base_sleep + random.uniform(0, self.config.jitter))

        elapsed = time.time() - start_time
        self._log(f"[抓取] 结束：有效 {len(filtered)} 条，耗时 {elapsed:.1f}s")
        return filtered, start_time, time.time(), {}

REVIEW_FILTERS_CN = dict(REVIEW_FILTERS)
PURCHASE_TYPES_CN = dict(PURCHASE_TYPES)

def compute_stats(reviews: List[Dict], start_time: float, end_time: float,
                  official_total: Optional[int] = None) -> Dict:

    total = len(reviews)
    positive = sum(1 for r in reviews if r.get("voted_up"))

    lang_count: Dict[str, int] = {}
    lang_positive: Dict[str, int] = {}
    for r in reviews:
        lang = r.get("language", "unknown")
        lang_count[lang] = lang_count.get(lang, 0) + 1
        if r.get("voted_up"):
            lang_positive[lang] = lang_positive.get(lang, 0) + 1

    purchase_stats: Dict[str, Dict] = {}
    for r in reviews:
        key = {True: "steam", False: "non_steam"}.get(r.get("steam_purchase"), "unknown")
        item = purchase_stats.setdefault(key, {"total": 0, "positive": 0})
        item["total"] += 1
        if r.get("voted_up"):
            item["positive"] += 1

    lang_dist = sorted(
        ((lang, cnt, lang_positive.get(lang, 0)) for lang, cnt in lang_count.items()),
        key=lambda x: -x[1],
    )
    purchase_dist = sorted(
        ((key, item["total"], item["positive"]) for key, item in purchase_stats.items()),
        key=lambda x: -x[1],
    )

    return {
        "total": total,
        "positive": positive,
        "negative": total - positive,
        "positive_rate": positive / total * 100 if total else 0.0,
        "official_total": official_total,
        "completeness": (total / official_total * 100)
        if (official_total and official_total > 0) else None,
        "start_time": start_time,
        "end_time": end_time,
        "elapsed": end_time - start_time,
        "lang_dist": lang_dist,
        "purchase_dist": purchase_dist,
    }

def _get_user_names(steamids: List[str], api_key: str,
                    on_progress: Optional[Callable[[int, int], None]] = None) -> Dict[str, str]:

    if not api_key or not steamids:
        return {}
    result: Dict[str, str] = {}
    unique_ids = list(set(steamids))
    total = len(unique_ids)
    for i in range(0, total, 100):
        batch = unique_ids[i:i + 100]
        params = {"key": api_key, "steamids": ",".join(batch)}
        try:
            resp = requests.get(STEAM_USER_API, params=params, timeout=8,
                                headers={"User-Agent": USER_AGENT}, verify=False)
            players = resp.json().get("response", {}).get("players", [])
        except Exception:
            players = []
        for p in players:
            result[p.get("steamid")] = p.get("personaname", "Unknown")
        done = min(i + 100, total)
        if on_progress:
            try:
                on_progress(done, total)
            except Exception:
                pass
        if i + 100 < total:
            time.sleep(0.5)
    return result

def enrich_with_usernames(reviews: List[Dict], api_key: Optional[str],
                          on_log: Optional[Callable[[str], None]] = None,
                          on_progress: Optional[Callable[[int, int], None]] = None) -> None:

    log = on_log or (lambda m: None)
    steamids = [r["author"]["steamid"] for r in reviews
                if "author" in r and "steamid" in r["author"]]
    if not api_key or not steamids:
        if on_progress:
            try:
                on_progress(0, 0)
            except Exception:
                pass
        for r in reviews:
            author = r.setdefault("author", {})
            author["personaname"] = author.get("steamid", "未知")
        return

    total_unique = len(set(steamids))
    log(f"[昵称] 正在获取 {total_unique} 个唯一用户的昵称（约需 1-3 分钟）...")
    name_map = _get_user_names(steamids, api_key, on_progress=on_progress)
    success = 0
    for r in reviews:
        sid = r["author"].get("steamid", "")
        r["author"]["personaname"] = name_map.get(sid, sid)
        if sid in name_map:
            success += 1
    log(f"[昵称] 获取成功 {success}/{len(reviews)} 条"
        if success else "[昵称] 所有昵称获取失败，使用 SteamID 代替")

def _export_dir(out_dir: str) -> str:
    out_dir = out_dir or "."
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def _review_link(steamid: str, appid: int) -> str:
    return f"https://steamcommunity.com/profiles/{steamid}/recommended/{appid}/"

def _purchase_cn(r: Dict) -> str:
    return PURCHASE_DISPLAY.get(
        {True: "steam", False: "non_steam"}.get(r.get("steam_purchase"), "unknown"), "未知来源")

def save_to_csv(reviews: List[Dict], appid: int, language: str,
                review_type: str, purchase_type: str,
                out_dir: str = "", on_log: Optional[Callable[[str], None]] = None) -> str:

    if not reviews:
        return ""
    log = on_log or (lambda m: None)
    import pandas as pd

    rows = []
    for r in reviews:
        a = r.get("author", {})
        steamid = a.get("steamid", "")
        rows.append({
            "用户SteamID": steamid,
            "用户昵称": a.get("personaname", ""),
            "评测链接": _review_link(steamid, appid),
            "评测语言": r.get("language", ""),
            "评测内容": r.get("review", ""),
            "创建时间": ts_to_str(r.get("timestamp_created", 0)),
            "更新时间": ts_to_str(r.get("timestamp_updated", 0)),
            "是否推荐": r.get("voted_up", False),
            "有用数": safe_int(r.get("votes_up")),
            "有趣数": safe_int(r.get("votes_funny")),
            "评论数": safe_int(r.get("comment_count")),
            "游戏总时长(分钟)": safe_int(a.get("playtime_forever")),
            "评测时游戏时长(分钟)": safe_int(a.get("playtime_at_review")),
            "最近两周时长(分钟)": safe_int(a.get("playtime_last_two_weeks")),
            "最后游玩时间": ts_to_str(a.get("last_played", 0)),
        })
    path = os.path.join(_export_dir(out_dir), build_filename(appid, language, review_type, purchase_type) + ".csv")
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    log(f"[导出] CSV 已保存: {path}")
    return path

def save_to_txt(reviews: List[Dict], appid: int, game_eng: str, game_chn: str,
                language: str, review_type: str, purchase_type: str,
                out_dir: str = "", on_log: Optional[Callable[[str], None]] = None) -> str:

    if not reviews:
        return ""
    log = on_log or (lambda m: None)
    filename = build_filename(appid, language, review_type, purchase_type) + ".txt"
    path = os.path.join(_export_dir(out_dir), filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{'=' * 80}\nSteam游戏评测报告\n"
                f"游戏ID: {appid}\n英文名: {game_eng}\n中文名: {game_chn}\n"
                f"查询语言: {language}\n评测类型: {review_type}\n购买来源: {purchase_type}\n"
                f"评测总数: {len(reviews)}\n"
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'=' * 80}\n\n")
        for idx, r in enumerate(reviews, 1):
            a = r.get("author", {})
            steamid = a.get("steamid", "")
            f.write(f"[评测 #{idx}]\n"
                    f"用户: {a.get('personaname', a.get('steamid', '未知'))}\n"
                    f"SteamID: {steamid}\n"
                    f"评测链接: {_review_link(steamid, appid)}\n"
                    f"推荐: {'推荐' if r.get('voted_up') else '不推荐'}\n"
                    f"语言: {r.get('language', '未知')}\n"
                    f"购买来源: {_purchase_cn(r)}\n"
                    f"创建: {ts_to_str(r.get('timestamp_created', 0))}\n"
                    f"更新: {ts_to_str(r.get('timestamp_updated', 0))}\n"
                    f"总时长: {format_playtime(safe_int(a.get('playtime_forever')))}\n"
                    f"评测时时长: {format_playtime(safe_int(a.get('playtime_at_review')))}\n"
                    f"最近两周: {format_playtime(safe_int(a.get('playtime_last_two_weeks')))}\n"
                    f"最后游戏: {ts_to_str(a.get('last_played', 0))}\n"
                    f"有用: {safe_int(r.get('votes_up'))}  "
                    f"有趣: {safe_int(r.get('votes_funny'))}  "
                    f"评论: {safe_int(r.get('comment_count'))}\n"
                    f"内容:\n{r.get('review', '无内容')}\n{'-' * 80}\n\n")
    log(f"[导出] TXT 已保存: {path}")
    return path

def validate_api_key(api_key: str) -> bool:

    if not api_key:
        return False
    params = {"key": api_key, "steamids": "76561197960287930"}
    try:
        resp = requests.get(STEAM_USER_API, params=params, timeout=8,
                            headers={"User-Agent": USER_AGENT}, verify=False)
        players = resp.json().get("response", {}).get("players")
        return resp.status_code == 200 and bool(players)
    except Exception:
        return False

def run_scrape(
    engine: ScraperEngine,
    appid: int,
    language: str,
    max_reviews: int,
    review_filter: str,
    purchase_type: str,
    min_hours: float,
    time_filter_field: str,
    api_key: Optional[str],
    export_dir: str,
    export_format: str = "all",
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    on_stage: Optional[Callable[[str], None]] = None,
    on_official: Optional[Callable[[Optional[int]], None]] = None,
    on_nickname_progress: Optional[Callable[[int, int], None]] = None,
) -> Dict:

    result = {"success": False, "reason": "", "stats": None,
              "game_eng": "", "game_chn": ""}
    stage = on_stage or (lambda m: None)
    log = engine._log

    stage("正在获取游戏信息 ...")
    eng, chn, summary = engine.fetch_game_info(appid)
    if not eng:
        result["reason"] = "无法获取游戏信息（网络/代理异常，或 AppID 不存在）"
        log(f"[错误] {result['reason']}")
        return result
    result["game_eng"], result["game_chn"] = eng, chn
    log(f"[游戏] {eng} / {chn}")

    official_total = None
    if summary and summary.get("total_reviews"):
        official_total = summary["total_reviews"]
        official_pos = summary.get("total_positive", 0)
        log(f"[官方] 总评测 {official_total} 条，好评 {official_pos} 条，"
            f"好评率 {official_pos / official_total * 100:.1f}%")
    else:
        log("[官方] 无法获取官方评测总数（建议更换加速器/代理），将不进行完整性对比")
    if on_official:
        try:
            on_official(official_total)
        except Exception:
            pass

    reviews, start_ts, end_ts, _ = engine.fetch_reviews(
        appid, language, max_reviews, review_filter,
        min_hours=min_hours, time_filter_field=time_filter_field,
        purchase_type=purchase_type,
        goal=max_reviews if max_reviews > 0 else (official_total or 0),
        progress_cb=progress_cb,
    )
    if not reviews:
        result["reason"] = "没有符合条件（语言/类型/时长）的评测"
        log(f"[结果] {result['reason']}，未导出文件")
        return result

    stage("正在获取用户昵称（约需 1-3 分钟）...")
    enrich_with_usernames(reviews, api_key, on_log=engine.on_log,
                          on_progress=on_nickname_progress)

    result["stats"] = compute_stats(reviews, start_ts, end_ts, official_total)
    result["success"] = True

    review_type_display = dict(REVIEW_FILTERS).get(review_filter, "all")
    export_format = export_format or "all"
    stage("正在导出报告 ...")
    if export_format in ("csv", "all"):
        save_to_csv(reviews, appid, language, review_type_display, purchase_type,
                    out_dir=export_dir, on_log=engine.on_log)
    if export_format in ("txt", "all"):
        save_to_txt(reviews, appid, eng, chn, language, review_type_display,
                    purchase_type, out_dir=export_dir, on_log=engine.on_log)
    return result