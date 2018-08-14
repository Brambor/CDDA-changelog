from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.request import Request, urlopen

pull_url = 'https://github.com/CleverRaven/Cataclysm-DDA/pull/{}'
driver = webdriver.Chrome(r'C:\Program Files\chromedriver.exe')  # if that throws error, fix this line

## INPUT ##
# from version (including)
range_from = 7697
# to version (including)
range_to = 7697
###########

for CDDA_version in range(range_from, range_to+1):
	url = "http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/{}/".format(CDDA_version)

	req = Request(url)
	webpage_read = urlopen(req).read().decode("utf-8")

	# cut top off
	webpage_read = webpage_read.split('Build #')[1]
	# cut bottom off
	webpage_read = '<tr>'.join(webpage_read.split('<tr>')[:2])
	#get individual commits
	commits = webpage_read.split('commit/')[1:]
	commit_set = set()
	for c in commits:
		commit_set.add(c[:40]) #  unique 40 digit commit hash or smthing

	# follow commits, get pull requests
	pulls = set()
	for commit in commit_set:
		url = 'https://github.com/CleverRaven/Cataclysm-DDA/commit/{}'.format(commit)

		driver.get(url)
		content = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'pull-request'))
		).text[2:-1]
		pulls.add((CDDA_version, content))

	new_pulls = []
	for pull in pulls:
		url = pull_url.format(pull[1])
		driver.get(url)
		pull_name = driver.find_element_by_class_name('gh-header-title').text
		new_pulls.append((pull[0], pull[1], pull_name))

	new_pulls.sort()

	# make html file(s)
	file_str = '<h2>{}</h2>'.format(CDDA_version)
	for pull in new_pulls:
		file_str += '''<a href='{url}'>{name}<a><br>'''.format(
			url=pull_url.format(pull[1]),
			name=pull[2],
		)

	file_str += '''<h3><a href='file:///C:/Users/Tonda/Documents/GitHub/CDDA-changelog/pages/{}.html'>&gt&gt{}</a></h3>'''.format(
		CDDA_version+1,
		CDDA_version+1,
		)

	with open('pages/{}.html'.format(CDDA_version), 'w') as file:
		file.write(file_str)
print('DONE')
