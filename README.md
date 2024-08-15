# bot_consulta_despachos
BOT TELEGRAM COM COMANDOS BOTÃO PARA CONSULTA DE CAMINHÕES DESPACHADOS PARA AS FRENTES DE COLHEITA
[Clean Architeture + Python + SQL + Telegram + Automação + Data Science]

Inicia o Bot com qualquer mensagem enviada no Chat

Verifica Matricula e data de Nascimento do usuário, para validar se está credenciado ao acesso.
(Suprimido no diretório público)

Bot no Telegram com arquitetura de botões adaptando o layout em 3 colunas ao inves de comandos "/"

Carrega base dados de Unidades / Frentes / Caminhões da API convertida em parquet
Trata e formata toda a base de dados (data science + python)

Gera os botões adaptando o layout de acordo com a quantidade de opções para Unidades 
Gera os botões adaptando o layout de acordo com a quantidade de opções para Frentes,
Realizando tratamento e distinção de frentes divididas em pontos A e B

Carrega os ultimos 10 caminhões despachados para a frente e apresenta em formato tabular: Horário de Partida, % de trajeto, previsão de chegada e fazenda de destino no momento do despacho

Gera uma imagem com fundo branco em letras arial (pensado para visibilidade sob o sol no campo)
Apresenta ultima atualização da base de dados.

Consulta se existe banco de dados no local pre-definido, caso contrário ele cria um usando sqlite3
Registra os dados de consulta no Banco de Dados (ID user, Unidade, Frente, Data e Hora)

Contador de erros registrado em SQL por usuário para sugerir contato com a Central
No caso dos 3 primeiros erros "Ocorreu um Erro, tente Novamente !"
Após isso, sugere entrar em contato com atendimento Humano "Por Favor, entre em contato com a CIA !"
