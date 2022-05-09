import yaml

# Jeweils die letzte Zahl in den Array eintragen
issue_1 = [2, 8]
issue_2 = [1, 2, 3, 5]
issue_3 = [1, 3, 4, 4, 5]


# Init
dict_cat = {}
for i in range(1, 11):
    dict_cat[i] = 0
counter = 1

for i1 in issue_1:
    for i2_1 in range(len(issue_2)):
        for i2_2 in range(i2_1+1, len(issue_2)):
            for i3_1 in range(len(issue_3)):
                for i3_2 in range(i3_1+1, len(issue_3)):
                    print(f"Combination no. {counter}:\n"
                          f"{i1} - {issue_2[i2_1]} - {issue_2[i2_2]} - {issue_3[i3_1]} - {issue_3[i3_2]}")
                    sum = i1 + issue_2[i2_1] + issue_2[i2_2] + issue_3[i3_1] + issue_3[i3_2]
                    sum = int(str(sum)[-1]) + 1
                    dict_cat[sum] += 1
                    print(f"Kategorie: {sum}")
                    counter += 1

print("-----")
print(yaml.dump(dict_cat, sort_keys=False, default_flow_style=False))
