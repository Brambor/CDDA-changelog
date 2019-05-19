import os

from datetime import datetime

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.request import Request, urlopen


pull_url = 'https://github.com/CleverRaven/Cataclysm-DDA/pull/{}'
commit_url = 'https://github.com/CleverRaven/Cataclysm-DDA/commit/{}'
driver = Chrome(r'C:\Program Files\chromedriver.exe')  # if that throws error, fix this line


if 'changelog.html' in os.listdir():
	with open('changelog.html', 'r') as changelog:
		last_changes = changelog.readline()
		CDDA_version_first = last_changes.split('</h2>')[0][4:]
		CDDA_version_first = int(CDDA_version_first) + 1
else:
	req = Request('http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/')
	webpage_read = urlopen(req).read().decode("utf-8")
	webpage_read = webpage_read.split('Last build (#')[1].split(')')[0]
	CDDA_version_first = int(webpage_read)
	with open('changelog.html', 'w') as changelog:
		changelog.write('')

# find the lastBuild
req = Request('http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/lastBuild/')
try:
	webpage_read = urlopen(req).read().decode("utf-8")
	CDDA_version_max = int(webpage_read.split("</title>")[0].split("#")[-1].split()[0])
except:
	input("Something in lastBuild fcked up!")
	raise

started_at = datetime.now()

print("now it is %s" % started_at)
print("newest ver = %d" % CDDA_version_max)

first_try = True
CDDA_version = CDDA_version_first
# keep fetching until we get to CDDA_version_max. TODO: before ending, check again (if we had very long fetching)
while CDDA_version <= CDDA_version_max:
	url = "http://gorgon.narc.ro:8080/job/Cataclysm-Matrix/{}/".format(CDDA_version)

	req = Request(url)
	try:
		webpage_read = urlopen(req).read().decode("utf-8")
	except:  # except HTTPError throws NameError
		if CDDA_version <= CDDA_version_max:
			print("\t%d doesn't exist" % CDDA_version)
			CDDA_version += 1
			continue
		if first_try:
			print('No new CDDA versions to make hmtl out off!')
		break

	at_progress = (CDDA_version-CDDA_version_first)/(CDDA_version_max-CDDA_version_first)
	since_start = datetime.now() - started_at
	if CDDA_version != CDDA_version_first:
		time_left = (1-at_progress) * at_progress**-1 * since_start
		time_complete = datetime.now() + time_left
	else:
		time_left = "?.0"
		time_complete = "?.0"
	print('downloading for ver %d (%d%%, time left: %s, ETC: %s)' % (
		CDDA_version,
		int(at_progress*100),  # percentage
		str(time_left).split(".")[0],
		str(time_complete).split(".")[0],
	))
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
			pull_number = WebDriverWait(driver, 3).until(
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

	CDDA_version += 1
	first_try = False

driver.quit()
