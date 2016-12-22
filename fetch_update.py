__author__ = 'alrifqi'
import requests
import json
import unicodedata
from datetime import datetime
import sqlite3
import os

def get_total_update():
    res = requests.get(
        "http://km.support.apple.com/kb/index?page=downloads_browse&offset=1&sort=recency&facet=all&category=PF6"
        "&locale=en_US&callback=ACDownloadSearch.showResults",
        verify=False).text
    res = res.replace('\t', '')
    res = res.replace('\n', '')
    res = res.replace('ACDownloadSearch.showResults(', '')
    res = res.replace(');', '')
    res = res.encode('ascii', 'ignore')
    a = json.loads(res)
    total = a['totalresults']
    total = int(total)/9
    return total

def get_update():
    total = get_total_update()
    dbfile = os.path.join('./database', 'osxupdate.db')
    conn = sqlite3.connect(dbfile, check_same_thread=False)
    conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
    c = conn.cursor()
    datas = []
    for x in range(total, 0, -1):
        data = {}
        res = requests.get(
            "http://km.support.apple.com/kb/index?page=downloads_browse&offset="+str(x)+"&sort=recency&facet=all&category=PF6"
            "&locale=en_US&callback=ACDownloadSearch.showResults",
            verify=False)
        if res.status_code==200:
            res = res.text
            res = res.replace('\t','')
            res = res.replace('\n','')
            res = res.replace('ACDownloadSearch.showResults(','')
            res = res.replace(');','')
            res = res.encode('ascii','ignore')
            res = res.replace("\\'","")
            a = json.loads(res)
            for b in a['downloads']:
                date_object = datetime.strptime(b['lastmodified'], '%b %d, %Y').strftime('%Y%m%d')
                date_release = datetime.strptime(b['lastmodified'], '%b %d, %Y').strftime("%Y-%m-%d")
                url_info = 'https://support.apple.com'+b['url']
                c.execute("INSERT INTO listupdate(name, release_date, url_info, id_update, value_date, description) VALUES(?,?,?,?,?,?)",
                          [b['title'],date_release, url_info, b['id'], date_object, b['description']])
            conn.commit()

def get_update_info():
    import os
    import plistlib
    import datetime
    import biplist
    inst = os.path.join('/Library', 'Receipts', 'InstallHistory.plist')
    install_date = ''
    try:
        if os.path.exists(inst):
            content = plistlib.readPlist(inst)
            for a in content:
                if 'processName' in a:
                    if a['processName'] == 'OS X Installer':
                        install_date = a['date'].strftime('%Y%m%d')
                else:
                    continue
    except Exception as err:
        print err

    try:
        f = os.path.join('/Library', 'Preferences', 'com.apple.SoftwareUpdate.plist')
        content = biplist.readPlist(f)
        update_time = content['LastSuccessfulDate']
        last = update_time.strftime('%Y%m%d')
    except Exception as err:
        print err

    dbfile = os.path.join('./database', 'osxupdate.db')
    conn = sqlite3.connect(dbfile, check_same_thread=False)
    conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
    c = conn.cursor()

    c.execute("SELECT * FROM listupdate WHERE release_date BETWEEN :install AND :last ", {'install': install_date, 'last': last})
    res = c.fetchall()
    datas = []
    for a in res:
        data = {}
        data['title'] = a[1]
        data['hotfixid'] = a[3]
        data['type'] = 'N/A'
        data['caption'] = a[1]
        data['update_date'] = a[5]
        data['installed'] = True
        datas.append(data)
    return datas

if __name__ == '__main__':
    get_update()