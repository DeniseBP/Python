# Projeto_Imob

Projeto Web Scraping com PYTHON [Beautiful Soup e Selenium] + POWER BI

Desenvolvi uma ferramenta no Power BI que unifica os dados das imobiliárias da minha cidade, permitindo de maneira fácil e rápida ter acesso aos imóveis disponíveis para aluguel e venda na cidade e região.

Em resumo, realizei as seguintes etapas:
1. Desenvolvi os scripts em python para fazer o web scraping dos sites utilizando as bibliotecas Beautiful Soup e Selenium;
2. Criei uma tarefa no Agendador de Tarefas do Windows para automatizar a rotina de execução dos scripts;
3. Construí a identidade visual da ferramenta (nome, logo, BG...);
4. Levei para o Power BI os arquivos com os dados dos imóveis, criei uma página de busca de imóveis e outras 2 com análises diversas;
5. Publiquei, agendei a atualização automática e inseri o link do relatório em um site.

Link projeto publicado: [Reunimob](http://reunimob.com.br)

## Detalhamento etapa 2:

### Agendar execução do script com recorrência - Agendador de Tarefas

Este processo depende do computador estar ligado!
Primeiro abrimos o menu Iniciar e buscamos por “Agendador de Tarefas”. Com o programa aberto, clicamos em “Criar Tarefa” na barra da direita.

A seguir, irá abrir uma janela que possibilita alterar várias configurações do agendamento.

Na aba “Geral”, podemos dar um nome à tarefa e uma breve descrição.

Na aba “Disparadores” podemos configurar vários disparadores diferentes para uma mesma tarefa. Criando um novo disparador, há várias opções de execução disponíveis, incluindo na inicialização do sistema ou quando o sistema ficar ocioso. Porém, o mais importante é a opção padrão “Em um agendamento”, onde há uma gama de opções para explorar.

Na aba “Ações” iremos de fato inserir os detalhes para a execução do script. Criando uma nova ação, deixamos a opção padrão “Iniciar um programa”.

No campo Programa/script, precisamos colocar o caminho do executável do python. Para descobrir isso, podemos abrir um prompt de comando (Menu Iniciar -> Digitar cmd -> Abrir o prompt de comando) e digitar o comando “where python”, e vamos ter o caminho da instalação do Python no computador.

**IMPORTANTE: Coloque o caminho do executável do Python entre aspas duplas, caso contrário pode resultar em erro.**

No campo “Adicione argumentos (opcional)”, devemos digitar o nome do arquivo que contém o código. No meu caso, salvei como “projeto_imob_all.py”

No campo “Iniciar em (opcional)”, devemos inserir o caminho do diretório onde o script está salvo. Basta copiar o caminho que aparece no próprio explorador de arquivos do Windows.

Pronto! Temos a tarefa agendada.

Link com passo a passo etapa 2: [Passo a passo agendar tarefa](https://medium.com/sucessoemvendasacademy/como-executar-scripts-de-python-de-forma-autom%C3%A1tica-e-recorrente-windows-867db62523bf)

## Detalhamento etapa 4:

1- Criar credenciais de autenticação para o Google Drive
2- Desenvolver o script em python para obter os IDs de todos os arquivos
3- Instalar bibliotecas pandas e matplotlib
4- Obter dados no PBI Desktop com conector 'Script do Python' e depois criar algumas etapas no PQ para compor as urls dos arquivos
5- Tornar as fonte de dados públicas
6- Instalar gateway para agendar atualização no PBI online

Link com passo a passo etapa 4: [Passo a passo obtenção arquivos](https://www.canva.com/design/DAGFJcQfKNo/32Jbv1DKN0ztbOfFokBy2Q/view?utm_content=DAGFJcQfKNo&utm_campaign=designshare&utm_medium=link&utm_source=editor)
