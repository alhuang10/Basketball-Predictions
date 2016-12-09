import pandas as pd
import _pickle as pickle



# Input - a list of dictionaries, each dictionary contains information for a single game, date, players, teams
		# along with the all extracted player and team data by season
# Output - features for each game dictionary, use scraped player and team data
def generate_game_features(game_list, player_data, team_data, classifiaction_problem=True):

	game_features = []
	game_outputs = []

	for game_dictionary in game_list:

		features, outputs = extract_features(game_dictionary, player_data, team_data, classifiaction_problem)

		if features is not None:
			game_features.extend(features)
			game_outputs.extend(outputs)

	assert(len(game_features) == len(game_outputs))

	return game_features, game_outputs


# One possible feature extraction method
# Gets all team total stats, does not account for players at all
def get_only_team_features(date, team_1, team_2, team_1_players, team_2_players, player_data, team_data):

	team_1_data = team_data.loc[(team_data['Team Name'] == team_1) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]
	team_2_data = team_data.loc[(team_data['Team Name'] == team_2) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]

	if len(team_1_data) == 0:
		return None, None

	team_1_data = team_1_data.dropna(axis=1)
	team_2_data = team_2_data.dropna(axis=1)

	
	team_1_values = team_1_data.values[0][2:]
	team_2_values = team_2_data.values[0][2:]

	team_1_features = team_1_values.tolist() + team_2_values.tolist()
	team_2_features = team_2_values.tolist() + team_1_values.tolist()

	# print(date, team_1, team_2)
	# print(team_1_features)
	# print(team_2_features)

	return team_1_features, team_2_features



# Call this for all your games to generate feature vectors for games
# Takes in a game dictionary and returns features for each team using team_data and player_data, previously extracted
# Classification problem determines if for outputs we return 0/1 or the amount that the team won/lost by
def extract_features(game_overview_dict, player_data, team_data, classifiaction_problem):

	# Do a try except because might not have been extractd into player/team data

	feature_vectors = []

	team_1_outcome = None
	team_2_outcome = None


	### Generating the input feature vectors ###

	date = game_overview_dict['Date']
	team_1 = game_overview_dict['Team_1']
	team_2 = game_overview_dict['Team_2']
	team_1_players = game_overview_dict['Team_1_Players']
	team_2_players = game_overview_dict['Team_2_Players']

	team_1_data = team_data.loc[(team_data['Team Name'] == team_1) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]
	team_2_data = team_data.loc[(team_data['Team Name'] == team_2) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]


	### Change this function here to get different feature sets ###
	team_1_features, team_2_features = get_only_team_features(date, team_1, team_2, team_1_players, team_2_players, player_data, team_data)

	if team_1_features is None:
		return None, None

	# Generating the output values corresponding to both generated vectors
	# Either 0/1 for win/loss classification or point spread for spread prediction (which can then be used for win loss also)
	team_1_data = team_data.loc[(team_data['Team Name'] == team_1) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]
	team_2_data = team_data.loc[(team_data['Team Name'] == team_2) & (team_data['Date'] == date.strftime('%Y-%m-%d'))]

	team_1_score = int(team_1_data.iloc[0]['PTS'])
	team_2_score = int(team_2_data.iloc[0]['PTS'])
	
	if classifiaction_problem:
		if team_1_score > team_2_score:
			team_1_outcome = 1
			team_2_outcome = 0
		else:
			team_1_outcome = 0
			team_2_outcome = 1
	else:
		team_1_outcome = team_1_score - team_2_score
		team_2_outcome = (-1) * team_1_outcome

	# print(date, team_1, team_2, team_1_score, team_2_score)
	# print(team_1_features)
	# print(team_2_features)

	return [team_1_features, team_2_features], [team_1_outcome, team_2_outcome]



# Get running averages of team information for every point in the season
### For use when making testing model on validation/test set, which wants to simulate the game not occuring yet, and thus we use season averages up
	### to that point
def get_team_averages(team_season_data, team_name):

	games_for_team = team_season_data.loc[team_season_data['Team Name'] == team_name]

	team_averages = pd.DataFrame()

	for i in range(len(games_for_team)-1, -1, -1):
		current_row = games_for_team.iloc[i]

		if i != 0:
			mean_previous = games_for_team.iloc[:i].mean()
			# Retain this because taking mean of dataframe will eliminate non numbers
			mean_previous['Team Name'] = current_row['Team Name']
			mean_previous['Date'] = current_row['Date']
			#indices = mean_previous.index.tolist()
			# Reordering the columns so in same form
			#indices = indices[-2:] + indices[:-2]
			# mean_previous = mean_previous.reindex(index = indices)
			team_averages = team_averages.append(mean_previous, ignore_index=True)
		else:
			team_averages = team_averages.append(current_row)	

	# Reorder the columns and sort by date
	team_averages = team_averages[games_for_team.columns.tolist()]
	team_averages = team_averages.sort_values(by='Date')

	return team_averages


def load_game_list(pickle_file):

	game_list = None

	with open(pickle_file, 'rb') as fp:
		game_list = pickle.load(fp)

	return game_list


