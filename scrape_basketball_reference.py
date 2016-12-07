from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
from datetime import timedelta
from time import sleep


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
def base_scrape_training_data(start_date, end_date):

	base_url_string = 'http://www.basketball-reference.com/boxscores/'

	date_strings = generate_date_strings(start_date, end_date)

	# Generate each possible string with all 30 teams. Teams that don't have a game that day will just be pass over with try, except
	# TODO: Possibly find a cleaner way to do this


	for ds in date_strings:

		for abbr in team_abbreviations:

			url_to_try = base_url_string + ds + '0' + abbr + '.html'

			try:
				soup = BeautifulSoup(urlopen(url_to_try), 'lxml')
				print("Found game with", abbr, "on " + ds)

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

# Start and end dates must be actual dates: Example: start_date = Date(2016, 10, 28)
def populate_player_and_team_data(start_date, end_date):

	base_url_string = 'http://www.basketball-reference.com/boxscores/'

	date_strings = generate_date_strings(start_date, end_date)

	# Generate each possible string with all 30 teams. Teams that don't have a game that day will just be pass over with try, except
	# TODO: Possibly find a cleaner way to do this

	# Mapping from player name to a dataframe with his stats for each game played
	#player_name_to_dataframe = {}

	player_stats = pd.DataFrame()
	team_stats = pd.DataFrame()

	game_count = 0

	for ds in date_strings:

		ds_year = ds[:4]
		ds_month = ds[4:6]
		ds_day = ds[6:]

		for abbr in team_abbreviations:
		# for abbr in ['CLE', 'POR', 'GSW']: # For testing with 10/25/2016

			url_to_try = base_url_string + ds + '0' + abbr + '.html'

			try:
				soup = BeautifulSoup(urlopen(url_to_try), 'lxml')
				print("Found game with", abbr, "on " + ds)
				game_count += 1

				# Get all the data rows from the webpage in bs4.Tag form
				data_rows = soup.findAll('tr')

				# Get the main stat column headers
				main_stat_column_headers = [th.getText() for th in data_rows[1].findAll('th')]


				# Get the advanced stat column headers
				empty_row = None
				for i in range(1,len(data_rows)): # Skip the first empty row because it preceeds main column headers
					#print(data_rows[i].findAll('th')[0].getText())
					player_name = data_rows[i].findAll('th')[0].getText()
				
					if player_name == "":
						empty_row = i
						break

				advanced_column_row = empty_row + 1

				advanced_stat_column_headers = [th.getText() for th in data_rows[advanced_column_row].findAll('th')]				

				# Iterate all the data rows and store the information in player_data
				player_data = [[data_rows[i].findAll('th')[0].getText()] + [td.getText() for td in data_rows[i].findAll('td')] for i in range(len(data_rows))]

				# Ignore first empty row and second row of column values
				player_data = player_data[2:]

				# Turning player data into a dataframe
				df = pd.DataFrame(player_data, columns=main_stat_column_headers)

				# Getting the empty row indices that divide between basic and advanced stats
				first_empty, second_empty, third_empty = df[df['Starters'] == ''].index.tolist()

				# Getting regular stats for the first team
				regular_stats_team_1 = df.iloc[:first_empty]
				# Removing the useless reserves rows
				regular_stats_team_1 = regular_stats_team_1.loc[df['Starters'] != 'Reserves']
				# Add date column for indexing by player
				regular_stats_team_1['Date'] = date(ds_year, ds_month, ds_day)

				# Getting advanced stats for the second team
				advanced_stats_team_1 = df.iloc[first_empty+2:second_empty]

				# Eliminating the reserves row
				advanced_stats_team_1 = advanced_stats_team_1.loc[advanced_stats_team_1['Starters'] != 'Reserves']
				# Drop the last 5 columns that are empty for these advanced stats
				advanced_stats_team_1 = advanced_stats_team_1.iloc[:, :-5]

				# Change the column values
				advanced_stats_team_1.columns = advanced_stat_column_headers


				# Getting regular stats for team 2
				regular_stats_team_2 = df.iloc[second_empty+2:third_empty]
				# Removing reserves row
				regular_stats_team_2 = regular_stats_team_2.loc[regular_stats_team_2['Starters'] != 'Reserves']
				# Add date column for indexing by player
				regular_stats_team_2['Date'] = date(ds_year, ds_month, ds_day)

				# Getting advanced stats for team 2
				advanced_stats_team_2 = df.iloc[third_empty+2:]
				# Eliminating the reserves row
				advanced_stats_team_2 = advanced_stats_team_2.loc[advanced_stats_team_2['Starters'] != 'Reserves']
				# Drop the last 5 columns that are empty for these advanced stats
				advanced_stats_team_2 = advanced_stats_team_2.iloc[:, :-5]
				# Change columns
				advanced_stats_team_2.columns = advanced_stat_column_headers


				# Horizontally concatenating the two stats dataframes for each team
				all_stats_team_1 = regular_stats_team_1.merge(advanced_stats_team_1, left_on='Starters', right_on='Starters', how='inner')
				all_stats_team_2 = regular_stats_team_2.merge(advanced_stats_team_2, left_on='Starters', right_on='Starters', how='inner')


				# Rearrange columns in the two dataframes
				columns = all_stats_team_2.columns.tolist()
				columns.remove('Date')
				columns.remove('Starters')

				all_stats_team_1 = all_stats_team_1[['Starters','Date'] + columns]
				all_stats_team_2 = all_stats_team_2[['Starters','Date'] + columns]


				# Parse HTML to get the names of the teams
				div = soup.findAll('div', {"class":"box"})
				headline = x = div[0].contents[1].contents[0]
				# Away team is always team 1, listed first
				team_1_name = headline[:(headline.find(' at '))]
				team_2_name = headline[(headline.find(' at ')+4):(headline.find(' Box '))]


				# 1. Handle player stats
				# Append all players stats to our player dataframe
				player_stats_team_1 = all_stats_team_1.iloc[:-1]
				player_stats_team_2 = all_stats_team_2.iloc[:-1]

				player_stats = player_stats.append(player_stats_team_1)
				player_stats = player_stats.append(player_stats_team_2)


				# Handle team total stats
				team_1_stats = all_stats_team_1.iloc[-1:]
				team_2_stats = all_stats_team_2.iloc[-1:]
				team_1_stats = team_1_stats.rename(columns={"Starters": "Team Name"})
				team_2_stats = team_2_stats.rename(columns={"Starters": "Team Name"})
				team_1_stats['Team Name'] = team_1_name
				team_2_stats['Team Name'] = team_2_name
				
				team_stats = team_stats.append(team_1_stats)
				team_stats = team_stats.append(team_2_stats)

				sleep(0.5)

			except:

				sleep(0.5)
				continue

	print(game_count, "Games Processed")
	return player_stats, team_stats


# start_date = date(2016, 10, 25)
# end_date = date(2016, 12, 6)
# x = populate_player_dataframes(start_date, end_date)


