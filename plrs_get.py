# -*- coding: utf-8 -*-
"""
PolarisCode (PLRS) 全店舗JSON生成スクリプト（進捗表示強化版）
・都道府県ごと・ページごとの進捗をリアルタイム出力
・開始時刻から総経過時間を最後に表示
・旧URLが404の場合もログで明確にわかる
"""

import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import time
from datetime import datetime

start_time = datetime.now()
print(f"処理開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')} JST\n")

# JPコード → エリアコード マッピング
pref_to_area = {
    '01': 'AR-01', '02': 'AR-01', '03': 'AR-01', '04': 'AR-01', '05': 'AR-01', '06': 'AR-01', '07': 'AR-01',
    '08': 'AR-02', '09': 'AR-02', '10': 'AR-02', '11': 'AR-02', '12': 'AR-02', '13': 'AR-02', '14': 'AR-02',
    '15': 'AR-03', '16': 'AR-03', '17': 'AR-03', '18': 'AR-03', '19': 'AR-03', '20': 'AR-03',
    '21': 'AR-03', '22': 'AR-03', '23': 'AR-03', '24': 'AR-03',
    '25': 'AR-04', '26': 'AR-04', '27': 'AR-04', '28': 'AR-04', '29': 'AR-04', '30': 'AR-04',
    '31': 'AR-05', '32': 'AR-05', '33': 'AR-05', '34': 'AR-05', '35': 'AR-05',
    '36': 'AR-06', '37': 'AR-06', '38': 'AR-06', '39': 'AR-06',
    '40': 'AR-07', '41': 'AR-07', '42': 'AR-07', '43': 'AR-07', '44': 'AR-07', '45': 'AR-07', '46': 'AR-07', '47': 'AR-07',
}

pref_codes_to_name = {
    '01': '北海道', '02': '青森県', '03': '岩手県', '04': '宮城県', '05': '秋田県', '06': '山形県', '07': '福島県',
    '08': '茨城県', '09': '栃木県', '10': '群馬県', '11': '埼玉県', '12': '千葉県', '13': '東京都', '14': '神奈川県',
    '15': '新潟県', '16': '富山県', '17': '石川県', '18': '福井県', '19': '山梨県', '20': '長野県',
    '21': '岐阜県', '22': '静岡県', '23': '愛知県', '24': '三重県',
    '25': '滋賀県', '26': '京都府', '27': '大阪府', '28': '兵庫県', '29': '奈良県', '30': '和歌山県',
    '31': '鳥取県', '32': '島根県', '33': '岡山県', '34': '広島県', '35': '山口県',
    '36': '徳島県', '37': '香川県', '38': '愛媛県', '39': '高知県',
    '40': '福岡県', '41': '佐賀県', '42': '長崎県', '43': '熊本県', '44': '大分県', '45': '宮崎県', '46': '鹿児島県', '47': '沖縄県',
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

all_values = [
    ["タイムスタンプ", "カテゴリ", "画像", "緯度", "経度", "スポット名", "紹介文", "Instagram", "Twitter", "公式サイト", "Facebook"]
]

total_stores = 0

for p in range(1, 48):
    pref = f"{p:02d}"
    area = pref_to_area.get(pref)
    if not area:
        continue

    pref_name = pref_codes_to_name.get(pref, f"JP-{pref}")
    print(f"\n[{pref_name} (JP-{pref})] 処理開始 ……")

    page = 1
    pref_stores = 0

    while True:
        url = (
            f"https://p.eagate.573.jp/game/facility/search/p/list.html"
            f"?gkey=PLRS&paselif=false&area={area}&pref=JP-{pref}&finder=area&page={page}"
        )

        print(f"  ページ {page} を取得中 → {url}")

        try:
            start_req = time.time()
            resp = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start_req

            if resp.status_code != 200:
                print(f"    → 失敗 (HTTP {resp.status_code})  {elapsed:.2f}秒")
                break

            soup = BeautifulSoup(resp.text, "html.parser")

            result_text = soup.find(string=lambda t: t and "件の店舗が見つかりました" in t)
            if result_text:
                print(f"    → {result_text.strip()}")

            blocs = soup.find_all("div", class_="cl_shop_bloc")
            print(f"    店舗ブロック数: {len(blocs)} 件")

            if not blocs:
                print("    → 店舗データなし。次の都道府県へ")
                break

            for bloc in blocs:
                name = bloc.get("data-name", "").strip()
                address = bloc.get("data-address", "").strip()
                lat = bloc.get("data-latitude", "")
                lng = bloc.get("data-longitude", "")

                if not (name and lat and lng):
                    continue

                a = bloc.select_one("a[href*='detail.html']")
                detail_url = f"https://p.eagate.573.jp{a['href']}" if a else ""

                tweet_text = urllib.parse.quote(f"{address}{name}")
                twitter_url = f"https://twitter.com/intent/tweet?text={tweet_text}"

                row = [
                    "", pref_name, "", lat, lng, name, address, "", twitter_url, detail_url, ""
                ]
                all_values.append(row)

                pref_stores += 1
                total_stores += 1

                print(f"      追加: {name} ({lat}, {lng})")

            next_link = soup.find("a", href=lambda h: h and f"&page={page+1}" in h)
            if not next_link:
                print(f"  → {pref_name} 完了（{pref_stores}件）")
                break

            page += 1
            time.sleep(1.8)  # サーバー負荷軽減

        except Exception as e:
            print(f"  エラー発生: {e}")
            break

        time.sleep(1.2)

print("\n" + "="*60)
print(f"全処理完了！ 総店舗数: {total_stores} 件")
total_elapsed = (datetime.now() - start_time).total_seconds()
minutes = int(total_elapsed // 60)
seconds = int(total_elapsed % 60)
print(f"開始から経過時間: {minutes}分 {seconds}秒 ({total_elapsed:.1f}秒)")
print("JSONファイル保存中...")

output = {
    "range": "スポットデータ",
    "majorDimension": "ROWS",
    "values": all_values
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("→ data.json に保存しました")
print("="*60)
