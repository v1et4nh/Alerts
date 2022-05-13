import json
from copy import deepcopy

# Fill with the last numbers of your issues
# e.g. I have issues 1 #5202 and 5648 -> issue_1 = [2, 8]
issue_1 = [2, 8]
issue_2 = [1, 2, 3, 5]
issue_3 = [1, 3, 4, 4, 5]
# Set your favorite category:
fav_cat = 1


# Init
dict_cat = {}
for i in range(1, 11):
    dict_cat[f"Cat {i}"] = {'count': 0, 'combi': '|', 'combi_array': []}

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
                    dict_cat[f"Cat {sum}"]['combi_array'].append([i1, issue_2[i2_1], issue_2[i2_2], issue_3[i3_1], issue_3[i3_2]])

# Calculate favorite categories
dict_fav = {}
if fav_cat:
    for combi in dict_cat[f"Cat {fav_cat}"]['combi_array']:
        i1, i2_1, i2_2, i3_1, i3_2 = combi
        str_combi_dict = f"{i1}-{i2_1}-{i2_2}-{i3_1}-{i3_2}"
        issue_1_new, issue_2_new, issue_3_new = deepcopy(issue_1), deepcopy(issue_2), deepcopy(issue_3)
        issue_1_new.remove(i1)
        issue_2_new.remove(i2_1)
        issue_2_new.remove(i2_2)
        issue_3_new.remove(i3_1)
        issue_3_new.remove(i3_2)

        for i1 in issue_1_new:
            for i2_1 in range(len(issue_2_new)):
                for i2_2 in range(i2_1 + 1, len(issue_2_new)):
                    for i3_1 in range(len(issue_3_new)):
                        for i3_2 in range(i3_1 + 1, len(issue_3_new)):
                            str_combi = f" {i1}-{issue_2_new[i2_1]}-{issue_2_new[i2_2]}-{issue_3_new[i3_1]}-{issue_3_new[i3_2]} |"
                            sum = i1 + issue_2_new[i2_1] + issue_2_new[i2_2] + issue_3_new[i3_1] + issue_3_new[i3_2]
                            sum = int(str(sum)[-1]) + 1
                            try:
                                if dict_fav[str_combi_dict][f"Cat {sum}"]:
                                    pass
                            except:
                                dict_fav[str_combi_dict] = {}
                                dict_fav[str_combi_dict][f"Cat {sum}"] = {'count': 0, 'combi': '|'}
                            dict_fav[str_combi_dict][f"Cat {sum}"]['count'] += 1
                            dict_fav[str_combi_dict][f"Cat {sum}"]['combi'] += str_combi


print('-----')
print(f'Favorite Category: {fav_cat}')
print(json.dumps(dict_fav, sort_keys=False, indent=2))
