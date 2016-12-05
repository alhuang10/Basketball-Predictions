from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
from datetime import timedelta


print('test')

# Start and end dates must be actual dates: Example: start_date = Date(2016, 10, 28)
def generate_date_strings(start_date, end_date):

	output_day_strings = []

	delta = end_date - start_date

	for i in range(delta.days+1):
		current_date = start_date + timedelta(days=i)
		current_date_string = str(current_date.year) + '{:02d}'.format(current_date.month) + '{:02d}'.format(current_date.day)
		output_day_strings.append(current_date_string)

	return output_day_strings

# The ends of the boxscore URLS
team_abbreviations=['ATL', 
					'BRK', 
					'BOS',
					'CHO',
					'CHI',
					'CLE',
					'DAL',
					'DEN',
					'DET',
					'GSW',
					'HOU',
					'IND',
					'LAC',
					'LAL',
					'MEM',
					'MIA',
					'MIL',
					'MIN',
					'NOP',
					'NYK',
					'OKC',
					'ORL',
					'PHI',
					'PHO',
					'POR',
					'SAC',
					'SAS',
					'TOR',
					'UTA',
					'WAS']

# Start and end dates must be actual dates: Example: start_date = Date(2016, 10, 28)
def scrape_training_data(start_date, end_date):

	base_url_string = 'http://www.basketball-reference.com/boxscores/'

	date_strings = generate_date_strings(start_date, end_date)

	# Generate each possible string with all 30 teams. Teams that don't have a game that day will just be pass over with try, except
	# TODO: Possibly find a cleaner way to do this

	for ds in date_strings:

		for abbr in team_abbreviations:

			url_to_try = base_url_string + ds + '0' + abbr + '.html'

			try:
				soup = BeautifulSoup(urlopen(url_to_try), 'lxml')
				print("Found game with", abbr)

				column_headers = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]
				# Ignore first two rows of descriptors
				data_rows = soup.findAll('tr')[2:]
				# Get name of player then all data
				player_data = [[data_rows[i].findAll('th')[0].getText()] + [td.getText() for td in data_rows[i].findAll('td')] 
								for i in range(len(data_rows))]

				player_df = pd.DataFrame(player_data, columns=column_headers)

				team_totals = player_df[player_df['Starters'] == 'Team Totals']

				### Actual stats for prediction ###
				# Drop advanced stats #
				team_totals_main_stats = team_totals.dropna()
				print(team_totals_main_stats)

				# Getting the teams that played (not sure if necessary)
				div = soup.findAll('div', {"class":"box"})
				headline = x = div[0].contents[1].contents[0]

				away_team = headline[:(headline.find(' at '))]
				home_team = headline[(headline.find(' at ')+4):(headline.find(' Box '))]

				print(away_team, home_team)

			except:
				continue







