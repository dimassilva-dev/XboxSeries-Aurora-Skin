"""Botões e caixas de texto no padrão da tela de detalhes: grafite chapado, foco branco, cantos de 4 px.
uso: python buttons.py <saida>"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from art2 import _rounded

B = 'Images\\Visuals\\XuiButton\\Aurora.Skin.Controls.'
GRAPHITE = (62, 62, 62, 242)
SPECS = {
    # botão (188x38)
    B + 'Button.Enabled.Blur.png':   ((188, 38), GRAPHITE, None),
    B + 'Button.Disabled.Blur.png':  ((188, 38), (62, 62, 62, 110), None),
    B + 'Button.Enabled.Focus.png':  ((188, 38), (247, 247, 247, 255), None),
    B + 'Button.Enabled.Down.png':   ((188, 38), (205, 205, 205, 255), None),
    B + 'Button.Disabled.Focus.png': ((188, 38), (150, 150, 150, 255), None),
    # caixa de texto (332x52): grafite com borda; foco com borda branca
    B + 'Textbox.Box.Enabled.Blur.png':    ((332, 52), (40, 40, 40, 238), ((95, 95, 95, 255), 1)),
    B + 'Textbox.Box.Disabled.Blur.png':   ((332, 52), (40, 40, 40, 110), ((70, 70, 70, 255), 1)),
    B + 'Textbox.Box.Enabled.Focus.png':   ((332, 52), (40, 40, 40, 242), ((247, 247, 247, 255), 2)),
    B + 'Textbox.Box.Enabled.Down.png':    ((332, 52), (55, 55, 55, 242), ((247, 247, 247, 255), 2)),
    B + 'Textbox.Box.Disabled.Focus.png':  ((332, 52), (40, 40, 40, 110), ((150, 150, 150, 255), 2)),
}


def build(out, names):
    n = 0
    for name, (size, fill, line) in SPECS.items():
        real = [x for x in names if x.endswith(name.split('\\')[-1])]
        for r in real:
            im = _rounded(size, 4, fill, line[0] if line else None, line[1] if line else 1)
            im.save(os.path.join(out, r)); n += 1
    return n


if __name__ == '__main__':
    out = sys.argv[1]
    print(build(out, os.listdir(sys.argv[2])), 'peças')
