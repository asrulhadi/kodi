# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
from kodiswift import Plugin


plugin = Plugin()
dTTL = 60*12        # default cache time (in second)
quranicaudio = "https://quranicaudio.com/"


@plugin.cached(ttl=dTTL)
def get_page(url):
    # Download the source HTML for the page using requests
    # and parse the page using BeautifulSoup
    return BeautifulSoup(requests.get(url).text, 'html.parser')


@plugin.cached_route('/qari/<section>/', ttl=dTTL)
def list_qari(section):
    qari = []
    page = get_page(quranicaudio + "section/" + section)
    # format <a class="XXX" href="/quran/1" data-reactid="XXX">Abdullah Awad</a>
    for aa in page.find_all(href=re.compile('/quran/')):
        href = aa['href'][1:]
        path = plugin.url_for('list_surah', link=href, qari=aa.string)
        qari.append({'label': aa.string, 'path': path})
    return qari


@plugin.cached_route('/surah/<qari>/<link>/', ttl=dTTL)
def list_surah(link, qari):
    surah = []
    page = get_page(quranicaudio + link)
    for li in page.find_all('li'):
        # search for download
        a_tag = li.find(href=re.compile('/download'))
        if a_tag is not None:
            # create default name
            nama = "{:03d}".format(len(surah)+1)
            a_href = a_tag['href']
            # search nama surah
            h5 = li.find_all('h5')
            if len(h5) > 2:
                # found. Use it
                nama = "".join([ss.string for ss in h5[1].find_all('span')])
            surah.append({
                'label': nama,
                'path': plugin.url_for('play_surah', url=a_href),
                'icon': 'DefaultAudio.png',
                'is_playable': True,
                'info_type': 'music',
                'info': {
                    'tracknumber': len(surah)+1,
                    'album': 'Al-Quran',
                    'artist': qari,
                    'title': nama,
                    'rating': '5'
                }
            })
    return surah


@plugin.route('/play/<url>')
def play_surah(url):
    plugin.log.info('Playing url: %s' % url)
    plugin.set_resolved_url(url)


@plugin.route('/')
def index():
    '''List category'''
    category = [
        {'label': 'Recitations',
         'path': plugin.url_for('list_qari', section=1)},
        {'label': 'Haramain Taraweeh',
         'path': plugin.url_for('list_qari', section=2)},
        {'label': 'Non-Hafs Recitations',
         'path': plugin.url_for('list_qari', section=3)},
        {'label': 'Recitations with Translations',
         'path': plugin.url_for('list_qari', section=4)}
    ]
    return category


if __name__ == '__main__':
    plugin.run()
