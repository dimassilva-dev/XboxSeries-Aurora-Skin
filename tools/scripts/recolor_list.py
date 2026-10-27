import re
# peças de interface e ícones convertidos para o estilo Xbox Series
PAT = re.compile(r'^Images\\(PolarGlass\\|Visuals\\Xui(Button|Checkbox|Slider|RadioButton|Text|ProgressBar|ScrollEnds|RatingBar|DiscIndicator|LinkStatus)\\'
                 r'|Icons\\(FileManager|FileBrowser|DeviceSelector|GameView|GameBrowser|GameAchievements|GameDetails|TitleUpdates|Trainers|QuickView|ProfileSelector|ProfilePanel|Thumbnails|Language|Overscan|RSSFeed|UtilityScripts)\\)')
SKIP = {'Images\\PolarGlass\\HomeChrome.png', 'Images\\PolarGlass\\Ground.png', 'Images\\PolarGlass\\DetailsBackdrop.png'}
# azul de propósito: botão X do controle e o conjunto "Blue" da Visão Rápida
KEEP = re.compile(r'\.X\.|Ring\.X|QV\.Blue')
def targets(names):
    return [n for n in names if n.lower().endswith('.png') and PAT.match(n) and n not in SKIP and not KEEP.search(n)]
