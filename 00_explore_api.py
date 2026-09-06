import sys
import os

OUTPUT_PATH = r"C:\Users\shio_\medini-dx-tools\output\api_探索結果.txt"

def dump_object(f, name, obj, max_members=200):
    f.write("=== %s ===\n" % name)
    try:
        f.write("type: %s\n" % type(obj))
    except Exception as e:
        f.write("type取得失敗: %s\n" % e)
    try:
        f.write("str: %s\n" % str(obj))
    except Exception as e:
        f.write("str取得失敗: %s\n" % e)
    try:
        members = dir(obj)
        f.write("メンバー数: %d\n" % len(members))
        for m in members[:max_members]:
            f.write("  - %s\n" % m)
        if len(members) > max_members:
            f.write("  ...(以下省略、全部で%d件)\n" % len(members))
    except Exception as e:
        f.write("dir()取得失敗: %s\n" % e)
    f.write("\n")


def main():
    with open(OUTPUT_PATH, "w") as f:
        f.write("medini scripting console API 探索結果\n")
        f.write("Jythonバージョン: %s\n" % sys.version)
        f.write("=" * 60 + "\n\n")

        f.write("--- コンソールのglobals()一覧 ---\n")
        g = globals()
        candidate_names = []
        for key in sorted(g.keys()):
            if key.startswith("__"):
                continue
            f.write("global変数候補: %s = %s\n" % (key, type(g[key])))
            candidate_names.append(key)
        f.write("\n")

        for name in candidate_names:
            dump_object(f, name, g[name])

        for probe_name in ["project", "currentProject", "mediniProject",
                            "session", "workspace", "modelManager",
                            "activeProject", "app", "application"]:
            if probe_name in g:
                continue
            try:
                obj = eval(probe_name)
                dump_object(f, probe_name, obj)
            except Exception:
                pass

    print("探索結果を出力しました: %s" % OUTPUT_PATH)


main()
