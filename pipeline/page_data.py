from __future__ import print_function
from __future__ import division
import os
import wikipedia
from argparse import ArgumentParser as AP

def _get_basic(pid, full_path):
    details_dict = {}
    with open(full_path, 'r') as f:
        for line in f:
            vals = line.split('\t')
            if vals[0] == pid:
                break
    details_dict['name'] = vals[1]
    details_dict['birth'] = vals[3]
    details_dict['death'] = vals[4][:-1]  # newline character is present
    details_dict['gender'] = vals[2]
    return details_dict

def _get_categories(pid, full_path):
    categories = []
    with open(full_path, 'r') as f:
        for line in f:
            people = line.split('\t')
            people = people[:-1]
            if pid in people:
                categories.append(people[1])
    return categories

p = AP()
p.add_argument('--root', type=str, default='./', help='Specify root location for storing data')
p.add_argument('--communities', type=str, required=True,
               help='Specify location for community data. Expected structure: <comm_id> \\t [person_id]+')
p.add_argument('--basic_info', type=str, default='./wsn_person-name-gender-birth-death.txt',
               help='File for obtaining the basic information')
p.add_argument('--category_info', type=str, default='./wsn_category-person.txt',
               help='File for obtaining the categories')
p.add_argument('--max_files_per_comm', type=int, default=-1,
               help='Maximum files to extract per community. -1 for all')
p = p.parse_args()

basic_info = p.basic_info
category_info = p.category_info

new_dir = os.path.join(p.root, './raw_data')
if not os.path.exists(new_dir):
    os.mkdir(new_dir, mode=0o755)

with open(p.communities, 'r') as all_comms:
    for community in all_comms:
        ids = community.split('\t')
        personids = ids[1:]
        personids[-1] = personids[-1][:-1]
        community_path = os.path.join(new_dir, 'community{}'.format(ids[0]))
        if not os.path.exists(community_path):
            os.mkdir(community_path)
        print(personids)
        dis_probs = []

        if p.max_files_per_comm == -1:
            number_required = len(personids)
        else:
            number_required = p.max_files_per_comm
        flag = False

        for pid in personids:
            details_dict = _get_basic(pid, basic_info)
            name = details_dict['name']
            if pid.find('WP') != -1:
                continue
            person_pagetext = os.path.join(community_path, '{}.txt'.format(pid))
            if os.path.exists(person_pagetext):
                number_required -= 1
                continue
            try:
                person_page = wikipedia.page(name)
                if person_page.title == name:
                    with open(person_pagetext, 'w') as pp:
                        pp.write(person_page.content)
                    number_required -= 1
                else:
                    dis_probs.append((pid, name))
            except:
                dis_probs.append((pid, name))

            if number_required == 0:
                flag = True
                break

        if flag:
            continue

        for pid, name in dis_probs:
            details_dict = _get_basic(pid, basic_info)
            categories = _get_categories(pid, category_info)
            candidates = wikipedia.search(name)
            candidates = [c for c in candidates if c.find(name) != -1]
            best_intersection = 0
            index = -1
            for i, c in enumerate(candidates):
                try:
                    cur_page = wikipedia.page(c)
                    # Extract categories and check the intersection
                    length_of_intersect = len(set(cur_page.categories) & set(categories))
                    if best_intersection < length_of_intersect:
                        best_intersection = length_of_intersect
                        index = i
                except:
                    pass

            if index != -1:
                person_pagetext = os.path.join(community_path, '{}.txt'.format(pid))
                with open(person_pagetext, 'w') as pp:
                    pp.write(wikipedia.page(candidates[index]).content)
                number_required -= 1

            if number_required == 0:
                break
