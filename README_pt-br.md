# UOFiddlerPy 🗡️

> 🌐 **Language / Idioma**: **Português (Brasil)** | [English (README.md)](README.md)  
> 👤 **Autor**: Mauricio Nunes + Gemini  
> 🔗 **GitHub**: [https://github.com/mbnunes/UOFiddlerPy](https://github.com/mbnunes/UOFiddlerPy)

**UOFiddlerPy** é uma recriação completa, nativa e de alta performance em **Python 3** do clássico **UOFiddler** para Ultima Online. Ele foi concebido para rodar de forma suave, estável e elegante em **qualquer distribuição Linux** (Ubuntu, Debian, Fedora, Arch, openSUSE, etc.) e outros sistemas operacionais, eliminando completamente qualquer dependência do **.NET runtime**, **Mono** ou **Wine**.

---

## 💡 Por que o UOFiddlerPy foi criado?

Usar a versão original em C#/.NET no Linux através de Wine ou do Mono frequentemente resulta em:
- Falhas de renderização, travamentos de fontes e vazamentos de memória (GDI+ / WinForms).
- Incompatibilidade de caminhos devido ao sistema de arquivos do Linux (*ext4, btrfs, xfs*) ser sensível a maiúsculas e minúsculas (*case-sensitive*), enquanto os clientes de Ultima Online misturam extensões e nomes (`Art.mul`, `artidx.mul`, `ARTLegacyMUL.uop`).
- Complicações na configuração de prefixes do Wine e dependências pesadas do .NET Desktop Runtime.

O **UOFiddlerPy** resolve tudo isso:
1. **100% Nativo em Python 3 + PyQt6**: Usa as bibliotecas nativas do sistema com renderização acelerada.
2. **Resolução de Arquivos Case-Insensitive**: O `FileManager` indexa e localiza os arquivos do cliente independentemente de estarem em maiúsculas ou minúsculas.
3. **Auto-Detecção Inteligente**: Encontra automaticamente instalações existentes de Ultima Online (inclusive em `/opt/hd_jogos/`, `~/.wine/`, Lutris, diretório atual e pastas de usuário).
4. **Performance 60 FPS com Virtualização**: Navegação ultra rápida em tabelas com mais de **65.536 itens** e **16.384 terrenos** utilizando o padrão *Model-View* sob demanda sem sobrecarregar a memória RAM.
5. **Tema Escuro Moderno (Dark Theme)**: Interface gráfica limpa, estilizada e com alto contraste, pronta para uso prolongado.
6. **Áudio Nativo sem Servidor Windows**: Reprodução direta de arquivos de som através das interfaces de áudio padrão do Linux (`PipeWire`, `PulseAudio`, `ALSA`).
7. **Arquitetura Híbrida (Splash Screen + Lazy Loading)**: Splash screen escura e veloz no startup com barra de progresso em tempo real (~1s), combinada com carregamento sob demanda (*Lazy Loading*) com indicador de progresso na primeira vez que cada aba é aberta, mantendo o consumo de memória ultrabaixo e o app sempre ágil.

---

## 📑 Detalhamento Completo das 17 Abas

### 1. ⚔️ Items (Statics)
- **Visualização em Grid (Padrão) e Lista**: Navegação em grade de miniaturas (`⊞ Grid`) com rótulos hexadecimais ou visualização detalhada em tabela (`☰ List`).
- **Navegação Virtualizada**: Acesso instantâneo a todos os 65.536 IDs de itens estáticos a 60 FPS sem congelamento de memória.
- **Busca Rápida**: Filtre por ID em decimal, hexadecimal (`0x0EED`) ou pelo nome do item em ambos os modos.
- **Canvas Interativo**: Suporte completo a zoom com a roda do mouse, arrasto (pan) e fundo quadriculado de transparência.
- **Testador de Hues**: Selecione e visualize qualquer uma das 3.000 matizes aplicadas diretamente sobre o item (incluindo tratamento de itens com flag `PartialHue`).
- **Inspetor de TileData**: Visualize nome, flags, peso, camada/qualidade, altura e animação associada.
- **🔗 Worn Equipment & Gump Linker**:
  - Resolução automática de **Item ID ➔ Gump ID de Paperdoll** para armaduras, roupas, armas e capas.
  - Seletor de Raça/Corpo: Humanos (400/401), Elfos (605/606) e Gárgulas (666/667).
  - Consulta automática da tabela `Equipconv` e regras de gênero (offset feminino +10000).
  - Botões diretos **"View Male Gump"** e **"View Female Gump"** com navegação instantânea para a aba Gumps!
- **Operações**: Exportação de imagens para PNG/BMP, substituição de arte por imagem externa e remoção.

### 2. 🌿 Land Tiles (Terrenos)
- **Visualização em Grid (Padrão) e Lista**: Alternância fluida entre grade de diamantes isométricos e tabela detalhada.
- **Geometria 44x44 Losango**: Decodificação exata do formato isométrico clássico de terrenos em 16-bit RGB 555.
- **Navegação e Busca**: Filtro de todos os 16.384 terrenos por ID ou nome.
- **Propriedades**: Exibição das flags de terreno (Impassable, Surface, Bridge, Wet, etc.) e Texture ID.
- **Exportação e Substituição**: Importe novas texturas PNG/BMP mantendo o padrão isométrico do jogo.

### 3. 📋 TileData
- **Visualização em Grid (Padrão) e Lista**: Escolha entre grade gráfica de miniaturas ou tabela com dados técnicos completos.
- **Editor Completo de Flags**: Suporte para o padrão clássico (32-bit flags) e o formato moderno **High Seas (64-bit flags)**.
- **Alternância de Modos**: Edição individualizada para `ItemData` e `LandData`.
- **Checkboxes para Todas as Flags**:
  - `Background`, `Weapon`, `Transparent`, `Translucent`, `Wall`, `Damaging`, `Impassable`, `Wet`, `Surface`, `Bridge`, `Generic`, `Window`, `NoShoot`, `PrefixA`, `PrefixAn`, `Internal`, `Foliage`, `PartialHue`, `Map`, `Container`, `Wearable`, `LightSource`, `Animated`, `NoDiagonal`, `Armor`, `Roof`, `Door`, `StairBack`, `StairRight`, `AlphaBlend`, `UseNewArt`, `ArtUsed`, `NoHouse`, `NoDraw`, `HoverOver`.
- **Edição de Campos**: Nome (até 20 caracteres), peso, camada/qualidade, altura, ID de animação, matiz e textura de terreno.
- **Salvamento Direto**: Gravação estruturada e compatível diretamente em `tiledata.mul`.

### 4. 🖼️ Gumps
- **Suporte Duplo Dual-Client**: Combobox integrado para alternar entre **Classic (2D)** e **Enhanced (3D)** em tempo real.
- **Suporte a UOP e MUL**: Lê `gumpart.mul` / `gumpidx.mul` e pacotes Mythic modernos `gumpartLegacyMUL.uop`.
- **📦 Container Bounding Box Overlay**:
  - Detecção automática de contêineres a partir de `data/gamedata/legacycontainers.csv` do `GameData.uop`.
  - Exibe dimensões exatas de área útil (`left, top, right, bottom, width, height`).
  - Desenho semi-transparente em tempo real da área de drop válida (com toggle para ativar/desativar).
- **Descompressão Completa**: Implementação de pipeline duplo (Zlib + descompressor de blocos Mythic).
- **Canvas com Zoom**: Visualização de janelas de interface grandes (como menus de 640x480) ou pequenos botões e ícones.
- **Exportação e Importação**: Salve gumps em PNG transparente ou importe novas artes.

### 5. 🎨 Hues
- **Visualização em Grid (Padrão) com Amostra de Cor**: Em modo Grid, cada célula exibe um quadrado preenchido com a cor representativa da matiz (tom central da paleta) com seu ID numérico.
- **Modo Lista Alternativo**: Tabela com ID, código hexadecimal, nome e amostra da cor.
- **3.000 Matizes Carregadas**: 375 grupos com 8 matizes cada, exatamente como em `hues.mul`.
- **Barra de Paleta com 32 Cores**: Exibição gráfica e clicável de todos os 32 tons que formam a escala do hue.
- **Seletor de Cores (Color Picker)**: Altere qualquer uma das 32 cores individualmente através do seletor nativo.
- **Testador ao Vivo**: Campo para escolher qualquer item do jogo e testar o efeito da tintura em tempo real.
- **Edição de Nomes e Gravação**: Renomeie qualquer matiz e salve as alterações em `hues.mul`.

### 6. 🧱 Textures
- **Seletor Multi-Cliente Integrado**: Alterne instantaneamente entre **Classic (2D MUL)**, **Enhanced Legacy (UOP)** e **Enhanced 3D (UOP)**.
- **Suporte a Texturas DDS do Cliente 3D**: Leitura nativa de **mais de 52.940 texturas DDS** de `LegacyTexture.uop` e **9.790 texturas modernas** de `Texture.uop`!
- **Visualização em Grid (Padrão) e Lista**: Navegação visual rápida por miniaturas de texturas ou tabela com dimensões exatas (64x64, 64x128, 128x128, etc.).
- **Texturas Clássicas e Modernas**: Suporte a formatos clássicos 16-bit RGB 555 e arquivos DirectX DDS (DXT1/DXT5).
- **Conversão de Cores**: Decodificação precisa de 16-bit RGB 555 e compressões DXT para RGBA de 32-bit.
- **Importação e Exportação**: Extraia texturas para edição no Photoshop/GIMP ou importe arquivos PNG para o cliente.

### 7. 🛰️ RadarCol (Cores de Radar/Minimapa)
- **Visualização em Grid (Padrão) e Lista**: Exibição em grade com miniatura da arte do item/terreno acompanhada do indicador da cor de radar no canto (ou amostra sólida da cor).
- **Tabela Completa de Cores**: Mapeamento de cor em 16 bits para cada terreno (0x0000..0x3FFF) e item estático (0x4000..0x13FFF).
- **Gerador Automático de Cores**: Botão inteligente que calcula a cor média representativa do item/terreno (desconsiderando pixels transparentes) e preenche a cor do radar automaticamente!
- **Seletor de Cores e Salvamento**: Ajuste fino com color picker e gravação em `radarcol.mul`.

### 8. 🐉 Animations (Criaturas, Personagens e Equipamentos)
- **Mais de 1.320 Corpos Suportados**: Catálogo completo integrando `Animationlist.xml` e `mobtypes.txt` com nomes reais e categorias (Monstros, Animais, Criaturas Marinhas, Humanos e Equipamentos).
- **Suporte Nativo a UOP Moderno**: Decodificação completa de pacotes `AnimationFrame1.uop` até `AnimationFrame6.uop` com hashes Jenkins `lookup3` de 64 bits (incluindo todas as criaturas modernas de Stygian Abyss, Time of Legends e High Seas como Gargoyles, Abyssal Infernals, etc.).
- **Tabela de Substituições de Sequência**: Leitura automática de `AnimationSequence.uop` para resolução de apelidos (*aliases*) e mapeamento de grupos de ações.
- **Suporte Multi-Arquivo Clássico**: Lê `anim.mul` através de `anim6.mul` com conversão de corpos via `bodyconv.def` e `body.def`.
- **Filtro por Categorias e Busca Instantânea**: Pesquise criaturas por nome ou ID numérico/hexadecimal com atualização em tempo real.
- **Detecção Inteligente de Ações**: O menu de ações adapta-se ao tipo de corpo (Monstro, Marinho, Animal ou Humano) com indicador visual (`✓`) de quais ações possuem quadros reais disponíveis.
- **Reprodutor Interativo**: Play, Pause, Próximo Quadro, Anterior, slider de FPS (2 a 30 fps) e seletor das 8 direções com espelhamento automático.

### 9. 🌐 Cliloc (Localização e Textos)
- **Busca Ultrarrápida**: Pesquise instantaneamente por número do ID ou por qualquer termo contido no texto.
- **Editor Integrado**: Modifique frases, avisos do sistema ou nomes de magias.
- **Criação e Remoção**: Adicione novas linhas de texto ou remova entradas obsoletas.
- **Salvamento**: Gravação compatível em arquivos `cliloc.*` (ex: `cliloc.enu`).

### 10. 🔊 Sounds (Áudio e Efeitos Sonoros)
- **Player de Áudio Nativo**: Escute os efeitos sonoros diretamente sem travar a interface, utilizando os reprodutores nativos do Linux (`pw-play`, `paplay` ou `aplay`).
- **Suporte a Sound.def**: Resolução automática de redirecionamentos e traduções de som.
- **Exportação e Importação de WAV**: Extraia sons em formato WAVE padrão (22.050 Hz Mono 16-bit) ou importe novos arquivos de áudio.

### 11. 🗺️ Map (Visualizador de Mundos - Estilo Google Maps com LOD de Alta Performance)
- **Navegação Interativa e Fluida (Google Maps Style)**: O mapa ocupa toda a área da aba. Navegue livremente arrastando com o botão esquerdo do mouse (Pan & Drag suave) e dê zoom com a roda do mouse focado exatamente onde o cursor está apontando.
- **Arquitetura LOD (Level of Detail) sem Travamento**: Ao afastar o zoom (`zoom < 0.55`), o visualizador alterna automaticamente para a camada global de visão geral (*Overview Layer* com interpolação bilinear acelerada por hardware), garantindo **60 FPS sem engasgos**, sem sobrecarregar a CPU e eliminando qualquer lentidão em zoom panorâmico.
- **I/O Contíguo por Colunas 50x mais Rápido**: Leitura otimizada de blocos contíguos de terrenos e índices estáticos em fatias inteiras, reduzindo o tempo de decodificação de chunks para poucos milissegundos.
- **Cache Inteligente LRU (1.500 Chunks)**: Algoritmo *Least-Recently-Used* que descarta apenas os chunks mais antigos conforme a navegação ocorre, prevenindo estouro de memória e reinicializações de cache.
- **Zoom Contínuo e Duplo Clique**: Níveis de zoom de 0.08x (mundo inteiro em tela cheia) até 16.0x (detalhe máximo de cada tile). Duplo clique aproxima o ponto selecionado.
- **Todas as Facetas Suportadas**: Felucca, Trammel, Ilshenar, Malas, Tokuno e Ter Mur com dimensões nativas (7168x4096, 2304x1600, etc.).
- **Atalhos de Cidades e Marcos (Landmark Presets)**: Dropdown com 24 cidades e pontos de interesse (Britain, Moonglow, Trinsic, Yew, Minoc, Luna, Umbra, Zento, Royal City, Delucia, etc.) para salto instantâneo.
- **Pulo por Coordenadas (X, Y)**: Digite coordenadas específicas para ir diretamente a qualquer ponto do mundo.
- **Alternância de Estáticos**: Ligue ou desligue os itens estáticos instantaneamente pelo checkbox da barra superior.
- **HUD e Barra de Status em Tempo Real**: Indicador de escala métrica dinâmica, exibição das coordenadas em tempo real sob o cursor do mouse `Cursor: (X, Y)`, centro atual da câmera e nível percentual de zoom.

### 12. 🏰 Multis (Construções, Casas e Barcos)
- **Renderizador Isométrico 2.5D**: Constrói a visualização gráfica da edificação projetando cada componente com sua respectiva altura (Z) e profundidade.
- **Controle de Andares (Height Cutoff)**: Slider para cortar visualmente os tetos ou andares superiores e inspecionar o interior das casas.
- **Tabela de Componentes**: Lista detalhada de cada ItemID, deslocamento X, Y, Z e flags de construção.
- **Exportação de Scripts**: Exporte a planta da construção em formato de script texto compatível.

### 13. 💡 Light (Máscaras de Iluminação)
- Visualização das fontes de luz de `light.mul` e `lightidx.mul`.
- Renderização do gradiente de intensidade sobre fundo escuro.

### 14. 🔤 Fonts (Fontes ASCII)
- Suporte a todas as fontes ASCII do cliente (0 a 9).
- Visualização de toda a tabela de caracteres.
- Caixa de texto para teste e visualização de frases renderizadas ao vivo com a tipografia do jogo.

### 15. 🏹 Skills (Habilidades)
- Tabela completa de habilidades de `skills.mul` e `skills.idx`.
- Configuração do botão de ação direta (*Use Skill*).
- Exibição dos grupos de habilidades de `skillgrp.mul`.

### 16. 💬 Speech (Falas e Gatilhos)
- Tabela de palavras-chave e gatilhos de `speech.mul`.
- IDs em big-endian e codificação UTF-8.
- Filtro de busca e edição de palavras-chave de NPCs e sistemas.

### 17. ⏱️ AnimData (Temporização de Ladrilhos)
- Leitura e edição de `animdata.mul`.
- Configuração de quantidade de quadros, intervalo de troca, atraso de início e lista de deslocamento de quadros para itens animados do cenário.

### 18. 📊 GameData (Tabelas e CSVs do Cliente 3D)
- **Inspetor Completo de `GameData.uop`**: Leitura nativa e descompactação de todas as **79 tabelas de metadados** do Enhanced Client (3D).
- **Visualizador em Grade (Table View)**: Exibição estruturada com colunas, cabeçalhos e linhas formatadas, com ordenação e filtro em tempo real.
- **Visualizador de Texto Bruto (Raw View)**: Aba monospaçada para inspecionar e copiar os arquivos CSV/XML originais na íntegra.
- **Tabelas Chave Catalogadas**:
  - `legacycontainers.csv`: Coordenadas de drop e bounding boxes exatas de todos os contêineres e mochilas.
  - `legacy_to_new_items.csv`: Conversão de IDs de itens do cliente clássico 2D para os novos meshes/gráficos 3D.
  - `body_to_mesh.csv`: Mapeamento de corpos clássicos para modelos `.dds` 3D (ogre, ettin, zombie, gargoyle, etc.).
  - `recipes.csv`: Tabela completa de receitas de crafting, requerimentos de skill e materiais.
  - Planilhas de placas de casas (`house sign gumps`), posicionamento de construções, cores de pele de gárgula/elfo e estilos de cabelo.
- **Exportação Flexível**:
  - Exportação da tabela selecionada para **CSV** ou **JSON**.
  - Botão **"Export All 79 Tables..."** para extrair todas as planilhas de uma só vez para qualquer diretório do computador.

---

## 🛠️ Tecnologias e Algoritmos do Core

- **Bob Jenkins lookup3 (hashlittle2)**: Algoritmo exato de hash de 64 bits utilizado pelos pacotes `.uop` para busca de entradas em tempo constante.
- **Adler32 Checksum**: Verificação de integridade de dados dentro das tabelas de pacotes UOP.
- **Descompressão Zlib & Mythic**: Algoritmo `MoveToFront` combinado com decodificação de tabela de frequências para arquivos compactados modernos.
- **Conversão de Cores ARGB1555**: Tabelas pré-computadas de conversão entre 5 bits (0..31) e 8 bits (0..255) para máxima velocidade em Python puro.
- **Decodificadores e Codificadores RLE**: Processamento bidirecional de fluxos *Run-Length Encoded* para itens estáticos e gumps.

---

## 📦 Instalação e Requisitos

### Pré-requisitos
- **Python 3.10 ou superior**
- **PyQt6** (ou PyQt5)
- **Pillow** (PIL)

### Instalação das Dependências

No seu ambiente Linux, instale os pacotes via gerenciador de pacotes da sua distro ou via `pip`:

**Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pyqt6 python3-pil
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-pyqt6 python-pillow
```

**Fedora:**
```bash
sudo dnf install python3 python3-pyqt6 python3-pillow
```

**Ou via pip (Ambiente Virtual ou Usuário):**
```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar

### 1. Interface Gráfica Completa (GUI)

Dentro da pasta `UOFiddlerPy/`:

```bash
./run.sh
```

Ou diretamente pelo interpretador Python:
```bash
python3 main.py
```

Ao abrir, o programa tentará detectar automaticamente o diretório do seu Ultima Online. Se precisar alterar, basta acessar o menu superior:  
**File ➔ Options / Directory Paths...**

---

### 2. Ferramenta de Linha de Comando (CLI)

O UOFiddlerPy também acompanha uma CLI integrada (`cli.py`) para inspeções rápidas e exportações em lote via terminal ou scripts de automação:

```bash
# Exibir o resumo do cliente carregado
./cli.py --info

# Exportar a imagem de um item (ex: Gold Coins 0x0EED / 3821)
./cli.py --export-item 3821 --out /tmp/gold.png

# Exportar um terreno (Land Tile 0x0002)
./cli.py --export-land 2 --out /tmp/grass.png

# Exportar um Gump (ex: Gump 0)
./cli.py --export-gump 0 --out /tmp/gump0.png

# Exportar a planta isométrica de uma casa/multi (ex: Multi 0)
./cli.py --export-multi 0 --out /tmp/house.png
```

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte de testes unitários para validar tanto a integridade da decodificação dos arquivos binários quanto o carregamento gráfico das 17 abas em modo *headless* (offscreen):

```bash
# Executar testes do motor binário (Art, TileData, Hues, Gumps, Multis, Maps, Animations)
python3 -m unittest tests/test_core.py

# Executar testes de interface gráfica PyQt6 (em modo offscreen)
python3 -m unittest tests/test_gui.py
```

---

## 📂 Estrutura do Código-Fonte

```
UOFiddlerPy/
├── main.py                     # Ponto de entrada da aplicação gráfica
├── cli.py                      # Interface de linha de comando
├── run.sh                      # Script executável de inicialização
├── requirements.txt            # Dependências (PyQt6, Pillow)
├── README.md                   # Documentação em Inglês
├── README_pt-br.md             # Esta documentação em Português
├── Animationlist.xml           # Catálogo XML de nomes de criaturas e equipamentos
├── tests/
│   ├── test_core.py            # Testes unitários do motor de arquivos
│   └── test_gui.py             # Testes unitários da interface PyQt6
└── uofiddler/
    ├── core/                   # Motor binário do Ultima Online (sem dependência de GUI)
    │   ├── files.py            # Descoberta de caminhos e resolução case-insensitive
    │   ├── file_index.py       # Leitor de índices (.idx, .mul e Mythic .uop)
    │   ├── hash_utils.py       # Bob Jenkins lookup3 e Adler32
    │   ├── mythic.py           # Descompressor Mythic (Move-To-Front)
    │   ├── colors.py           # Conversões de cores 16-bit RGB 555 / 32-bit RGBA
    │   ├── art.py              # Decodificador e codificador de itens e terrenos
    │   ├── tiledata.py         # Leitor e gravador de tiledata.mul (Classic e High Seas)
    │   ├── hues.py             # 3.000 matizes e aplicação de paletas
    │   ├── gumps.py            # Leitor e codificador de gumps
    │   ├── textures.py         # Texturas de terreno (64x64 e 128x128)
    │   ├── radar_col.py        # Cores de minimapa e cálculo de média
    │   ├── sounds.py           # Sons, cabeçalhos WAV e playback Linux
    │   ├── cliloc.py           # Tabelas de strings localizadas
    │   ├── skills.py           # Habilidades e grupos
    │   ├── speech.py           # Palavras-chave e gatilhos de fala
    │   ├── animdata.py         # Temporização de quadros de animação
    │   ├── light.py            # Máscaras de luz
    │   ├── multis.py           # Componentes e renderizador isométrico de construções
    │   ├── animations.py       # Quadros e direções de animações (MUL e UOP)
    │   ├── maps.py             # Facetas, blocos 8x8, estáticos e I/O contíguo
    │   └── defs.py             # Parsers de bodyconv.def, body.def, mobtypes.txt e Animationlist.xml
    └── gui/                    # Interface gráfica moderna em PyQt6
        ├── app.py              # Janela principal e barra de abas com Lazy Loading
        ├── theme.py            # Folha de estilos Dark Theme (QSS)
        ├── widgets/
        │   ├── splash_screen.py# Tela de carregamento rápido (~1s)
        │   ├── lazy_tab.py     # Wrapper com barra de progresso para carregamento sob demanda
        │   ├── image_canvas.py # Canvas interativo com zoom e pan
        │   ├── color_bar.py    # Barra de 32 cores do Hue
        │   ├── virtual_tile_view.py # Navegação virtualizada em Grid / Lista (60 FPS)
        │   └── interactive_map_view.py # Mapa estilo Google Maps com LOD e LRU
        └── tabs/               # Todas as 17 abas implementadas
            ├── items_tab.py
            ├── land_tiles_tab.py
            ├── tiledata_tab.py
            ├── gumps_tab.py
            ├── hues_tab.py
            ├── textures_tab.py
            ├── radar_col_tab.py
            ├── animations_tab.py
            ├── cliloc_tab.py
            ├── sounds_tab.py
            ├── map_tab.py
            ├── multis_tab.py
            ├── light_tab.py
            ├── fonts_tab.py
            ├── skills_tab.py
            ├── speech_tab.py
            ├── animdata_tab.py
            └── settings_dialog.py
```

---

## 👤 Autor & Agradecimentos

- **Autor**: Mauricio Nunes + Gemini
- **Repositório GitHub**: [https://github.com/mbnunes/UOFiddlerPy](https://github.com/mbnunes/UOFiddlerPy)

---

## 📄 Licença

Distribuído sob os mesmos princípios de código aberto do ecossistema Ultima Online. Sinta-se livre para utilizar, modificar e aprimorar!
