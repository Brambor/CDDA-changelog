import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.request import Request, urlopen


pull_url = 'https://github.com/CleverRaven/Cataclysm-DDA/pull/{}'
commit_url = 'https://github.com/CleverRaven/Cataclysm-DDA/commit/{}'
driver = webdriver.Chrome(r'C:\Program Files\chromedriver.exe')  # if that throws error, fix this line


if 'changelog.html' in os.listdir():
	with open('changelog.html', 'r') as changelog:
		last_changes = changelog.readline()
		CDDA_version = last_changes.split('</h2>')[0][4:]
		CDDA_version = int(CDDA_version) + 1
else:
	req = Request('http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/')
	webpage_read = urlopen(req).read().decode("utf-8")
	webpage_read = webpage_read.split('Last build (#')[1].split(')')[0]
	CDDA_version = int(webpage_read)
	with open('changelog.html', 'w') as changelog:
		changelog.write('')

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
	no_pull_commits = set()
	for commit in commit_set:
		url = commit_url.format(commit)

		driver.get(url)
		try:
			pull_number = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.CLASS_NAME, 'pull-request'))
			).text[2:-1]
		except:
			commit_name = driver.find_element_by_class_name('commit-title').text
			no_pull_commits.add((commit, commit_name))
			continue
		pulls.add(pull_number)

	pulls_list = []
	for pull_number in pulls:
		url = pull_url.format(pull_number)
		driver.get(url)
		pull_name = driver.find_element_by_class_name('gh-header-title').text
		pull_name = pull_name.encode('ASCII', 'ignore').decode()  # cause ❤ broke it
		pulls_list.append((pull_number, pull_name))

	pulls_list.sort()

	# make html file(s)
	file_str = '''<h2>{v_current}</h2>'''.format(
		v_current=CDDA_version,
		v_next=CDDA_version+1,
		)

	for pull_number, pull_name in pulls_list:
		file_str += '''<a href='{url}'>{name}<a><br>'''.format(
			url=pull_url.format(pull_number),
			name=pull_name,
		)

	if no_pull_commits:
		file_str += '<h3>Commits:</h3>'
	for commit, commit_name in no_pull_commits:
		file_str += '''<a href='{url}'>{name}<a><br>'''.format(
			url=commit_url.format(commit),
			name=commit_name,
		)

	with open('changelog.html', 'r') as changelog:
		old_changelog = changelog.read()

	file_str += '\n' + old_changelog

	with open('changelog.html', 'w') as changelog:
		changelog.write(file_str)

	if further_version_exists:
		CDDA_version += 1
		first_try = False
	else:
		break

driver.quit()
