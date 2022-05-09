import json

# Fill with the last numbers of your issues
# e.g. I have issues 1 #5202 and 5648 -> issue_1 = [2, 8]
issue_1 = [2, 8]
issue_2 = [1, 2, 3, 5]
issue_3 = [1, 3, 4, 4, 5]


# Init
dict_cat = {}
for i in range(1, 11):
    dict_cat[f"Cat {i}"] = {'count': 0, 'combi': '|'}
counter = 1

for i1 in issue_1:
    for i2_1 in range(len(issue_2)):
        for i2_2 in range(i2_1+1, len(issue_2)):
            for i3_1 in range(len(issue_3)):
                for i3_2 in range(i3_1+1, len(issue_3)):
                    str_combi = f" {i1}-{issue_2[i2_1]}-{issue_2[i2_2]}-{issue_3[i3_1]}-{issue_3[i3_2]} |"
                    sum = i1 + issue_2[i2_1] + issue_2[i2_2] + issue_3[i3_1] + issue_3[i3_2]
                    sum = int(str(sum)[-1]) + 1
                    dict_cat[f"Cat {sum}"]['count'] += 1
                    dict_cat[f"Cat {sum}"]['combi'] += str_combi
                    counter += 1

print(json.dumps(dict_cat, sort_keys=False, indent=2))
