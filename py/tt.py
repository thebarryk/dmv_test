import sys
l = sys.argv[1:]
print()
for x in l[:-1]: print(f"\"{x}\"", end=",")
print(f"\"{x}\"")
