import json
import sys
from datetime import datetime, timezone


def week_title(now):
    year, week, _ = now.isocalendar()
    return f"This week: {year}-W{week:02d}"


def find_open_week_issue(issues, title):
    for issue in issues:
        if issue["title"] == title and issue["state"].upper() == "OPEN":
            return issue["number"]
    return None


def main(argv):
    if argv[:1] == ["title"]:
        print(week_title(datetime.now(timezone.utc)))
        return 0
    if len(argv) == 2 and argv[0] == "find":
        number = find_open_week_issue(json.load(sys.stdin), argv[1])
        if number is not None:
            print(number)
        return 0
    print('usage: week title | week find "<title>"', file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
