import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.request import Request, urlopen


pull_url = 'https://github.com/CleverRaven/Cataclysm-DDA/pull/{}'
driver = webdriver.Chrome(r'C:\Program Files\chromedriver.exe')  # if that throws error, fix this line

CDDA_version = int(os.listdir('pages')[-1][:-5]) + 1
first_try = True
while True:
	url = "http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/{}/".format(CDDA_version)

	req = Request(url)
	try:
		webpage_read = urlopen(req).read().decode("utf-8")
	except:  # except HTTPError throws NameError
		if first_try:
			print('No new CDDA versions to make hmtl out off!')
		break

	if '<a href="/job/Cataclysm-Matrix/{}'.format(CDDA_version+1) in webpage_read:
		further_version_exists = True
	else:
		further_version_exists = False

	print('downloading for ver', CDDA_version)
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
		pull_number = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.CLASS_NAME, 'pull-request'))
		).text[2:-1]
		pulls.add(pull_number)

	pulls_list = []
	for pull_number in pulls:
		url = pull_url.format(pull_number)
		driver.get(url)
		pull_name = driver.find_element_by_class_name('gh-header-title').text
		pulls_list.append((pull_number, pull_name))

	pulls_list.sort()

	# make html file(s)
	file_str = '<h2>{}</h2>'.format(CDDA_version)
	for pull_number, pull_name in pulls_list:
		file_str += '''<a href='{url}'>{name}<a><br>'''.format(
			url=pull_url.format(pull_number),
			name=pull_name,
		)

	file_str += '''<h3><a href='file:///C:/Users/Tonda/Documents/GitHub/CDDA-changelog/pages/{}.html'>&gt&gt{}</a></h3>'''.format(
		CDDA_version+1,
		CDDA_version+1,
		)

	if 'pages' not in os.listdir():
		os.mkdir('pages')

	with open('pages/{}.html'.format(CDDA_version), 'w') as file:
		file.write(file_str)

	if further_version_exists:
		CDDA_version += 1
		first_try = False
	else:
		break

driver.quit()
print('DONE')
