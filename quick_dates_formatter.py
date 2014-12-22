import sublime, sublime_plugin
from datetime import datetime


# Date to be shown as example in the formats list
EXAMPLE_DATE = datetime(1970, 12, 31)


class QuickdatesformatterFormatDatesCommand(sublime_plugin.WindowCommand):

	# Needed to find the dates in the chosen format within the text
	date_to_regex = {
		'%d/%m/%Y': r'\d{1,2}/\d{1,2}/\d{4}',
		'%m/%d/%Y': r'\d{1,2}/\d{1,2}/\d{4}',
		'%Y/%m/%d': r'\d{4}/\d{1,2}/\d{1,2}',

		'%d-%m-%Y': r'\d{1,2}-\d{1,2}-\d{4}',
		'%m-%d-%Y': r'\d{1,2}-\d{1,2}-\d{4}',
		'%Y-%m-%d': r'\d{4}-\d{1,2}-\d{1,2}',

		'%d.%m.%Y': r'\d{1,2}\.\d{1,2}\.\d{4}',
		'%m.%d.%Y': r'\d{1,2}\.\d{1,2}\.\d{4}',
		'%Y.%m.%d': r'\d{4}\.\d{1,2}\.\d{1,2}'
	}

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		self.settings = None
		self.formats = None
		self.target_format = None
		self.format = None
		self.dates = [] # dates in current selection as datetime objects
		self.formatted_dates = [] # date strings formatted in the target format

	def format_highlighted(self, index):
		view = self.window.active_view()
		view.sel().clear()

		# If quick panel cancelled, clear current state and return.
		# ( index of -1 means that the quick panel was cancelled )
		if index == -1:
			self.dates = []
			self.formatted_dates = []
			return

		# Get the format and the corresponding regex
		self.format = self.formats[index][0]
		pattern = self.date_to_regex[self.format]

		# Add all found dates to the current selection
		for region in view.find_all(pattern):
			contents = view.substr(view.word(region))
			try:
				# To check if the regex match really fits the chosen format, we try parsing the string
				# Then just add it to the list of dates, not to parse it again later
				date_obj = datetime.strptime(contents, self.format)
				self.dates.append(date_obj)

				# If the string fits the chosen format, then add the region
				view.sel().add(region)
			except ValueError:
				# Nothing to handle here, the string is not in the right format
				pass

	def format_selected(self, index):
		# When format is selected, prompt the user for the desired target format
		self.window.show_input_panel(
			"Target format",
			self.settings.get('target_format'),
			self.target_format_selected,
			self.target_format_change,
			self.target_format_cancelled,
		)

	def target_format_cancelled(self):
		# Clear current selection and formatted_dates list
		self.window.active_view().sel().clear()
		self.dates = []
		self.formatted_dates = []

	def target_format_change(self, fmt):
		pass

	def target_format_selected(self, fmt):
		"""
		Replace selected dates with dates formatted in target format as soon as the target format is input
		"""
		# Run replace_dates TextCommand
		view = self.window.active_view()
		view.run_command('quickdatesformatter_replace_dates', {'formatted_dates':
			[ datetime.strftime(date_obj, self.target_format) for date_obj in self.dates]})

	def run(self, *args, **kwargs):
		self.settings = sublime.load_settings('QuickDatesFormatter.sublime-settings')
		self.formats = self.settings.get('formats')
		self.target_format = self.settings.get('target_format')

		self.window.show_quick_panel(
			[[label, datetime.strftime(EXAMPLE_DATE, fmt)] for fmt, label in self.formats],
			self.format_selected,
			sublime.MONOSPACE_FONT,
			0, # menu item index which is highlighted by default
			self.format_highlighted
		)


class QuickdatesformatterReplaceDatesCommand(sublime_plugin.TextCommand):

	def run(self, edit, formatted_dates=None):
		regions = self.view.sel()
		if formatted_dates and len(formatted_dates) >= len(regions):
			for i in range(len(regions)):
				self.view.replace(edit, regions[i], formatted_dates[i])
