import os

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
lnks = [f for f in os.listdir(desktop) if f.lower().endswith(".lnk")]

new_ok = os.path.exists(os.path.join(desktop, "\u6781\u7b80\u5a92\u4f53\u4e2d\u5fc3.lnk"))
mojibake = [f for f in lnks if f.startswith("\u944b") or "\u6fc7\u63a1" in f]

print("new_shortcut_exists =", new_ok)
print("mojibake_leftover_count =", len(mojibake))
for f in mojibake:
    print("  leftover:", ascii(f))
print("total_lnk_count =", len(lnks))
