"""Baixa capas do XboxUnity (a mesma fonte que o Aurora usa). uso: python covers.py <dir>"""
import json, sys, os, time, subprocess, urllib.parse
GAMES = ['Halo 3', 'Gears of War 2', 'Forza Horizon', 'Red Dead Redemption', 'Mass Effect 2', 'Alan Wake',
         'Skyrim', 'Portal 2', 'Minecraft', 'Fable II', 'Left 4 Dead 2', 'Grand Theft Auto V']
UA = {'User-Agent': 'Mozilla/5.0'}
def get(url):
    # curl usa os certificados do sistema
    return subprocess.run(['curl', '-sfL', '-m', '30', '-A', UA['User-Agent'], url], check=True, capture_output=True).stdout
out = sys.argv[1]; res = []
for name in GAMES:
    q = urllib.parse.quote(name)
    items = json.loads(get('https://xboxunity.net/Resources/Lib/TitleList.php?page=0&count=10&search=%s&sort=3&direction=1&category=0&filter=0' % q))['Items']
    items = [i for i in items if i['TitleType'] == '360' and int(i['Covers'] or 0) > 0]
    exact = [i for i in items if i['Name'].lower() == name.lower()] or items
    if not exact:
        print('sem resultado:', name); continue
    t = exact[0]
    covers = json.loads(get('https://xboxunity.net/Resources/Lib/CoverInfo.php?titleid=' + t['TitleID']))['Covers']
    covers.sort(key=lambda c: (c['Official'] != '1', -(int(c['Rating'] or 0))))
    cid = covers[0]['CoverID']
    data = get('https://xboxunity.net/Resources/Lib/Cover.php?size=large&cid=' + cid)
    fn = os.path.join(out, t['TitleID'] + '.jpg'); open(fn, 'wb').write(data)
    res.append(dict(query=name, name=t['Name'], tid=t['TitleID'], cover=cid, official=covers[0]['Official'], file=fn, bytes=len(data)))
    print(res[-1]); time.sleep(0.5)
json.dump(res, open(os.path.join(out, 'covers.json'), 'w'), indent=1)
