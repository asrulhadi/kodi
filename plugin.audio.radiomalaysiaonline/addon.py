# -*- coding: utf-8 -*-
import re
import xbmc
import requests
from bs4 import BeautifulSoup
from kodiswift import Plugin, ListItem



plugin = Plugin()
#dTTL = 60*60*24        # default cache time (in second)
dTTL = 60*1        # default cache time (in second)
ori_src = "http://www.liveonlineradio.net/malaysia"


@plugin.cached(ttl=dTTL)
def get_page(url):
    # Download the source HTML for the page using requests
    # and parse the page using BeautifulSoup
    return BeautifulSoup(requests.get(url).text, 'html.parser')


def get_radios(page, section):
    radios = []
    # format multiline
    # <a href="http://www.liveonlineradio.net/malaysia/fly-fm-95-8.htm" title="Fly FM 95.8">
    # <div class="catsli" style="display: block;"><div class="catover">
    # <p>Fly FM 95.8</p>
    # </div>
    # <img src="http://www.liveonlineradio.net/wp-content/uploads/2013/09/fly-fm.jpg" alt="Fly FM 95.8" />
    # </div></a>
    for radio in page.find("div", class_=section).find_all("a"):
        href = radio['href']
        nama = radio.find('p').string
        icon = radio.find('img')['src']
        path = plugin.url_for('play_radio', link=href, nama=nama)
        radios.append({
            'label': nama,
            'icon': icon,
            'path': path
        })
    return radios


@plugin.cached_route('/popular', ttl=dTTL)
def list_popular():
    page = get_page(ori_src)
    return get_radios(page, 'box22')


@plugin.cached_route('/page/<section>', ttl=dTTL)
def list_radio(section):
    radios = []
    page = get_page(ori_src + "/page/" + section)

    # get the previous and next page
    nav = page.find('div', class_='navigation')
    cur = nav.find('li', class_='active')
    p = cur.find_previous_sibling()
    if p: radios.append({
        'label': '<< Previous',
        'path': plugin.url_for('list_radio', section=p.string)
    })
    radios += get_radios(page, "widget_categories2a")
    # add next page
    n = cur.find_next_sibling()
    if n: radios.append({
        'label': 'Next >>',
        'path': plugin.url_for('list_radio', section=n.string)
    })
    return radios


@plugin.route('/radio/<nama>/<link>')
def play_radio(link, nama):
    # get the page and parse ...
    page = get_page(link)
    # format
    # <video autoplay="true" controls="false" height="40" name="media" width="303">
    # <source src="http://118.100.116.170:8000/stream" type="audio/mpeg"/></video>
    video = page.find('video')
    # obtain the livestream url
    url = video.source['src']
    # set the information
    station = ListItem(nama, path=url)
    station.set_info('music', { 'title': 'Online %s'%(nama)})
    plugin.log.info('Playing radio: %s' % url)
    xbmc.Player().play(url, station.as_xbmc_listitem(), True)


@plugin.route('/')
def index():
    '''List category'''
    category = [
        {'label': 'Ikim FM',
         'path': plugin.url_for(
             'play_radio',
             link='http://www.liveonlineradio.net/malaysia/ikim-fm.htm',
             nama='Ikim.FM'
         )},
        {'label': 'Popular Malaysia Station',
         'path': plugin.url_for('list_popular')},
        {'label': 'All Malaysia Radio Station',
         'path': plugin.url_for('list_radio', section=1)}
    ]
    return category


if __name__ == '__main__':
    plugin.run()
