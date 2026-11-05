# -*- coding: utf-8 -*-
"""拉取摸鱼源 -> 更新 fish.json（供 GitHub Actions 定时双推使用）
- 源: https://6800.kstore.vip/fish.json
- 强制 logo = GitLink 蓝色头像 CDN 直链
- 首站 name = "自动更新时间：{北京时间}"
- 源不可达: 不破坏现有内容，仅把首站标记为「在线源获取失败」
- 无变化不写盘；有变化写盘并输出 changed=true
"""
import json, os, ssl, sys, datetime, urllib.request
from urllib.parse import urlsplit, urlunsplit

SOURCES = ["https://6800.kstore.vip/fish.json"]
LOGO = "https://cdn09022024.gitlink.org.cn/api/v1/repos/Miro/Miro/raw/logo.jpg?ref=master"
UA = ("Mozilla/5.0 (Linux; Android 11; TV) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/537.36 okhttp/3.12.1")
FISH_PATH = "fish.json"
MIN_SITES = 50
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def to_ascii(url):
    p = urlsplit(url)
    try:
        host = p.hostname.encode("idna").decode("ascii")
    except Exception:
        host = p.hostname
    port = ":" + str(p.port) if p.port else ""
    return urlunsplit((p.scheme, host + port, p.path, p.query, p.fragment))


def fetch(url):
    req = urllib.request.Request(to_ascii(url), headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        return resp.read()


def read_old():
    if not os.path.exists(FISH_PATH):
        return None, None
    with open(FISH_PATH, "r", encoding="utf-8") as f:
        txt = f.read()
    try:
        return txt, json.loads(txt)
    except Exception:
        return txt, None


def save(content, changed):
    if not changed:
        print("内容无变化，跳过写盘")
        return
    with open(FISH_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("已写入 fish.json")


def main():
    data = None
    for url in SOURCES:
        try:
            data = json.loads(fetch(url).decode("utf-8", "ignore"))
            print("拉取成功:", url)
            break
        except Exception as e:
            print("拉取失败:", url, str(e)[:150])

    old_txt, old_data = read_old()

    # 源全部不可达：不破坏现有源，仅标记首站
    if data is None or not (data.get("sites") or []):
        print("摸鱼源不可达，标记首站为 在线源获取失败")
        base = old_data
        if not base or not base.get("sites"):
            print("现有 fish.json 无站点，无法标记，跳过")
            return 0
        base["sites"][0]["name"] = "在线源获取失败"
        new_txt = json.dumps(base, ensure_ascii=False, separators=(",", ":"))
        save(new_txt, new_txt != old_txt)
        return 0

    sites = data.get("sites") or []
    if len(sites) < MIN_SITES:
        print("站点数异常(%d)，跳过，不破坏现有源" % len(sites))
        return 0

    data["logo"] = LOGO
    bj = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    sites[0]["name"] = "自动更新时间：" + bj.strftime("%Y-%m-%d %H:%M")
    new_txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    changed = new_txt != old_txt
    print("站点数: %d, 首站: %s, 变化: %s" % (len(sites), sites[0]["name"], changed))
    save(new_txt, changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
