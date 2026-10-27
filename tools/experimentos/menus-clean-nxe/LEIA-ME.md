# Xbox Series + menus da Clean NXE (em teste)

`XboxSeries-NXE.xzp` junta a Home da Xbox Series com as telas internas da **Clean NXE 2.0.1 (Jayshai)**.

- Da Xbox Series: tela inicial e detalhes (`Aurora_Main.xur`), abertura, shader e texturas das capas,
  modelos visuais da Home (disco, perfil, notificação, botões A/Y, ícones do controle), fontes Inter, `skin.meta`.
- Da Clean NXE: todas as outras telas (Configurações, Exibir, Arquivos, Visão Rápida, opções do jogo...),
  as peças e as fontes Segoe.
- Textos das telas da NXE traduzidos para pt-BR (só propriedades Text; nomes e exemplos ficam como estão).

No console fica como uma skin separada: **Xbox Series NXE**. A estável continua sendo `XboxSeries.xzp`.

## Gerar de novo

```
python3 tools/scripts/merge_nxe.py <CleanNXE.xzp> Aurora/Skins/XboxSeries.xzp saida.xzp
```
`tools/scripts/xur5.py` é o leitor/gravador de `.xur` (regrava as 117 telas das três skins idênticas byte a byte).
As definições de classe vêm do XUIHelper (SGCSam) em `tools/scripts/xur5classes/`; as do Aurora
(`zz_Aurora.xml`) foram deduzidas dos bytes.
