from kivymd.app import MDApp
from pytube import YouTube
from pytube.cli import on_progress
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.lang import Builder
from kivymd.uix.card import MDCard
from kivymd.toast import toast
from kivy.uix.widget import Widget
from kivymd.utils.fitimage import FitImage
from kivy.uix.button import ButtonBehavior
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.button import MDFlatButton
from kivymd.uix.list import OneLineListItem
from kivy.clock import Clock
from functools import partial
from threading import Thread
import os
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
from kivy.utils import platform

if platform=='android':
	from android.permissions import request_permissions, Permission, check_permission
	from android.storage import primary_external_storage_path
	primary_ext_storage = primary_external_storage_path() + "/Download"
else:
	primary_ext_storage = os.getcwd() + "/Download"


DEVELOPER_KEY = "AIzaSyDaZ0oX5UwgiLPmY6cMLwiCiLnX_FIHDfo"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search(q, max_results=1,order="relevance", token=None, location=None, location_radius=None):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)
  search_response = youtube.search().list(
    q=q,
    type="video",
    pageToken=token,
    order = order,
    part="id,snippet",
    maxResults=max_results,
    location=location,
    locationRadius=location_radius

  ).execute()



  videos = []

  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append(search_result)
  try:
      nexttok = search_response["nextPageToken"]
      return videos
  except Exception as e:
      nexttok = "last_page"
      return videos

class MyImage(ButtonBehavior, FitImage): pass

class SearchResultBox(MDCard):
	def __init__(self, url, title, channel, _uid,  **kwargs):
		super().__init__(**kwargs)
		self.tnailUrl = url
		self.vTitle = title
		self.cName = channel
		self.vidid = _uid

class HomeScreen(Screen): pass

class YtDownloader(MDApp):

	def build(self):
		if platform=='android':
			while not check_permission('android.permission.WRITE_EXTERNAL_STORAGE'):
				request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
		self.theme_cls.primary_palette = "Red"
		master = Builder.load_file('main.kv')
		return master

	def populate(self, query):
		self.root.ids.home_screen.ids.spinner.active = True
		Clock.schedule_once(partial(self._populate, query), 1)
		
	def _populate(self, query, dt):
		self.root.ids.home_screen.ids.results.clear_widgets()
		results = youtube_search(q=query, max_results=10)
		for a in results:
			card = SearchResultBox(a['snippet']['thumbnails']['high']['url'], a['snippet']['title'], a['snippet']['channelTitle'], a['id']['videoId'])
			self.root.ids.home_screen.ids.results.add_widget(card)
		self.root.ids.home_screen.ids.results.add_widget(Widget(height=100))
		self.root.ids.home_screen.ids.spinner.active = False

	def download(self, uid):
		bmp3 = MDFlatButton(text='mp3', on_release = lambda x: self._download(uid, "mp3"))
		b144p = MDFlatButton(text='144p', on_release = lambda x: self._download(uid, "144p"))
		b360p = MDFlatButton(text='360p', on_release = lambda x: self._download(uid, "360p"))
		b480p = MDFlatButton(text='480p', on_release = lambda x: self._download(uid, "480p"))
		b720p = MDFlatButton(text='720p', on_release = lambda x: self._download(uid, "720p"))
		b240p = MDFlatButton(text='240p', on_release = lambda x: self._download(uid, "240p"))
		Buttons = [bmp3, b144p,b240p, b360p, b480p, b720p]
		self.dialog = MDDialog(title = "Select Quality", size_hint=(0.95,1),buttons = Buttons)
		self.dialog.open()

	def _download(self, uid, qual):
		down_thread = Thread(target=self.down, args=(uid,qual), daemon=True) 
		down_thread.start()
		toast("Downloading")
		self.root.ids.home_screen.ids.toolbar.title = 'YT Downloader (..Downloading)'
		self.root.ids.home_screen.ids.box.ids.progress.start()

	def down(self, uid, qual):
		self.dialog.dismiss()
		url = 'https://www.youtube.com/watch?v='
		try:
			if qual=='mp3':
				vid = YouTube(url+uid)
				toast(f"Downloading {int(vid.streams.filter(only_audio=True,file_extension='webm').first().filesize)//1024000}MB ")
				vid.streams.filter(only_audio=True,file_extension='webm').first().download(primary_ext_storage)
			else:
				vid = YouTube(url+uid,on_progress_callback = on_progress)
				toast(f"Downloading {int(vid.streams.filter(progressive=True,res=qual).first().filesize)//1024000}MB ")
				vid.streams.filter(progressive=True,res=qual).first().download(primary_ext_storage)
			toast(f"{vid.title} downloaded")
		except Exception as e:
			toast(str(e))
		self.root.ids.home_screen.ids.toolbar.title = 'YT Downloader'
		self.root.ids.home_screen.ids.box.ids.progress.stop()

YtDownloader().run()