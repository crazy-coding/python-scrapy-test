

class BasketballMixin():


	def change_team_name(self, input_name, season_year=None):
		if season_year:
			if season_year < 2013 and input_name == "New Orleans Pelicans":
				return "Hornets"
			if season_year < 2014 and input_name == "Charlotte Hornets":
				return "Bobcats"

		if input_name in self.team_names:
			return self.team_names[input_name]
		return input_name


	team_names = {
		'Philadelphia 76ers': '76ers' ,
		'Charlotte Bobcats': 'Bobcats',
		'Milwaukee Bucks': 'Bucks',
		'Chicago Bulls': 'Bulls',
		'Cleveland Cavaliers' : 'Cavaliers',
		'Boston Celtics': 'Celtics',
		'Los Angeles Clippers': 'Clippers',
		'Memphis Grizzlies': 'Grizzlies',
		'Atlanta Hawks': 'Hawks',
		'Miami Heat': 'Heat',
		'Charlotte Hornets': 'Hornets',
		'Utah Jazz': 'Jazz',
		'Sacramento Kings': 'Kings',
		'New York Knicks': 'Knicks',
		'Los Angeles Lakers': 'Lakers',
		'Orlando Magic': 'Magic',
		'Dallas Mavericks': 'Mavericks',
		'Brooklyn Nets': 'Nets',
		'Denver Nuggets': 'Nuggets',
		'Indiana Pacers': 'Pacers',
		'New Orleans Pelicans': 'Pelicans',
		'Detroit Pistons': 'Pistons',
		'Toronto Raptors' : 'Raptors',
		'Houston Rockets': 'Rockets',
		'San Antonio Spurs': 'Spurs',
		'Phoenix Suns': 'Suns',
		'Oklahoma City Thunder': 'Thunder',
		'Minnesota Timberwolves': 'Timberwolves',
		'Portland Trail Blazers': 'Trail Blazers',
		'Golden State Warriors': 'Warriors',
		'Washington Wizards': 'Wizards',
	}

