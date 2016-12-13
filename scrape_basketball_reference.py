from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
from datetime import timedelta
from time import sleep
import random
import pickle

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

# For each game, get the date, names of both teams, and players for both teams
# Can use this informaiton with the player and team scraped data to generate features
# Example: Game_List_2016 = scrape_game_overview_data(date(2016, 10, 25), date(2016, 12, 7), 2016)
def scrape_game_overview_data(start_date, end_date, year):

	base_url_string = 'http://www.basketball-reference.com/boxscores/'
	date_strings = generate_date_strings(start_date, end_date)

	# List of dictionaries, each one representing a game with keys 'Date', 'Team_1', 'Team_2', 'Team_1_Players', 'Team_2_Players'
	# Each game represents two features, one for each team, and two output values (win/loss or point differential)
		# Might be good to have "other team" feature values as predictor to account for strength of opponent
	game_list = []


	for ds in date_strings:

		ds_year = int(ds[:4])
		ds_month = int(ds[4:6])
		ds_day = int(ds[6:])

		for abbr in team_abbreviations:

			url_to_try = base_url_string + ds + '0' + abbr + '.html'

			try:
				soup = BeautifulSoup(urlopen(url_to_try), 'lxml')
				print("Found game with", abbr, "on " + ds)

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

				# Getting regular stats for team 2
				regular_stats_team_2 = df.iloc[second_empty+2:third_empty]
				# Removing reserves row
				regular_stats_team_2 = regular_stats_team_2.loc[regular_stats_team_2['Starters'] != 'Reserves']
				# Add date column for indexing by player
				regular_stats_team_2['Date'] = date(ds_year, ds_month, ds_day)

				# 1. Handle player stats
				# Append all players stats to our player dataframe
				team_1_players = regular_stats_team_1['Starters'].tolist()[:-1] # ignore 'Team Totals'
				team_2_players = regular_stats_team_2['Starters'].tolist()[:-1]

				# Parse HTML to get the names of the teams
				div = soup.findAll('div', {"class":"box"})
				headline = x = div[0].contents[1].contents[0]
				# Away team is always team 1, listed first
				team_1_name = headline[:(headline.find(' at '))]
				team_2_name = headline[(headline.find(' at ')+4):(headline.find(' Box '))]


				# Construct game summary and attach to list
				game_dictionary = {}
				game_dictionary['Date'] = date(ds_year, ds_month, ds_day)
				game_dictionary['Team_1'] = team_1_name
				game_dictionary['Team_2'] = team_2_name
				game_dictionary['Team_1_Players'] = team_1_players
				game_dictionary['Team_2_Players'] = team_2_players


				game_list.append(game_dictionary)


				sleep(random.uniform(0.1, 0.2))

			except:

				sleep(random.uniform(0.1, 0.2))
				continue

		print(len(game_list))

	print(len(game_list), "Games Processed")

	try:
		# Dump game list file for later loading
		pickle_file_name = 'Game_List_' + str(year) + '.p'
		with open(pickle_file_name, 'wb') as fp:
			pickle.dump(game_list, fp)
	except:
		pass

	return game_list

# Get all player and all team data within a certain range
# Start and end dates must be actual dates: Example: start_date = Date(2016, 10, 28)
# Example:
	# p_2015,s_2015 = populate_player_and_team_data(date(2015, 10, 27), date(2016, 4, 13))
	# Then save both dataframes to csv
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

		ds_year = int(ds[:4])
		ds_month = int(ds[4:6])
		ds_day = int(ds[6:])

		for abbr in team_abbreviations:
		#for abbr in ['LAL', 'NOP', 'SAS']: # For testing with 10/25/2016

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

				# print(advanced_stat_column_headers)
				# print(advanced_stats_team_1)

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


				sleep(random.uniform(0.1, 0.2))

			except:

				sleep(random.uniform(0.1, 0.2))
				continue

		print(len(player_stats), len(team_stats))

	print(game_count, "Games Processed")
	return player_stats, team_stats


