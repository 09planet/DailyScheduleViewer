#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本日の予定表示スクリプト（macOS Calendar.app から直接読み取り）

- Calendar.app に表示されている全カレンダーが対象（Google同期の「メモ」等も含む）
- OAuth / APIキー 不要
- 必要パッケージ:  pip3 install pyobjc-framework-EventKit
- 初回実行時に macOS が「カレンダーへのアクセス」を確認するので許可してください
"""

import sys
import time
import threading
import subprocess
from datetime import datetime, timedelta

try:
    from Foundation import NSDate, NSRunLoop, NSDefaultRunLoopMode
    from EventKit import EKEventStore, EKEntityTypeEvent
except ImportError:
    sys.exit(
        "EventKit が見つかりません。次を実行してください:\n"
        "    pip3 install pyobjc-framework-EventKit"
    )

GREETING = "おはようございます"
HEADER = "【本日の予定】"
NO_EVENTS_LINE = "・本日の予定はありません"
SHOW_TIME = True  # True にすると各予定の先頭に開始時刻を付ける


def request_access(store):
    """カレンダーへのアクセス許可を同期的に取得する。"""
    done = threading.Event()
    result = {"granted": False}

    def handler(granted, error):
        result["granted"] = bool(granted)
        done.set()

    # macOS 14+ は FullAccess 系、それ以前は従来API
    if store.respondsToSelector_("requestFullAccessToEventsWithCompletion:"):
        store.requestFullAccessToEventsWithCompletion_(handler)
    else:
        store.requestAccessToEntityType_completion_(EKEntityTypeEvent, handler)

    deadline = time.time() + 20
    while not done.is_set() and time.time() < deadline:
        NSRunLoop.currentRunLoop().runMode_beforeDate_(
            NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.05)
        )
    return result["granted"]


def to_nsdate(dt):
    return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())


def fetch_today_events(store):
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    calendars = store.calendarsForEntityType_(EKEntityTypeEvent)
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        to_nsdate(start), to_nsdate(end), calendars
    )
    events = list(store.eventsMatchingPredicate_(predicate) or [])
    events.sort(key=lambda e: e.startDate().timeIntervalSince1970())
    return events


def format_line(event):
    title = (event.title() or "（無題）").strip()
    if SHOW_TIME and not event.isAllDay():
        ts = event.startDate().timeIntervalSince1970()
        return f"・{datetime.fromtimestamp(ts):%H:%M} {title}"
    return f"・{title}"


def main():
    store = EKEventStore.alloc().init()
    if not request_access(store):
        sys.exit("カレンダーへのアクセスが許可されていません。"
                 "「システム設定 > プライバシーとセキュリティ > カレンダー」で許可してください。")

    events = fetch_today_events(store)

    # 同一カレンダーが重複表示されるケースを軽く除去（タイトル+開始時刻で判定）
    seen = set()
    lines = []
    for e in events:
        key = (e.title(), round(e.startDate().timeIntervalSince1970()))
        if key in seen:
            continue
        seen.add(key)
        lines.append(format_line(e))

    output = GREETING + "\n\n" + HEADER + "\n"
    output += "\n".join(lines) if lines else NO_EVENTS_LINE

    print(output)
    subprocess.run("pbcopy", input=output.encode(), check=True)


if __name__ == "__main__":
    main()
