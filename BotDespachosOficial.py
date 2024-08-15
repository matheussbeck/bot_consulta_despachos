import telebot
import pandas as pd
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import io
import sqlite3
import os
from datetime import datetime

# ID do BOT
chave_api = "CHAVE API TELEGRAM BOT"
bot = telebot.TeleBot(chave_api)

# Caminho onde o arquivo do banco de dados será salvo
db_path = "registro_consultas.db"

# Definir data e hora atual no escopo global
data_hora_atual = datetime.now()

# Dicionário para armazenar o contador de erros por chat_id
erros_por_usuario = {}

# Função para verificar e criar o banco de dados e a tabela
def verificar_e_criar_tabela_consultas():
    try:
        if not os.path.exists(db_path):
            conexao = sqlite3.connect(db_path)
            c = conexao.cursor()
            c.execute('''CREATE TABLE consultas
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          data TEXT,
                          hora TEXT,
                          unidade TEXT,
                          frente TEXT,
                          chat_id TEXT)''')
            conexao.commit()
            conexao.close()
            print(f"Banco de dados criado em {db_path}.")
        else:
            conexao = sqlite3.connect(db_path)
            c = conexao.cursor()
            c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='consultas' ''')
            if c.fetchone()[0] == 0:
                c.execute('''CREATE TABLE consultas
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              data TEXT,
                              hora TEXT,
                              unidade TEXT,
                              frente TEXT,
                              chat_id TEXT)''')
                conexao.commit()
                print("Tabela 'consultas' criada.")
            conexao.close()
    except sqlite3.Error as error:
        print("Erro ao conectar ao SQLite:", error)

# Função para carregar dados e realizar transformações
def carregar_dados_transformar():
    parquet_file = "base_despachos.parquet"
    df = pd.read_parquet(parquet_file)

    # Seleção de Colunas e transformações
    df2 = df[["UNIDADE", "FrentePrev", "LocalPrev", "Numero", "DataHora", "DataCheLavPrev"]]
    titulos = {
        'FrentePrev': 'FRENTE',
        'LocalPrev': 'FAZENDA',
        'Numero': 'CAMINHAO',
        'DataHora': 'DESPACHO',
        'DataCheLavPrev': 'PREVISAO'
    }
    df2 = df2.rename(columns=titulos)
    df2 = df2.astype(str).replace(r'\.0', '', regex=True)
    df2['DESPACHO'] = pd.to_datetime(df2['DESPACHO'])
    df2['PREVISAO'] = pd.to_datetime(df2['PREVISAO'])
    df2['tempotrajeto'] = df2['PREVISAO'] - df2['DESPACHO']
    df2['tempochegada'] = data_hora_atual - df2['DESPACHO']
    df2['TRAJETO'] = ((df2['tempochegada'] / df2['tempotrajeto']) * 100).astype(int)
    df2.loc[df2['TRAJETO'] > 100, 'TRAJETO'] = 100
    df2["CHAVE"] = df2["UNIDADE"] + "_" + df2["FRENTE"]
    df2['TRAJETO'] = df2['TRAJETO'].astype(str) + ' %'
    df2['DESPACHO'] = df2['DESPACHO'].dt.strftime('%d/%m/%Y %H:%M:%S')
    df2['PREVISAO'] = df2['PREVISAO'].dt.strftime('%d/%m/%Y %H:%M:%S')
    df2 = df2[['CHAVE', 'UNIDADE', 'FRENTE', 'FAZENDA', 'CAMINHAO', 'DESPACHO', 'TRAJETO', 'PREVISAO']]

    return df2

# Função para formatar data e hora no formato brasileiro (dd/mm/yyyy HH:MM)
def formatar_data_hora_br(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%d/%m/%Y %H:%M:%S')
    return dt.strftime('%d/%m/%Y %H:%M')

# Função para gerar teclado inline com unidades (três colunas)
def gerar_teclado_unidades():
    df2 = carregar_dados_transformar()  # Carregar os dados
    markup = types.InlineKeyboardMarkup(row_width=3)  # Definindo row_width como 3 para três colunas
    unidades_unicas = sorted(df2["UNIDADE"].unique())
    for i in range(0, len(unidades_unicas), 3):
        botao1 = types.InlineKeyboardButton(unidades_unicas[i], callback_data=f"unidade_{unidades_unicas[i]}")
        if i + 1 < len(unidades_unicas):
            botao2 = types.InlineKeyboardButton(unidades_unicas[i+1], callback_data=f"unidade_{unidades_unicas[i+1]}")
        else:
            botao2 = None
        if i + 2 < len(unidades_unicas):
            botao3 = types.InlineKeyboardButton(unidades_unicas[i+2], callback_data=f"unidade_{unidades_unicas[i+2]}")
        else:
            botao3 = None
        if botao2 and botao3:
            markup.add(botao1, botao2, botao3)
        elif botao2:
            markup.add(botao1, botao2)
        else:
            markup.add(botao1)
    return markup

# Função para gerar teclado inline com frentes para uma unidade específica (três colunas)
def gerar_teclado_frentes(unidade):
    df2 = carregar_dados_transformar()  # Carregar os dados

    # Carregar a planilha codFrente.xlsx
    df_codFrente = pd.read_parquet('CodFrente.parquet')
    df_codFrente = df_codFrente.astype(str)

    # Filtrar pela unidade selecionada
    df_unidade = df2[df2["UNIDADE"] == unidade]
    df_codFrente = df_codFrente[df_codFrente["UNIDADE"] == unidade]

    # Adicionar a coluna FRENTEN ao df_unidade
    df_unidade = df_unidade.merge(df_codFrente, left_on='FRENTE', right_on='FRENTE', how='left')
    df_unidade = df_unidade.rename(columns={'Abreviatura': 'FRENTEN'})

    markup = types.InlineKeyboardMarkup(row_width=3)  # Definindo row_width como 3 para três colunas
    frentes_unicas = sorted(df_unidade["FRENTEN"].unique())
    for i in range(0, len(frentes_unicas), 3):
        botao1 = types.InlineKeyboardButton(frentes_unicas[i], callback_data=f"frente_{unidade}_{frentes_unicas[i]}")
        if i + 1 < len(frentes_unicas):
            botao2 = types.InlineKeyboardButton(frentes_unicas[i+1], callback_data=f"frente_{unidade}_{frentes_unicas[i+1]}")
        else:
            botao2 = None
        if i + 2 < len(frentes_unicas):
            botao3 = types.InlineKeyboardButton(frentes_unicas[i+2], callback_data=f"frente_{unidade}_{frentes_unicas[i+2]}")
        else:
            botao3 = None
        if botao2 and botao3:
            markup.add(botao1, botao2, botao3)
        elif botao2:
            markup.add(botao1, botao2)
        else:
            markup.add(botao1)
    return markup

# Handler para responder com os últimos 10 despachos quando uma unidade é selecionada
@bot.callback_query_handler(func=lambda call: call.data.startswith("unidade_"))
def handle_unidade(call):
    _, unidade = call.data.split("_")
    markup_frentes = gerar_teclado_frentes(unidade)
    bot.send_message(call.message.chat.id, f"Selecione a frente para {unidade}", reply_markup=markup_frentes)

# Handler para responder com a imagem dos despachos quando uma frente é selecionada
@bot.callback_query_handler(func=lambda call: call.data.startswith("frente_"))
def handle_frente(call):
    _, unidade, frenten = call.data.split("_")
    df2 = carregar_dados_transformar()  # Carregar os dados

    # Carregar a planilha codFrente.xlsx
    df_codFrente = pd.read_parquet('CodFrente.parquet')

    # Filtrar pela unidade e frente selecionada
    df_unidade_frente = df2[(df2["UNIDADE"] == unidade)]

    # Adicionar a coluna FRENTEN ao df_unidade_frente
    df_unidade_frente = df_unidade_frente.merge(df_codFrente, left_on='FRENTE', right_on='FRENTE', how='left')
    df_unidade_frente = df_unidade_frente.rename(columns={'Abreviatura': 'FRENTEN'})

    df_despachos = df_unidade_frente[df_unidade_frente["FRENTEN"] == frenten].sort_values(by="DESPACHO", ascending=False).head(10)

    try:
        img_buffer = gerar_imagem_despachos(df_despachos, unidade, frenten)  # Gerar imagem
        bot.send_photo(call.message.chat.id, img_buffer)
        registrar_consulta(call.message.chat.id, unidade, frenten)  # Registrar consulta no banco de dados

    except Exception as e:
        print(f"Erro ao enviar imagem: {e}")
        enviar_mensagem_erro(call.message.chat.id)

# Função para registrar consulta no banco de dados
def registrar_consulta(chat_id, unidade, frente):
    data_atual = datetime.now().strftime('%Y-%m-%d')
    hora_atual = datetime.now().strftime('%H:%M:%S')

    try:
        conexao = sqlite3.connect(db_path)
        c = conexao.cursor()
        c.execute("INSERT INTO consultas (data, hora, unidade, frente, chat_id) VALUES (?, ?, ?, ?, ?)",
                  (data_atual, hora_atual, unidade, frente, chat_id))
        conexao.commit()
        conexao.close()
    except sqlite3.Error as error:
        print("Erro ao inserir consulta no SQLite:", error)

# Função para gerar imagem dos despachos
def gerar_imagem_despachos(df_despachos, unidade, frente):
    img_width = 1000  # Ajustado para acomodar a nova coluna
    line_height = 30
    padding = 10
    font_size = 16
    font = ImageFont.truetype("ARIALN.TTF", size=font_size)  # Alterado para usar Arial padrão
    text_color = (0, 0, 0)  # preto
    bg_color = (255, 255, 255)  # branco

    # Criar imagem
    num_rows = len(df_despachos)
    img_height = line_height * (num_rows + 3) + padding * 2
    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Escrever Unidade e Frente Selecionado acima do cabeçalho
    draw.text((padding, padding), f"Unidade: {unidade}", font=font, fill=text_color)
    draw.text((padding, padding + line_height), f"Frente Selecionado: {frente}", font=font, fill=text_color)

    # Escrever cabeçalho
    headers = ["Caminhão", "Despacho", "Trajeto", "Previsão", "Fazenda"]
    for i, header in enumerate(headers):
        draw.text((padding + i * (img_width // len(headers)), padding + 2 * line_height), header, font=font, fill=text_color)

    # Escrever dados
    for i, (_, row) in enumerate(df_despachos.iterrows()):
        row_text = [
            str(row["CAMINHAO"]),
            formatar_data_hora_br(row["DESPACHO"]),
            str(row["TRAJETO"]),
            formatar_data_hora_br(row["PREVISAO"]),
            str(row["FAZENDA"])
        ]
        for j, text in enumerate(row_text):
            draw.text((padding + j * (img_width // len(row_text)), padding + (i + 3) * line_height),
                      text, font=font, fill=text_color)

    # Salvar imagem em buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return img_buffer

# Função para enviar mensagem de erro ao usuário
def enviar_mensagem_erro(chat_id):
    global erros_por_usuario

    if chat_id in erros_por_usuario:
        erros_por_usuario[chat_id] += 1
    else:
        erros_por_usuario[chat_id] = 1

    # Responder com mensagem específica após 3 erros
    if erros_por_usuario[chat_id] == 3:
        bot.send_message(chat_id, "Ocorreu um Erro, tente Novamente !")
    elif erros_por_usuario[chat_id] == 4:
        bot.send_message(chat_id, "Por favor, entre em contato com a CIA !")
        erros_por_usuario[chat_id] = 0  # Reiniciar contador de erros

# Handler para iniciar a conversa com a seleção da unidade
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    markup_unidades = gerar_teclado_unidades()
    bot.send_message(chat_id, "Selecione a unidade:", reply_markup=markup_unidades)

# Iniciar o bot
if __name__ == "__main__":
    verificar_e_criar_tabela_consultas()

    try:
        bot.infinity_polling(timeout=5)  # Rodar o bot sem parar ao apresentar erros
    except Exception as e:
        print(f"Erro no polling do bot: {e}")
